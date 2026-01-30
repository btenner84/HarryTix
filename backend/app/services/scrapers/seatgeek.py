"""
SeatGeek Scraper

RELIABILITY: LOW - Uses DataDome anti-bot protection
ANTI-BOT: HIGH - DataDome is one of the most sophisticated anti-bot systems

URL Patterns:
- Performer: /[performer-name]-tickets
- Event: /[performer]-tickets/[venue-city-date]/[eventID]

NOTE: SeatGeek has aggressive bot protection. This scraper provides:
1. Public API access (event stats only, no individual listings)
2. Page scraping with fallbacks (may get blocked)

For reliable SeatGeek data, consider using a headless browser with residential proxies.
"""
import httpx
from typing import List, Optional
from datetime import datetime
import logging
import json
import re

from app.services.scrapers.base import BaseScraper, ListingData

logger = logging.getLogger(__name__)


class SeatGeekScraper(BaseScraper):
    """
    SeatGeek scraper with multiple fallback methods.

    WARNING: SeatGeek uses DataDome anti-bot which blocks most scraping attempts.
    This scraper tries multiple approaches but may have limited success.
    """

    platform_name = "seatgeek"
    base_url = "https://seatgeek.com"

    # Public API (limited - no individual listings)
    api_url = "https://api.seatgeek.com/2"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    async def fetch_listings(self, event_id: str) -> List[ListingData]:
        """
        Fetch listings for a SeatGeek event.

        Args:
            event_id: The event ID (e.g., "6234567" from the URL)

        Note: SeatGeek's public API only provides price statistics (min/avg/max),
        not individual listings. Individual listings require bypassing DataDome.
        """
        try:
            await self._rate_limit()

            # Try public API first (most reliable but limited data)
            listings = await self._fetch_via_api(event_id)

            # Try page scraping if API didn't work
            if not listings:
                listings = await self._fetch_via_page(event_id)

            logger.info(f"SeatGeek: Found {len(listings)} price points for event {event_id}")
            return listings

        except Exception as e:
            logger.error(f"SeatGeek: fetch_listings failed: {e}")
            return []

    async def _fetch_via_api(self, event_id: str) -> List[ListingData]:
        """
        Fetch event price stats via SeatGeek's public API.

        The public API provides:
        - lowest_price
        - average_price
        - highest_price
        - listing_count

        But NOT individual listing details (section, row, etc.)
        """
        listings = []

        try:
            # SeatGeek public API endpoint
            url = f"{self.api_url}/events/{event_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"Accept": "application/json"},
                    # Note: Would need client_id for full access
                    # params={"client_id": "YOUR_CLIENT_ID"}
                )

                if response.status_code == 200:
                    data = response.json()
                    event = data if "stats" in data else data.get("event", {})
                    stats = event.get("stats", {})

                    if stats:
                        listings = self._create_listings_from_stats(stats, event_id)
                        logger.debug(f"SeatGeek: API returned stats: {stats}")
                elif response.status_code == 403:
                    logger.debug("SeatGeek: API requires authentication")
                else:
                    logger.debug(f"SeatGeek: API returned {response.status_code}")

        except Exception as e:
            logger.debug(f"SeatGeek: API fetch failed: {e}")

        return listings

    def _create_listings_from_stats(self, stats: dict, event_id: str) -> List[ListingData]:
        """Create listing objects from API price statistics"""
        listings = []

        lowest = stats.get("lowest_price") or stats.get("lowest_sg_base_price")
        average = stats.get("average_price") or stats.get("median_price")
        highest = stats.get("highest_price")
        listing_count = stats.get("listing_count", 0)

        if lowest:
            listings.append(ListingData(
                platform="seatgeek",
                section="Various (Low)",
                row=None,
                quantity=1,
                price_per_ticket=float(lowest),
                total_price=float(lowest),
                listing_url=f"{self.base_url}/e/{event_id}",
                raw_data={
                    "type": "lowest_price",
                    "listing_count": listing_count,
                    "source": "api_stats"
                },
            ))

        if average and average != lowest:
            listings.append(ListingData(
                platform="seatgeek",
                section="Various (Avg)",
                row=None,
                quantity=1,
                price_per_ticket=float(average),
                total_price=float(average),
                listing_url=f"{self.base_url}/e/{event_id}",
                raw_data={
                    "type": "average_price",
                    "listing_count": listing_count,
                    "source": "api_stats"
                },
            ))

        if highest and highest != average:
            listings.append(ListingData(
                platform="seatgeek",
                section="Various (High)",
                row=None,
                quantity=1,
                price_per_ticket=float(highest),
                total_price=float(highest),
                listing_url=f"{self.base_url}/e/{event_id}",
                raw_data={
                    "type": "highest_price",
                    "listing_count": listing_count,
                    "source": "api_stats"
                },
            ))

        return listings

    async def _fetch_via_page(self, event_id: str) -> List[ListingData]:
        """
        Try to fetch listings by scraping the event page.

        WARNING: SeatGeek uses DataDome which will likely block this request.
        This is a fallback that may occasionally work.
        """
        listings = []

        try:
            url = f"{self.base_url}/e/{event_id}"
            logger.info(f"SeatGeek: Attempting page fetch {url}")

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)

                # Check for DataDome block
                if response.status_code == 403 or "datadome" in response.text.lower():
                    logger.warning("SeatGeek: Blocked by DataDome anti-bot protection")
                    return []

                if response.status_code != 200:
                    logger.warning(f"SeatGeek: HTTP {response.status_code}")
                    return []

                # Try to parse any embedded data
                listings = self._parse_page_data(response.text, event_id)

        except httpx.TimeoutException:
            logger.error("SeatGeek: Request timed out")
        except Exception as e:
            logger.error(f"SeatGeek: Page fetch failed: {e}")

        return listings

    def _parse_page_data(self, html: str, event_id: str) -> List[ListingData]:
        """Parse any embedded data from the SeatGeek page"""
        listings = []

        try:
            # Try __NEXT_DATA__
            next_pattern = r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            match = re.search(next_pattern, html, re.DOTALL)

            if match:
                data = json.loads(match.group(1))
                page_props = data.get("props", {}).get("pageProps", {})

                # Look for event stats
                event = page_props.get("event", {})
                stats = event.get("stats", {})

                if stats:
                    listings = self._create_listings_from_stats(stats, event_id)

                # Try to find actual listings (rare)
                listing_data = page_props.get("listings", [])
                for item in listing_data[:50]:
                    try:
                        price = item.get("price") or item.get("p") or 0
                        if price and float(price) > 0:
                            listings.append(ListingData(
                                platform="seatgeek",
                                section=item.get("section", "General"),
                                row=item.get("row"),
                                quantity=item.get("quantity", 1),
                                price_per_ticket=float(price),
                                total_price=float(price) * item.get("quantity", 1),
                                listing_url=f"{self.base_url}/e/{event_id}",
                                raw_data=item,
                            ))
                    except Exception:
                        continue

            # Fallback: regex for prices
            if not listings:
                listings = self._fallback_extraction(html, event_id)

        except json.JSONDecodeError:
            logger.debug("SeatGeek: Failed to parse JSON from page")
        except Exception as e:
            logger.debug(f"SeatGeek: Page parse error: {e}")

        return listings

    def _fallback_extraction(self, html: str, event_id: str) -> List[ListingData]:
        """Extract prices via regex as last resort"""
        listings = []

        try:
            # Look for price-like patterns
            patterns = [
                r'"lowest_price"\s*:\s*(\d+(?:\.\d{2})?)',
                r'"average_price"\s*:\s*(\d+(?:\.\d{2})?)',
                r'"highest_price"\s*:\s*(\d+(?:\.\d{2})?)',
                r'data-price="(\d+(?:\.\d{2})?)"',
            ]

            prices = {}
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, html)
                if matches:
                    price_type = ["low", "avg", "high", "data"][i]
                    prices[price_type] = float(matches[0])

            if prices.get("low"):
                listings.append(ListingData(
                    platform="seatgeek",
                    section="Various (Low)",
                    row=None,
                    quantity=1,
                    price_per_ticket=prices["low"],
                    total_price=prices["low"],
                    listing_url=f"{self.base_url}/e/{event_id}",
                    raw_data={"type": "fallback", "source": "regex"},
                ))

            if prices.get("avg") and prices.get("avg") != prices.get("low"):
                listings.append(ListingData(
                    platform="seatgeek",
                    section="Various (Avg)",
                    row=None,
                    quantity=1,
                    price_per_ticket=prices["avg"],
                    total_price=prices["avg"],
                    listing_url=f"{self.base_url}/e/{event_id}",
                    raw_data={"type": "fallback", "source": "regex"},
                ))

        except Exception as e:
            logger.debug(f"SeatGeek: Fallback extraction failed: {e}")

        return listings

    async def search_event(self, artist: str, venue: str, date: datetime) -> Optional[str]:
        """Search for an event and return its ID"""
        try:
            await self._rate_limit()

            # Use public API for search (more reliable than scraping)
            search_query = artist.replace(" ", "+")
            url = f"{self.api_url}/events"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={
                        "q": artist,
                        "datetime_utc.gte": date.strftime("%Y-%m-%dT00:00:00"),
                        "datetime_utc.lte": date.strftime("%Y-%m-%dT23:59:59"),
                        "per_page": 10,
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", [])

                    # Find matching event
                    for event in events:
                        event_venue = event.get("venue", {}).get("name", "").lower()
                        if venue.lower() in event_venue or "madison square" in event_venue:
                            return str(event.get("id"))

                    # Return first result if no exact match
                    if events:
                        return str(events[0].get("id"))

            return None

        except Exception as e:
            logger.error(f"SeatGeek: search_event failed: {e}")
            return None
