from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # Ticket details
    section: Mapped[str] = mapped_column(String(50), nullable=False)
    row: Mapped[str | None] = mapped_column(String(10), nullable=True)
    seat_numbers: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "7-10" or "101,102,103"
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Cost tracking
    cost_per_ticket: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Target pricing (user's expected sell range)
    target_sell_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    target_sell_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="inventory_items")
