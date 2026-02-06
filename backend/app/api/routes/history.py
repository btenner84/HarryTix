"""
Price History API - Stores and retrieves hourly price snapshots
Now with database persistence!
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import httpx

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.snapshot import PriceSnapshot as PriceSnapshotModel

router = APIRouter(prefix="/history", tags=["history"])

# Your inventory (same as comparison.py)
VIVID_FEE = 0.10

INVENTORY = [
    {"set_name": "Set A", "section_filter": "SECTION 2", "row_filter": "1", "vivid_event_id": "6564557", "quantity": 4, "cost_per_ticket": 471.25},
    {"set_name": "Set B", "section_filter": "LEFT", "row_filter": None, "vivid_event_id": "6564614", "quantity": 6, "cost_per_ticket": 490.67},
    {"set_name": "Set C", "section_filter": "112", "row_filter": None, "vivid_event_id": "6564610", "quantity": 8, "cost_per_ticket": 324.88},
    {"set_name": "Set D", "section_filter": "LEFT", "row_filter": None, "vivid_event_id": "6564676", "quantity": 5, "cost_per_ticket": 433.20},
    {"set_name": "Set E", "section_filter": "SECTION 1", "row_filter": None, "vivid_event_id": "6564623", "quantity": 4, "cost_per_ticket": 368.00, "max_row": 10, "solo_only": True},
    {"set_name": "Set F", "section_filter": "SECTION 1", "row_filter": None, "vivid_event_id": "6564691", "quantity": 1, "cost_per_ticket": 368.00, "max_row": 15, "solo_only": True},
    {"set_name": "Set G", "section_filter": "GA", "row_filter": None, "vivid_event_id": "6564691", "quantity": 5, "cost_per_ticket": 433.20},
    {"set_name": "Set H", "section_filter": "114", "row_filter": None, "vivid_event_id": "6564691", "quantity": 2, "cost_per_ticket": 368.00},
]


class PriceSnapshotResponse(BaseModel):
    timestamp: datetime
    set_name: str
    min_price: Optional[float]
    avg_lowest_2: Optional[float]
    listings_count: int
    total_seats: int
    you_receive: Optional[float]
    profit_per_ticket: Optional[float]
    total_profit: Optional[float]
    quantity: int
    cost_per_ticket: float

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    snapshots: list[PriceSnapshotResponse]
    last_updated: Optional[datetime]


async def fetch_vivid_price(
    event_id: str,
    section_filter: str,
    row_filter: Optional[str],
    max_row: Optional[int] = None,
    solo_only: bool = False
) -> dict:
    """Fetch current price from Vivid Seats API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://www.vividseats.com/hermes/api/v1/listings?productionId={event_id}"
            )
            data = resp.json()
            tickets = data.get("tickets", [])

            prices = []
            total_seats = 0

            for t in tickets:
                section = str(t.get("s", "")).upper()
                row = str(t.get("r", "")).upper()
                price = float(t.get("aip", 0))
                qty = int(t.get("q", 1))

                if price < 100:
                    continue
                if section_filter.upper() not in section:
                    continue
                if row_filter and row != row_filter.upper():
                    continue

                # Filter by max row number
                if max_row:
                    try:
                        row_num = int(row)
                        if row_num >= max_row:
                            continue
                    except ValueError:
                        continue

                # Filter for solo tickets only
                if solo_only and qty != 1:
                    continue

                prices.append(price)
                total_seats += qty

            if prices:
                sorted_prices = sorted(prices)
                avg_lowest_2 = (sorted_prices[0] + sorted_prices[1]) / 2 if len(sorted_prices) >= 2 else sorted_prices[0]
                return {
                    "min_price": min(prices),
                    "avg_lowest_2": round(avg_lowest_2, 2),
                    "listings_count": len(prices),
                    "total_seats": total_seats,
                }
    except Exception as e:
        print(f"Vivid API error: {e}")

    return {"min_price": None, "avg_lowest_2": None, "listings_count": 0, "total_seats": 0}


@router.post("/snapshot")
async def take_snapshot(db: AsyncSession = Depends(get_db)):
    """Take a price snapshot for all sets and save to database"""
    now = datetime.utcnow()
    snapshots_taken = []

    for inv in INVENTORY:
        data = await fetch_vivid_price(
            inv["vivid_event_id"],
            inv["section_filter"],
            inv["row_filter"],
            inv.get("max_row"),
            inv.get("solo_only", False)
        )

        # Calculate profit
        you_receive = None
        profit_per_ticket = None
        total_profit = None

        if data["avg_lowest_2"]:
            you_receive = round(data["avg_lowest_2"] * (1 - VIVID_FEE), 2)
            profit_per_ticket = round(you_receive - inv["cost_per_ticket"], 2)
            total_profit = round(profit_per_ticket * inv["quantity"], 2)

        # Create database record
        snapshot = PriceSnapshotModel(
            timestamp=now,
            set_name=inv["set_name"],
            min_price=Decimal(str(data["min_price"])) if data["min_price"] else None,
            avg_lowest_2=Decimal(str(data["avg_lowest_2"])) if data["avg_lowest_2"] else None,
            listings_count=data["listings_count"],
            total_seats=data["total_seats"],
            you_receive=Decimal(str(you_receive)) if you_receive else None,
            profit_per_ticket=Decimal(str(profit_per_ticket)) if profit_per_ticket else None,
            total_profit=Decimal(str(total_profit)) if total_profit else None,
            quantity=inv["quantity"],
            cost_per_ticket=Decimal(str(inv["cost_per_ticket"])),
        )
        db.add(snapshot)

        snapshots_taken.append({
            "timestamp": now.isoformat() + "Z",
            "set_name": inv["set_name"],
            "min_price": data["min_price"],
            "avg_lowest_2": data["avg_lowest_2"],
            "listings_count": data["listings_count"],
            "total_seats": data["total_seats"],
            "you_receive": you_receive,
            "profit_per_ticket": profit_per_ticket,
            "total_profit": total_profit,
            "quantity": inv["quantity"],
            "cost_per_ticket": inv["cost_per_ticket"],
        })

    await db.commit()
    return {"status": "ok", "snapshots": snapshots_taken, "saved_to_db": True}


