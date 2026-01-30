from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Grouping (NULL section = overall event stats)
    section: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Time granularity
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-23 for hourly granularity

    # Aggregated stats
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    avg_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    median_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    listing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Per-platform breakdown
    platform_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"stubhub": {"avg": 150, "count": 10}, "seatgeek": {"avg": 145, "count": 8}}

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="price_history")

    __table_args__ = (
        UniqueConstraint("event_id", "section", "recorded_date", "recorded_hour", name="uq_price_history_lookup"),
        Index("idx_price_history_lookup", "event_id", "section", "recorded_date"),
    )
