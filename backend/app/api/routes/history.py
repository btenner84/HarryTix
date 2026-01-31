"""
Price History API - Stores and retrieves hourly price snapshots
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import httpx

router = APIRouter(prefix="/history", tags=["history"])

# In-memory storage for now (will persist across requests but not restarts)
# In production, this would be in a database
PRICE_HISTORY: list[dict] = []

# Your inventory (same as comparison.py)
INVENTORY = [
    {"set_name": "Set A", "section_filter": "SECTION 2", "row_filter": "1", "vivid_event_id": "6564568"},
    {"set_name": "Set B", "section_filter": "LEFT", "row_filter": None, "vivid_event_id": "6564614"},
    {"set_name": "Set C", "section_filter": "112", "row_filter": None, "vivid_event_id": "6564610"},
    {"set_name": "Set D", "section_filter": "LEFT", "row_filter": None, "vivid_event_id": "6564676"},
    {"set_name": "Set E", "section_filter": "SECTION 1", "row_filter": None, "vivid_event_id": "6564623"},
]


class PriceSnapshot(BaseModel):
    timestamp: datetime
    set_name: str
    min_price: Optional[float]
    avg_lowest_2: Optional[float]
    listings_count: int
    total_seats: int


class HistoryResponse(BaseModel):
    snapshots: list[PriceSnapshot]
    last_updated: Optional[datetime]


async def fetch_vivid_price(event_id: str, section_filter: str, row_filter: Optional[str]) -> dict:
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
async def take_snapshot():
    """Take a price snapshot for all sets (call this hourly or manually)"""
    now = datetime.utcnow()
    snapshots_taken = []

    for inv in INVENTORY:
        data = await fetch_vivid_price(inv["vivid_event_id"], inv["section_filter"], inv["row_filter"])

        snapshot = {
            "timestamp": now.isoformat() + "Z",  # Add Z to indicate UTC for proper local time conversion
            "set_name": inv["set_name"],
            "min_price": data["min_price"],
            "avg_lowest_2": data["avg_lowest_2"],
            "listings_count": data["listings_count"],
            "total_seats": data["total_seats"],
        }
        PRICE_HISTORY.append(snapshot)
        snapshots_taken.append(snapshot)

    return {"status": "ok", "snapshots": snapshots_taken}


@router.get("", response_model=HistoryResponse)
async def get_history(set_name: Optional[str] = None, limit: int = 100):
    """Get price history, optionally filtered by set name"""
    snapshots = PRICE_HISTORY.copy()

    if set_name:
        snapshots = [s for s in snapshots if s["set_name"] == set_name]

    # Sort by timestamp descending and limit
    snapshots = sorted(snapshots, key=lambda x: x["timestamp"], reverse=True)[:limit]

    last_updated = None
    if snapshots:
        last_updated = datetime.fromisoformat(snapshots[0]["timestamp"])

    return HistoryResponse(
        snapshots=[PriceSnapshot(**s) for s in snapshots],
        last_updated=last_updated
    )


@router.get("/latest")
async def get_latest():
    """Get the most recent snapshot for each set"""
    latest = {}
    for snapshot in reversed(PRICE_HISTORY):
        set_name = snapshot["set_name"]
        if set_name not in latest:
            latest[set_name] = snapshot

    return {"snapshots": list(latest.values())}
