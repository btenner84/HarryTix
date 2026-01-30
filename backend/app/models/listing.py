from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Numeric, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Platform info
    platform: Mapped[str] = mapped_column(String(20), nullable=False)  # 'stubhub', 'seatgeek', 'vividseats'

    # Listing details
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)
    row: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Pricing
    price_per_ticket: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Reference
    listing_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Raw API response for debugging
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="listing_snapshots")

    __table_args__ = (
        Index("idx_listings_event_fetched", "event_id", "fetched_at"),
        Index("idx_listings_section", "section"),
        Index("idx_listings_platform", "platform"),
    )
