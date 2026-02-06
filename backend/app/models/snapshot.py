from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceSnapshot(Base):
    """Stores periodic price snapshots for each ticket set."""
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)

    # When the snapshot was taken
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Which set this is for
    set_name: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Price data from VividSeats
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    avg_lowest_2: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    listings_count: Mapped[int] = mapped_column(Integer, default=0)
    total_seats: Mapped[int] = mapped_column(Integer, default=0)

    # Calculated values
    you_receive: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    profit_per_ticket: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_profit: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Set info at time of snapshot
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_per_ticket: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
