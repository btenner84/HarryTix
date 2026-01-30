from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class RevenueAnalytics(BaseModel):
    """Overall revenue analytics for user's inventory"""
    total_tickets: int
    total_cost_basis: Decimal
    expected_revenue_min: Decimal | None
    expected_revenue_max: Decimal | None
    expected_revenue_avg: Decimal | None
    projected_profit_min: Decimal | None
    projected_profit_max: Decimal | None
    projected_profit_avg: Decimal | None
    last_updated: datetime


class InventoryRevenueItem(BaseModel):
    """Revenue analytics for a single inventory item"""
    inventory_id: int
    section: str
    quantity: int
    cost_basis: Decimal
    current_market_avg: Decimal | None
    expected_revenue: Decimal | None
    expected_profit: Decimal | None
    profit_margin_pct: float | None


class PriceHistoryPoint(BaseModel):
    """Single point in price history"""
    recorded_date: date
    recorded_hour: int | None
    min_price: Decimal | None
    max_price: Decimal | None
    avg_price: Decimal | None
    median_price: Decimal | None
    listing_count: int | None
    platform_breakdown: dict | None


class PriceHistoryResponse(BaseModel):
    """Price history for charting"""
    event_id: int
    section: str | None
    history: list[PriceHistoryPoint]


class PlatformComparison(BaseModel):
    """Price comparison across platforms"""
    platform: str
    avg_price: Decimal | None
    min_price: Decimal | None
    max_price: Decimal | None
    listing_count: int