@router.get("", response_model=HistoryResponse)
async def get_history(
    set_name: Optional[str] = None,
    limit: int = 500,
    db: AsyncSession = Depends(get_db)
):
    """Get price history from database, optionally filtered by set name"""
    query = select(PriceSnapshotModel).order_by(desc(PriceSnapshotModel.timestamp))

    if set_name:
        query = query.where(PriceSnapshotModel.set_name == set_name)

    query = query.limit(limit)

    result = await db.execute(query)
    snapshots = result.scalars().all()

    last_updated = snapshots[0].timestamp if snapshots else None

    # Convert to response format with consistent timestamps
    response_snapshots = []
    for s in snapshots:
        snap_dict = {
            "timestamp": s.timestamp,
            "set_name": s.set_name,
            "min_price": float(s.min_price) if s.min_price else None,
            "avg_lowest_2": float(s.avg_lowest_2) if s.avg_lowest_2 else None,
            "listings_count": s.listings_count,
            "total_seats": s.total_seats,
            "you_receive": float(s.you_receive) if s.you_receive else None,
            "profit_per_ticket": float(s.profit_per_ticket) if s.profit_per_ticket else None,
            "total_profit": float(s.total_profit) if s.total_profit else None,
            "quantity": s.quantity,
            "cost_per_ticket": float(s.cost_per_ticket),
        }
        response_snapshots.append(PriceSnapshotResponse(**snap_dict))

    return HistoryResponse(
        snapshots=response_snapshots,
        last_updated=last_updated
    )


@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    """Get the most recent snapshot for each set"""
    latest = {}

    for inv in INVENTORY:
        query = (
            select(PriceSnapshotModel)
            .where(PriceSnapshotModel.set_name == inv["set_name"])
            .order_by(desc(PriceSnapshotModel.timestamp))
            .limit(1)
        )
        result = await db.execute(query)
        snapshot = result.scalar_one_or_none()

        if snapshot:
            latest[inv["set_name"]] = {
                "timestamp": snapshot.timestamp.isoformat().replace('+00:00', 'Z'),
                "set_name": snapshot.set_name,
                "min_price": float(snapshot.min_price) if snapshot.min_price else None,
                "avg_lowest_2": float(snapshot.avg_lowest_2) if snapshot.avg_lowest_2 else None,
                "listings_count": snapshot.listings_count,
                "total_seats": snapshot.total_seats,
                "you_receive": float(snapshot.you_receive) if snapshot.you_receive else None,
                "profit_per_ticket": float(snapshot.profit_per_ticket) if snapshot.profit_per_ticket else None,
                "total_profit": float(snapshot.total_profit) if snapshot.total_profit else None,
                "quantity": snapshot.quantity,
                "cost_per_ticket": float(snapshot.cost_per_ticket),
            }

    return {"snapshots": list(latest.values())}


@router.get("/profit-over-time")
async def get_profit_over_time(db: AsyncSession = Depends(get_db)):
    """Get total profit across all sets at each timestamp"""
    query = select(PriceSnapshotModel).order_by(PriceSnapshotModel.timestamp)
    result = await db.execute(query)
    snapshots = result.scalars().all()

    # Group by timestamp
    by_timestamp: dict = {}

    for snapshot in snapshots:
        ts = snapshot.timestamp.isoformat().replace('+00:00', 'Z')
        if ts not in by_timestamp:
            by_timestamp[ts] = {
                "timestamp": ts,
                "total_profit": 0,
                "sets": {},
            }

        profit = float(snapshot.total_profit) if snapshot.total_profit else 0
        by_timestamp[ts]["total_profit"] += profit
        by_timestamp[ts]["sets"][snapshot.set_name] = {
            "profit": float(snapshot.total_profit) if snapshot.total_profit else None,
            "price": float(snapshot.avg_lowest_2) if snapshot.avg_lowest_2 else None,
        }

    # Sort by timestamp
    result_list = sorted(by_timestamp.values(), key=lambda x: x["timestamp"])

    return {"data": result_list}
