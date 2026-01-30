from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ListingBase(BaseModel):
    platform: str
    section: str | None = None
    row: str | None = None
    quantity: int | None = None
    price_per_ticket: Decimal
    total_price: Decimal | None = None
    listing_url: str | None = None


class ListingResponse(ListingBase):
    """Listing data returned from scrapers"""
    pass


class ListingSnapshotResponse(ListingBase):
    """Listing snapshot stored in database"""
    id: int
    event_id: int
    fetched_at: datetime

    class Config:
        from_attributes = True


class CurrentListingsResponse(BaseModel):
    """Response containing current listings from all platforms"""
    event_id: int
    last_updated: datetime
    listings: list[ListingSnapshotResponse]
    by_platform: dict[str, list[ListingSnapshotResponse]]


class ComparableListingsResponse(BaseModel):
    """Listings comparable to a specific inventory item"""
    inventory_id: int
    section: str
    row: str | None
    listings: list[ListingSnapshotResponse]
    avg_price: Decimal | None
    min_price: Decimal | None
    max_price: Decimal | None
    listing_count: int
