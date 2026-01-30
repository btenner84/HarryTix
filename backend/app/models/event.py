from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Platform-specific event IDs for API lookups
    stubhub_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seatgeek_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vividseats_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    inventory_items: Mapped[list["Inventory"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    listing_snapshots: Mapped[list["ListingSnapshot"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="event", cascade="all, delete-orphan")
