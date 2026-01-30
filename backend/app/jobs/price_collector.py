import asyncio
import logging
from datetime import datetime, date
from decimal import Decimal
from statistics import median
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.event import Event
from app.models.listing import ListingSnapshot
from app.models.price_history import PriceHistory
from app.services.scrapers import StubHubScraper, SeatGeekScraper, VividSeatsScraper, ListingData

logger = logging.getLogger(__name__)


async def collect_all_prices():
    """Main job to collect prices from all platforms for all events"""

    logger.info("Starting hourly price collection")

    scrapers = [
        StubHubScraper(),
        SeatGeekScraper(),
        VividSeatsScraper(),
    ]

    async with async_session_maker() as session:
        # Get all active events (future events only)
        result = await session.execute(
            select(Event).where(Event.event_date > datetime.utcnow())
        )
        events = result.scalars().all()

        if not events:
            logger.info("No upcoming events to collect prices for")
            return

        for event in events:
            try:
                await collect_event_prices(session, event, scrapers)
            except Exception as e:
                logger.error(f"Failed to collect prices for event {event.id}: {e}")

        await session.commit()

    logger.info("Completed hourly price collection")


async def collect_event_prices(
    session: AsyncSession,
    event: Event,
    scrapers: List
):
    """Collect prices for a single event from all platforms"""

    logger.info(f"Collecting prices for event: {event.name} ({event.event_date})")

    all_listings: List[ListingData] = []

    # Fetch from all platforms sequentially (to respect rate limits)
    for scraper in scrapers:
        event_id = getattr(event, f"{scraper.platform_name}_event_id", None)
        if not event_id:
            logger.debug(f"No {scraper.platform_name} event ID for {event.name}")
            continue

        try:
            listings = await scraper.fetch_listings(event_id)
            all_listings.extend(listings)
            logger.info(f"  {scraper.platform_name}: {len(listings)} listings")
        except Exception as e:
            logger.error(f"  {scraper.platform_name} failed: {e}")

    if not all_listings:
        logger.warning(f"No listings fetched for event {event.id}")
        return

    # Store raw listings
    now = datetime.utcnow()
    for listing in all_listings:
        snapshot = ListingSnapshot(
            event_id=event.id,
            platform=listing.platform,
            section=listing.section,
            row=listing.row,
            quantity=listing.quantity,
            price_per_ticket=Decimal(str(listing.price_per_ticket)),
            total_price=Decimal(str(listing.total_price)) if listing.total_price else None,
            listing_url=listing.listing_url,
            fetched_at=now,
            raw_data=listing.raw_data,
        )
        session.add(snapshot)

    # Calculate and store aggregated stats
    await calculate_price_stats(session, event.id, all_listings)

    logger.info(f"Stored {len(all_listings)} listings for event {event.id}")


async def calculate_price_stats(
    session: AsyncSession,
    event_id: int,
    listings: List[ListingData]
):
    """Calculate and store aggregated price statistics"""

    if not listings:
        return

    now = datetime.utcnow()
    today = now.date()
    hour = now.hour

    # Overall stats (section = None)
    prices = [l.price_per_ticket for l in listings]
    platform_breakdown = {}

    for platform in ["stubhub", "seatgeek", "vividseats"]:
        platform_prices = [l.price_per_ticket for l in listings if l.platform == platform]
        if platform_prices:
            platform_breakdown[platform] = {
                "avg": round(sum(platform_prices) / len(platform_prices), 2),
                "min": min(platform_prices),
                "max": max(platform_prices),
                "count": len(platform_prices),
            }

    # Upsert overall stats
    overall_history = PriceHistory(
        event_id=event_id,
        section=None,
        recorded_date=today,
        recorded_hour=hour,
        min_price=Decimal(str(min(prices))),
        max_price=Decimal(str(max(prices))),
        avg_price=Decimal(str(round(sum(prices) / len(prices), 2))),
        median_price=Decimal(str(round(median(prices), 2))),
        listing_count=len(listings),
        platform_breakdown=platform_breakdown,
    )

    # Check for existing record and update or insert
    existing = await session.execute(
        select(PriceHistory).where(
            PriceHistory.event_id == event_id,
            PriceHistory.section.is_(None),
            PriceHistory.recorded_date == today,
            PriceHistory.recorded_hour == hour,
        )
    )
    existing_record = existing.scalar_one_or_none()

    if existing_record:
        existing_record.min_price = overall_history.min_price
        existing_record.max_price = overall_history.max_price
        existing_record.avg_price = overall_history.avg_price
        existing_record.median_price = overall_history.median_price
        existing_record.listing_count = overall_history.listing_count
        existing_record.platform_breakdown = overall_history.platform_breakdown
    else:
        session.add(overall_history)

    # Also calculate per-section stats
    sections = set(l.section for l in listings if l.section)
    for section in sections:
        section_listings = [l for l in listings if l.section == section]
        section_prices = [l.price_per_ticket for l in section_listings]

        if not section_prices:
            continue

        section_history = PriceHistory(
            event_id=event_id,
            section=section,
            recorded_date=today,
            recorded_hour=hour,
            min_price=Decimal(str(min(section_prices))),
            max_price=Decimal(str(max(section_prices))),
            avg_price=Decimal(str(round(sum(section_prices) / len(section_prices), 2))),
            median_price=Decimal(str(round(median(section_prices), 2))),
            listing_count=len(section_listings),
            platform_breakdown=None,
        )

        existing_section = await session.execute(
            select(PriceHistory).where(
                PriceHistory.event_id == event_id,
                PriceHistory.section == section,
                PriceHistory.recorded_date == today,
                PriceHistory.recorded_hour == hour,
            )
        )
        existing_section_record = existing_section.scalar_one_or_none()

        if existing_section_record:
            existing_section_record.min_price = section_history.min_price
            existing_section_record.max_price = section_history.max_price
            existing_section_record.avg_price = section_history.avg_price
            existing_section_record.median_price = section_history.median_price
            existing_section_record.listing_count = section_history.listing_count
        else:
            session.add(section_history)
