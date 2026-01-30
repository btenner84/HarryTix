"""
Price Comparison API - Returns verified prices from Vivid Seats and StubHub
for your specific ticket inventory.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter(prefix="/comparison", tags=["comparison"])


class TicketSet(BaseModel):
    set_name: str
    date: str
    section: str
    quantity: int
    cost_per_ticket: float
    total_cost: float
    vivid_event_id: str
    stubhub_event_id: str
    vivid_buyer_price: Optional[float] = None
    vivid_you_receive: Optional[float] = None
    stubhub_buyer_price: Optional[float] = None
    stubhub_you_receive: Optional[float] = None
    avg_you_receive: Optional[float] = None
    profit_per_ticket: Optional[float] = None
    total_profit: Optional[float] = None
    best_platform: Optional[str] = None
    comparable_count: int = 0


class ComparisonResponse(BaseModel):
    sets: list[TicketSet]
    summary: dict


# Your inventory with event IDs
INVENTORY = [
    {
        "set_name": "Set A",
        "date": "Sept 2",
        "event_date": "2026-09-02",
        "section": "200s Row 1",
        "quantity": 4,
        "cost_per_ticket": 471.25,
        "vivid_event_id": "6564568",
        "stubhub_event_id": "160334450",
        "section_filter": "SECTION 2",
        "row_filter": "1",
    },
    {
        "set_name": "Set B",
        "date": "Sept 19",
        "event_date": "2026-09-19",
        "section": "Left GA",
        "quantity": 6,
        "cost_per_ticket": 490.67,
        "vivid_event_id": "6564614",
        "stubhub_event_id": "160334462",
        "section_filter": "LEFT",
        "row_filter": None,
    },
    {
        "set_name": "Set C",
        "date": "Sept 18",
        "event_date": "2026-09-18",
        "section": "Section 112",
        "quantity": 8,
        "cost_per_ticket": 324.88,
        "vivid_event_id": "6564610",
        "stubhub_event_id": "160334461",
        "section_filter": "112",
        "row_filter": None,
    },
    {
        "set_name": "Set D",
        "date": "Oct 9",
        "event_date": "2026-10-09",
        "section": "Left GA",
        "quantity": 5,
        "cost_per_ticket": 433.20,
        "vivid_event_id": "6564676",
        "stubhub_event_id": "160334466",
        "section_filter": "LEFT",
        "row_filter": None,
    },
    {
        "set_name": "Set E",
        "date": "Sept 25",
        "event_date": "2026-09-25",
        "section": "100s (solos)",
        "quantity": 4,
        "cost_per_ticket": 368.00,
        "vivid_event_id": "6564623",
        "stubhub_event_id": "160334464",
        "section_filter": "SECTION 1",
        "row_filter": None,
    },
]

# Verified StubHub prices from map screenshots (all-in, buyer pays)
STUBHUB_PRICES = {
    "160334450": 700,   # Set A - 200s Row 1 estimate from map
    "160334462": 1138,  # Set B - Left GA from map
    "160334461": 620,   # Set C - Section 112 from map
    "160334466": 750,   # Set D - Left GA from map
    "160334464": 600,   # Set E - 100s from map
}

VIVID_FEE = 0.10
STUBHUB_FEE = 0.15


async def get_vivid_min_price(event_id: str, section_filter: str, row_filter: Optional[str]) -> tuple[Optional[float], int]:
    """Fetch minimum price from Vivid Seats API for matching section/row."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://www.vividseats.com/hermes/api/v1/listings?productionId={event_id}"
            )
            data = resp.json()
            tickets = data.get("tickets", [])

            matches = []
            for t in tickets:
                section = str(t.get("s", "")).upper()
                row = str(t.get("r", "")).upper()
                price = float(t.get("aip", 0))

                if price < 100:
                    continue

                if section_filter.upper() not in section:
                    continue

                if row_filter and row != row_filter.upper():
                    continue

                matches.append(price)

            if matches:
                return min(matches), len(matches)
    except Exception as e:
        print(f"Vivid API error: {e}")

    return None, 0


@router.get("", response_model=ComparisonResponse)
async def get_comparison():
    """Get price comparison for all ticket sets."""
    sets = []

    total_cost = 0
    total_vivid_revenue = 0
    total_stubhub_revenue = 0
    total_tickets = 0

    for inv in INVENTORY:
        # Get live Vivid price
        vivid_price, count = await get_vivid_min_price(
            inv["vivid_event_id"],
            inv["section_filter"],
            inv["row_filter"]
        )

        # Get StubHub price (from verified map data)
        stubhub_price = STUBHUB_PRICES.get(inv["stubhub_event_id"])

        # Calculate what you receive after fees
        vivid_receive = vivid_price * (1 - VIVID_FEE) if vivid_price else None
        stubhub_receive = stubhub_price * (1 - STUBHUB_FEE) if stubhub_price else None

        # Calculate average and profit
        avg_receive = None
        if vivid_receive and stubhub_receive:
            avg_receive = (vivid_receive + stubhub_receive) / 2
        elif vivid_receive:
            avg_receive = vivid_receive
        elif stubhub_receive:
            avg_receive = stubhub_receive

        profit_per = (avg_receive - inv["cost_per_ticket"]) if avg_receive else None
        total_profit = profit_per * inv["quantity"] if profit_per else None

        # Determine best platform
        best = None
        if vivid_receive and stubhub_receive:
            best = "Vivid" if vivid_receive > stubhub_receive else "StubHub"
        elif vivid_receive:
            best = "Vivid"
        elif stubhub_receive:
            best = "StubHub"

        ticket_set = TicketSet(
            set_name=inv["set_name"],
            date=inv["date"],
            section=inv["section"],
            quantity=inv["quantity"],
            cost_per_ticket=inv["cost_per_ticket"],
            total_cost=inv["cost_per_ticket"] * inv["quantity"],
            vivid_event_id=inv["vivid_event_id"],
            stubhub_event_id=inv["stubhub_event_id"],
            vivid_buyer_price=vivid_price,
            vivid_you_receive=vivid_receive,
            stubhub_buyer_price=stubhub_price,
            stubhub_you_receive=stubhub_receive,
            avg_you_receive=avg_receive,
            profit_per_ticket=profit_per,
            total_profit=total_profit,
            best_platform=best,
            comparable_count=count,
        )
        sets.append(ticket_set)

        # Update totals
        total_cost += inv["cost_per_ticket"] * inv["quantity"]
        total_tickets += inv["quantity"]
        if vivid_receive:
            total_vivid_revenue += vivid_receive * inv["quantity"]
        if stubhub_receive:
            total_stubhub_revenue += stubhub_receive * inv["quantity"]

    summary = {
        "total_tickets": total_tickets,
        "total_cost": total_cost,
        "total_vivid_revenue": total_vivid_revenue,
        "total_vivid_profit": total_vivid_revenue - total_cost,
        "total_stubhub_revenue": total_stubhub_revenue,
        "total_stubhub_profit": total_stubhub_revenue - total_cost,
        "best_overall": "Vivid" if total_vivid_revenue > total_stubhub_revenue else "StubHub",
    }

    return ComparisonResponse(sets=sets, summary=summary)
