from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class ListingData(BaseModel):
    """Standardized listing data from any platform"""
    platform: str
    section: str | None = None
    row: str | None = None
    quantity: int = 1
    price_per_ticket: float
    total_price: float | None = None
    listing_url: str | None = None
    raw_data: dict = {}


class BaseScraper(ABC):
    """Abstract base class for ticket platform scrapers"""

    platform_name: str = "base"
    rate_limit_calls: int = 10  # calls per minute
    rate_limit_period: int = 60  # seconds

    def __init__(self):
        self._last_call_time: float = 0
        self._call_count: int = 0

    async def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_call_time

        # Reset counter if period has passed
        if time_since_last >= self.rate_limit_period:
            self._call_count = 0

        # Wait if we've hit the limit
        if self._call_count >= self.rate_limit_calls:
            wait_time = self.rate_limit_period - time_since_last
            if wait_time > 0:
                logger.info(f"{self.platform_name}: Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self._call_count = 0

        self._call_count += 1
        self._last_call_time = asyncio.get_event_loop().time()

    @abstractmethod
    async def fetch_listings(self, event_id: str) -> List[ListingData]:
        """Fetch all current listings for an event"""
        pass

    @abstractmethod
    async def search_event(self, artist: str, venue: str, date: datetime) -> Optional[str]:
        """Search for an event and return its platform-specific ID"""
        pass

    async def get_comparable_listings(
        self,
        event_id: str,
        section: str | None = None,
        row: str | None = None
    ) -> List[ListingData]:
        """Fetch listings comparable to a specific section/row"""
        all_listings = await self.fetch_listings(event_id)

        if not section:
            return all_listings

        # Filter by section (case-insensitive partial match)
        section_lower = section.lower()
        filtered = [
            l for l in all_listings
            if l.section and section_lower in l.section.lower()
        ]

        # Further filter by row if specified
        if row and row.upper() not in ("GA", "PIT", "FLOOR"):
            filtered = [l for l in filtered if l.row == row]

        return filtered
