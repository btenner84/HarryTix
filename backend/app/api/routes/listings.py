from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
import httpx

from app.api.deps import get_db
from app.models.listing import ListingSnapshot
from app.models.inventory import Inventory
from app.models.event import Event
from app.schemas.listing import ListingSnapshotResponse, CurrentListingsResponse, ComparableListingsResponse

router = APIRouter()


# Vivid Seats API for live prices
VIVIDSEATS_API = "https://www.vividseats.com/hermes/api/v1"


@router.get("/current", response_model=CurrentListingsResponse)
async def get_current_listings(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent listings for an event from all platforms"""
    # Get listings from the last 2 hours
    cutoff = datetime.utcnow() - timedelta(hours=2)

    result = await db.execute(
        select(ListingSnapshot)
        .where(
            ListingSnapshot.event_id == event_id,
            ListingSnapshot.fetched_at >= cutoff
        )
        .order_by(ListingSnapshot.price_per_ticket)
    )
    listings = result.scalars().all()

    # Group by platform
    by_platform: dict[str, list] = {"stubhub": [], "seatgeek": [], "vividseats": []}
    for listing in listings:
        if listing.platform in by_platform:
            by_platform[listing.platform].append(listing)

    # Find the most recent fetch time
    last_updated = max((l.fetched_at for l in listings), default=datetime.utcnow())

    return CurrentListingsResponse(
        event_id=event_id,
        last_updated=last_updated,
        listings=listings,
        by_platform=by_platform,
    )


@router.get("/comparable/{inventory_id}", response_model=ComparableListingsResponse)
async def get_comparable_listings(
    inventory_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get listings comparable to a specific inventory item"""
    # Get the inventory item
    inv_result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    inventory = inv_result.scalar_one_or_none()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get recent listings in similar section
    cutoff = datetime.utcnow() - timedelta(hours=2)

    # Match section prefix (e.g., "200" matches "200s", "Sec 200", etc.)
    section_prefix = inventory.section.split()[0] if inventory.section else ""

    query = select(ListingSnapshot).where(
        ListingSnapshot.event_id == inventory.event_id,
        ListingSnapshot.fetched_at >= cutoff,
    )

    # Add section filter if we have a section
    if section_prefix:
        query = query.where(ListingSnapshot.section.ilike(f"%{section_prefix}%"))

    # Add row filter if specified and not GA
    if inventory.row and inventory.row.upper() not in ("GA", "PIT", "FLOOR"):
        query = query.where(ListingSnapshot.row == inventory.row)

    result = await db.execute(query.order_by(ListingSnapshot.price_per_ticket))
    listings = result.scalars().all()

    # Calculate stats
    if listings:
        prices = [float(l.price_per_ticket) for l in listings]
        avg_price = Decimal(str(round(sum(prices) / len(prices), 2)))
        min_price = Decimal(str(min(prices)))
        max_price = Decimal(str(max(prices)))
    else:
        avg_price = min_price = max_price = None

    return ComparableListingsResponse(
        inventory_id=inventory_id,
        section=inventory.section,
        row=inventory.row,
        listings=listings,
        avg_price=avg_price,
        min_price=min_price,
        max_price=max_price,
        listing_count=len(listings),
    )


@router.get("/all", response_model=list[ListingSnapshotResponse])
async def get_all_recent_listings(
    hours: int = Query(default=24, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get all listings from the last N hours (default 24, max 168)"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(ListingSnapshot)
        .where(ListingSnapshot.fetched_at >= cutoff)
        .order_by(ListingSnapshot.fetched_at.desc())
        .limit(1000)
    )
    return result.scalars().all()


@router.get("/live/{event_id}")
async def get_live_listings(
    event_id: int,
    section_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get LIVE listings directly from Vivid Seats API.
    This bypasses the database and fetches real-time prices.
    """
    # Get event to find Vivid Seats ID
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not event.vividseats_event_id:
        raise HTTPException(status_code=400, detail="No Vivid Seats event ID configured")

    vs_id = event.vividseats_event_id

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get listings
            listings_resp = await client.get(
                f"{VIVIDSEATS_API}/listings",
                params={"productionId": vs_id},
                headers={"Accept": "application/json"}
            )

            if listings_resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch from Vivid Seats")

            data = listings_resp.json()
            tickets = data.get("tickets", [])
            sections_data = data.get("sections", [])

            # Filter if section_filter provided
            if section_filter:
                filter_upper = section_filter.upper()
                tickets = [t for t in tickets if filter_upper in str(t.get("s", "")).upper()]

            # Process tickets
            listings = []
            for t in tickets[:200]:  # Limit to 200
                listings.append({
                    "section": t.get("s"),
                    "row": t.get("r"),
                    "quantity": t.get("q"),
                    "base_price": float(t.get("p", 0)),
                    "all_in_price": float(t.get("aip", 0)),
                })

            # Calculate stats
            if listings:
                all_in_prices = [l["all_in_price"] for l in listings]
                stats = {
                    "min_price": min(all_in_prices),
                    "max_price": max(all_in_prices),
                    "avg_price": sum(all_in_prices) / len(all_in_prices),
                    "listing_count": len(listings),
                }
            else:
                stats = {
                    "min_price": None,
                    "max_price": None,
                    "avg_price": None,
                    "listing_count": 0,
                }

            # Process sections for GA/special areas
            ga_sections = []
            for s in sections_data:
                name = s.get("n", "").upper()
                if any(x in name for x in ["GA", "FLOOR", "PIT", "KISS", "DISCO"]):
                    if int(s.get("q", 0)) > 0:
                        ga_sections.append({
                            "name": s.get("n"),
                            "low_price": float(s.get("l", 0)),
                            "high_price": float(s.get("h", 0)),
                            "quantity": int(s.get("q", 0)),
                        })

            return {
                "event_id": event_id,
                "vividseats_id": vs_id,
                "event_name": event.name,
                "event_date": event.event_date.isoformat(),
                "venue": event.venue,
                "fetched_at": datetime.utcnow().isoformat(),
                "stats": stats,
                "ga_sections": ga_sections,
                "listings": listings,
            }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Vivid Seats API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-inventory")
async def get_live_inventory_prices(db: AsyncSession = Depends(get_db)):
    """
    Get live prices for ALL inventory items at once.
    Returns market data for each ticket set.
    """
    # Get all inventory with events
    result = await db.execute(
        select(Inventory, Event)
        .join(Event, Inventory.event_id == Event.id)
        .order_by(Event.event_date)
    )
    inventory_events = result.all()

    if not inventory_events:
        return {"items": [], "summary": {}}

    items = []
    total_cost = 0
    total_min_value = 0
    total_max_value = 0
    total_tickets = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for inv, event in inventory_events:
            if not event.vividseats_event_id:
                continue

            vs_id = event.vividseats_event_id

            try:
                # Fetch live data
                resp = await client.get(
                    f"{VIVIDSEATS_API}/listings",
                    params={"productionId": vs_id},
                    headers={"Accept": "application/json"}
                )

                if resp.status_code != 200:
                    continue

                data = resp.json()
                tickets = data.get("tickets", [])
                sections = data.get("sections", [])

                # Determine filter based on section type
                section_upper = (inv.section or "").upper()

                # Determine minimum quantity for comparison
                # Solo tickets (Set E) can compare to qty 1, others need qty 2+
                is_solo_tickets = "solo" in (inv.notes or "").lower() or "single" in (inv.notes or "").lower()
                min_qty = 1 if is_solo_tickets else 2

                if "GA" in section_upper or "PIT" in section_upper or "LEFT" in section_upper:
                    # Filter for Left GA specifically if that's what they have
                    if "LEFT" in section_upper:
                        comparable = [t for t in tickets if "LEFT" in str(t.get("s", "")).upper() and "GA" in str(t.get("s", "")).upper() and int(t.get("q", 1)) >= min_qty]
                    else:
                        comparable = [t for t in tickets if any(x in str(t.get("s", "")).upper() for x in ["GA", "PIT", "FLOOR"]) and "KISS" not in str(t.get("s", "")).upper() and "DISCO" not in str(t.get("s", "")).upper() and int(t.get("q", 1)) >= min_qty]
                elif "200S" in section_upper or "100S" in section_upper:
                    # Match entire section level (200s or 100s)
                    level = "2" if "200" in section_upper else "1"
                    comparable = [t for t in tickets if str(t.get("s", "")).startswith(f"Section {level}") and int(t.get("q", 1)) >= min_qty]
                    # Further filter by row if Row 1
                    if inv.row == "1":
                        comparable = [t for t in comparable if t.get("r") == "1"]
                elif inv.section and inv.section.startswith("Section"):
                    # Extract specific section number (e.g., Section 112 -> 112)
                    sec_num = inv.section.replace("Section ", "").replace("s", "")
                    comparable = [t for t in tickets if sec_num in str(t.get("s", "")) and int(t.get("q", 1)) >= min_qty]
                else:
                    comparable = [t for t in tickets if int(t.get("q", 1)) >= min_qty][:50]

                # Calculate market prices
                if comparable:
                    all_in_prices = [float(t.get("aip", 0)) for t in comparable]
                    min_price = min(all_in_prices)
                    max_price = max(all_in_prices)
                    avg_price = sum(all_in_prices) / len(all_in_prices)
                    listing_count = len(comparable)

                    # Individual listings for display
                    listing_details = []
                    for t in sorted(comparable, key=lambda x: float(x.get("aip", 0)))[:10]:
                        listing_details.append({
                            "section": t.get("s"),
                            "row": t.get("r"),
                            "quantity": t.get("q"),
                            "all_in_price": float(t.get("aip", 0)),
                        })
                else:
                    min_price = max_price = avg_price = None
                    listing_count = 0
                    listing_details = []

                # Calculate profit
                cost = float(inv.cost_per_ticket)
                qty = inv.quantity

                if min_price:
                    min_profit = (min_price - cost) * qty
                    max_profit = (max_price - cost) * qty
                    avg_profit = (avg_price - cost) * qty
                else:
                    min_profit = max_profit = avg_profit = None

                item_data = {
                    "inventory_id": inv.id,
                    "set_name": inv.notes or f"Set {inv.id}",
                    "event_id": event.id,
                    "event_date": event.event_date.isoformat(),
                    "venue": event.venue,
                    "section": inv.section,
                    "row": inv.row,
                    "quantity": qty,
                    "cost_per_ticket": cost,
                    "total_cost": cost * qty,
                    "market": {
                        "min_price": min_price,
                        "max_price": max_price,
                        "avg_price": avg_price,
                        "listing_count": listing_count,
                    },
                    "profit": {
                        "min": min_profit,
                        "max": max_profit,
                        "avg": avg_profit,
                    },
                    "comparable_listings": listing_details,
                }

                items.append(item_data)

                total_cost += cost * qty
                total_tickets += qty
                if min_price:
                    total_min_value += min_price * qty
                    total_max_value += max_price * qty

            except Exception as e:
                print(f"Error fetching live data for event {event.id}: {e}")
                continue

    return {
        "fetched_at": datetime.utcnow().isoformat(),
        "items": items,
        "summary": {
            "total_tickets": total_tickets,
            "total_cost": total_cost,
            "total_min_value": total_min_value,
            "total_max_value": total_max_value,
            "total_min_profit": total_min_value - total_cost if total_min_value else None,
            "total_max_profit": total_max_value - total_cost if total_max_value else None,
        }
    }


@router.get("/multi-platform/{event_id}")
async def get_multi_platform_prices(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get prices from BOTH Vivid Seats and StubHub for an event.
    Returns comparison data for making selling decisions.
    """
    from app.services.scrapers.stubhub_browser import StubHubBrowserScraper

    # Get event
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    response = {
        "event_id": event_id,
        "event_name": event.name,
        "event_date": event.event_date.isoformat(),
        "venue": event.venue,
        "platforms": {},
    }

    # Get Vivid Seats prices
    if event.vividseats_event_id:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{VIVIDSEATS_API}/listings",
                    params={"productionId": event.vividseats_event_id},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tickets = data.get("tickets", [])
                    prices = [float(t.get("aip", 0)) for t in tickets if float(t.get("aip", 0)) > 50]

                    response["platforms"]["vividseats"] = {
                        "listing_count": len(prices),
                        "min_price": min(prices) if prices else None,
                        "max_price": max(prices) if prices else None,
                        "avg_price": sum(prices) / len(prices) if prices else None,
                        "price_type": "all-in",
                        "seller_fee": 0.10,
                    }
        except Exception as e:
            response["platforms"]["vividseats"] = {"error": str(e)}

    # Get StubHub prices
    if event.stubhub_event_id:
        scraper = StubHubBrowserScraper()
        try:
            sh_result = await scraper.get_event_listings(f"event/{event.stubhub_event_id}")
            sh_prices = [l["price"] for l in sh_result.get("listings", []) if l.get("price")]

            if sh_prices:
                # StubHub prices are BASE prices, estimate all-in by adding 25%
                all_in_prices = [p * 1.25 for p in sh_prices]

                response["platforms"]["stubhub"] = {
                    "listing_count": len(sh_prices),
                    "min_price_base": min(sh_prices),
                    "max_price_base": max(sh_prices),
                    "min_price_allin": min(all_in_prices),
                    "max_price_allin": max(all_in_prices),
                    "avg_price_allin": sum(all_in_prices) / len(all_in_prices),
                    "price_type": "base (all-in estimated +25%)",
                    "seller_fee": 0.15,
                }
            else:
                response["platforms"]["stubhub"] = {"listing_count": 0, "error": "No prices found"}
        except Exception as e:
            response["platforms"]["stubhub"] = {"error": str(e)}
        finally:
            await scraper.close()

    # Calculate which platform is better for selling
    vs = response["platforms"].get("vividseats", {})
    sh = response["platforms"].get("stubhub", {})

    if vs.get("min_price") and sh.get("min_price_allin"):
        vs_net = vs["min_price"] * (1 - vs["seller_fee"])
        sh_net = sh["min_price_allin"] * (1 - sh["seller_fee"])

        response["recommendation"] = {
            "vividseats_net_per_ticket": vs_net,
            "stubhub_net_per_ticket": sh_net,
            "better_platform": "stubhub" if sh_net > vs_net else "vividseats",
            "difference": abs(sh_net - vs_net),
        }

    response["fetched_at"] = datetime.utcnow().isoformat()
    return response
