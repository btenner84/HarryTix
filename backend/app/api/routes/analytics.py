from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, date

from app.api.deps import get_db
from app.models.inventory import Inventory
from app.models.listing import ListingSnapshot
from app.models.price_history import PriceHistory
from app.schemas.analytics import (
    RevenueAnalytics,
    InventoryRevenueItem,
    PriceHistoryResponse,
    PriceHistoryPoint,
    PlatformComparison,
)

router = APIRouter()


@router.get("/revenue", response_model=RevenueAnalytics)
async def get_revenue_analytics(db: AsyncSession = Depends(get_db)):
    """Get overall revenue analytics for all inventory"""
    # Get all inventory
    inv_result = await db.execute(select(Inventory))
    inventory_items = inv_result.scalars().all()

    if not inventory_items:
        return RevenueAnalytics(
            total_tickets=0,
            total_cost_basis=Decimal("0"),
            expected_revenue_min=None,
            expected_revenue_max=None,
            expected_revenue_avg=None,
            projected_profit_min=None,
            projected_profit_max=None,
            projected_profit_avg=None,
            last_updated=datetime.utcnow(),
        )

    total_tickets = sum(item.quantity for item in inventory_items)
    total_cost_basis = sum(item.total_cost for item in inventory_items)

    # Get recent listings for market pricing
    cutoff = datetime.utcnow() - timedelta(hours=2)

    expected_revenues = []
    for item in inventory_items:
        section_prefix = item.section.split()[0] if item.section else ""
        listings_query = select(ListingSnapshot).where(
            ListingSnapshot.event_id == item.event_id,
            ListingSnapshot.fetched_at >= cutoff,
        )
        if section_prefix:
            listings_query = listings_query.where(
                ListingSnapshot.section.ilike(f"%{section_prefix}%")
            )

        listings_result = await db.execute(listings_query)
        listings = listings_result.scalars().all()

        if listings:
            prices = [float(l.price_per_ticket) for l in listings]
            avg_price = sum(prices) / len(prices)
            expected_revenues.append(avg_price * item.quantity)
        elif item.target_sell_min and item.target_sell_max:
            # Fallback to user's target range
            avg_target = (float(item.target_sell_min) + float(item.target_sell_max)) / 2
            expected_revenues.append(avg_target * item.quantity)

    if expected_revenues:
        total_expected = sum(expected_revenues)
        expected_revenue_avg = Decimal(str(round(total_expected, 2)))
        # Estimate min/max as +/- 20% of average
        expected_revenue_min = Decimal(str(round(total_expected * 0.8, 2)))
        expected_revenue_max = Decimal(str(round(total_expected * 1.2, 2)))

        projected_profit_avg = expected_revenue_avg - total_cost_basis
        projected_profit_min = expected_revenue_min - total_cost_basis
        projected_profit_max = expected_revenue_max - total_cost_basis
    else:
        expected_revenue_min = expected_revenue_max = expected_revenue_avg = None
        projected_profit_min = projected_profit_max = projected_profit_avg = None

    return RevenueAnalytics(
        total_tickets=total_tickets,
        total_cost_basis=total_cost_basis,
        expected_revenue_min=expected_revenue_min,
        expected_revenue_max=expected_revenue_max,
        expected_revenue_avg=expected_revenue_avg,
        projected_profit_min=projected_profit_min,
        projected_profit_max=projected_profit_max,
        projected_profit_avg=projected_profit_avg,
        last_updated=datetime.utcnow(),
    )


@router.get("/revenue/by-item", response_model=list[InventoryRevenueItem])
async def get_revenue_by_item(db: AsyncSession = Depends(get_db)):
    """Get revenue analytics broken down by inventory item"""
    inv_result = await db.execute(select(Inventory))
    inventory_items = inv_result.scalars().all()

    cutoff = datetime.utcnow() - timedelta(hours=2)
    items = []

    for item in inventory_items:
        section_prefix = item.section.split()[0] if item.section else ""
        listings_query = select(ListingSnapshot).where(
            ListingSnapshot.event_id == item.event_id,
            ListingSnapshot.fetched_at >= cutoff,
        )
        if section_prefix:
            listings_query = listings_query.where(
                ListingSnapshot.section.ilike(f"%{section_prefix}%")
            )

        listings_result = await db.execute(listings_query)
        listings = listings_result.scalars().all()

        if listings:
            prices = [float(l.price_per_ticket) for l in listings]
            current_market_avg = Decimal(str(round(sum(prices) / len(prices), 2)))
            expected_revenue = current_market_avg * item.quantity
            expected_profit = expected_revenue - item.total_cost
            profit_margin_pct = float(expected_profit / item.total_cost * 100) if item.total_cost else None
        else:
            current_market_avg = None
            expected_revenue = None
            expected_profit = None
            profit_margin_pct = None

        items.append(InventoryRevenueItem(
            inventory_id=item.id,
            section=item.section,
            quantity=item.quantity,
            cost_basis=item.total_cost,
            current_market_avg=current_market_avg,
            expected_revenue=expected_revenue,
            expected_profit=expected_profit,
            profit_margin_pct=profit_margin_pct,
        ))

    return items


@router.get("/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    event_id: int,
    section: str | None = None,
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get price history for charting"""
    cutoff_date = date.today() - timedelta(days=days)

    query = select(PriceHistory).where(
        PriceHistory.event_id == event_id,
        PriceHistory.recorded_date >= cutoff_date,
    )

    if section:
        query = query.where(PriceHistory.section == section)
    else:
        query = query.where(PriceHistory.section.is_(None))

    query = query.order_by(PriceHistory.recorded_date, PriceHistory.recorded_hour)

    result = await db.execute(query)
    history_records = result.scalars().all()

    history = [
        PriceHistoryPoint(
            recorded_date=h.recorded_date,
            recorded_hour=h.recorded_hour,
            min_price=h.min_price,
            max_price=h.max_price,
            avg_price=h.avg_price,
            median_price=h.median_price,
            listing_count=h.listing_count,
            platform_breakdown=h.platform_breakdown,
        )
        for h in history_records
    ]

    return PriceHistoryResponse(
        event_id=event_id,
        section=section,
        history=history,
    )


@router.get("/platform-comparison", response_model=list[PlatformComparison])
async def get_platform_comparison(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Compare prices across platforms for an event"""
    cutoff = datetime.utcnow() - timedelta(hours=2)

    platforms = ["stubhub", "seatgeek", "vividseats"]
    comparisons = []

    for platform in platforms:
        result = await db.execute(
            select(
                func.avg(ListingSnapshot.price_per_ticket).label("avg"),
                func.min(ListingSnapshot.price_per_ticket).label("min"),
                func.max(ListingSnapshot.price_per_ticket).label("max"),
                func.count(ListingSnapshot.id).label("count"),
            ).where(
                ListingSnapshot.event_id == event_id,
                ListingSnapshot.platform == platform,
                ListingSnapshot.fetched_at >= cutoff,
            )
        )
        row = result.one()

        comparisons.append(PlatformComparison(
            platform=platform,
            avg_price=Decimal(str(round(row.avg, 2))) if row.avg else None,
            min_price=Decimal(str(row.min)) if row.min else None,
            max_price=Decimal(str(row.max)) if row.max else None,
            listing_count=row.count or 0,
        ))

    return comparisons
