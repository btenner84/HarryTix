from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, computed_field


class InventoryBase(BaseModel):
    event_id: int
    section: str
    row: str | None = None
    seat_numbers: str | None = None
    quantity: int = 1
    cost_per_ticket: Decimal
    total_cost: Decimal
    purchase_date: date | None = None
    target_sell_min: Decimal | None = None
    target_sell_max: Decimal | None = None
    notes: str | None = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    section: str | None = None
    row: str | None = None
    seat_numbers: str | None = None
    quantity: int | None = None
    cost_per_ticket: Decimal | None = None
    total_cost: Decimal | None = None
    purchase_date: date | None = None
    target_sell_min: Decimal | None = None
    target_sell_max: Decimal | None = None
    notes: str | None = None


class InventoryResponse(InventoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Computed fields for UI display
    current_market_price: Decimal | None = None
    expected_revenue: Decimal | None = None
    expected_profit: Decimal | None = None

    class Config:
        from_attributes = True


class InventoryWithMarketData(InventoryResponse):
    """Inventory item with current market pricing data attached"""
    comparable_listings_count: int = 0
    min_market_price: Decimal | None = None
    max_market_price: Decimal | None = None
    avg_market_price: Decimal | None = None
