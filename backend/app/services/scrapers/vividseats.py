"""
Vivid Seats Scraper

RELIABILITY: HIGH - Uses direct Hermes API
ANTI-BOT: LOW - API is publicly accessible

API Endpoints:
- Production details: /hermes/api/v1/productions/{productionId}
- Listings: /hermes/api/v1/listings?productionId={productionId}

The API returns comprehensive ticket data including section, row, price, and quantity.
"""
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import re

from app.services.scrapers.base import BaseScraper, ListingData

logger = logging.getLogger(__name__)


class VividSeatsScraper(BaseScraper):
    """Vivid Seats scraper using the Hermes API"""

    platform_name = "vividseats"
    base_url = "https://www.vividseats.com"
    api_url = "https://www.vividseats.com/hermes/api/v1"

    def __init__(self):
        super().__init__()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.vividseats.com/",
        }

    async def fetch_listings(self, event_id: str) -> List[ListingData]:
        """
        Fetch listings from Vivid Seats API.

        Args:
            event_id: The production ID (e.g., "6564610")
        """
        try:
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get listings from API
                listings_url = f"{self.api_url}/listings?productionId={event_id}"
                logger.info(f"VividSeats: Fetching {listings_url}")

                response = await client.get(listings_url, headers=self.headers)

                if response.status_code == 403:
                    logger.warning("VividSeats: 403 Forbidden - may be rate limited")
                    return []
                elif response.status_code == 404:
                    logger.warning(f"VividSeats: Event {event_id} not found")
                    return []
                elif response.status_code != 200:
                    logger.warning(f"VividSeats: HTTP {response.status_code}")
                    return []

                data = response.json()
                listings = self._parse_api_response(data, event_id)

                # If no individual listings, try to get stats from production endpoint
                if not listings:
                    listings = await self._fetch_production_stats(client, event_id)

                logger.info(f"VividSeats: Found {len(listings)} listings for event {event_id}")
                return listings

        except httpx.TimeoutException:
            logger.error("VividSeats: Request timed out")
            return []
        except Exception as e:
            logger.error(f"VividSeats: fetch_listings failed: {e}")
            return []

    def _parse_api_response(self, data: dict, event_id: str) -> List[ListingData]:
        """Parse listings from the API response"""
        listings = []

        tickets = data.get("tickets", [])

        for ticket in tickets[:200]:  # Limit to 200 listings
            try:
                listing = self._parse_ticket(ticket, event_id)
                if listing:
                    listings.append(listing)
            except Exception as e:
                logger.debug(f"VividSeats: Failed to parse ticket: {e}")
                continue

        return listings

    def _parse_ticket(self, ticket: dict, event_id: str) -> Optional[ListingData]:
        """Parse a single ticket listing from API data"""
        # API uses short keys: s=section, r=row, q=quantity, p=price
        # But also includes full names as fallback
        price = (
            ticket.get("p") or
            ticket.get("price") or
            ticket.get("allInPricePerTicket") or
            ticket.get("aip") or
            0
        )

        if not price or float(price) <= 0:
            return None

        section = (
            ticket.get("s") or
            ticket.get("sectionName") or
            ticket.get("section") or
            "General"
        )

        row = (
            ticket.get("r") or
            ticket.get("row") or
            None
        )

        quantity = (
            ticket.get("q") or
            ticket.get("quantity") or
            1
        )

        # Get listing ID for unique URL if available
        listing_id = ticket.get("i") or ticket.get("id")

        return ListingData(
            platform="vividseats",
            section=str(section),
            row=str(row) if row else None,
            quantity=int(quantity),
            price_per_ticket=float(price),
            total_price=float(price) * int(quantity),
            listing_url=f"{self.base_url}/production/{event_id}",
            raw_data=ticket,
        )

    async def _fetch_production_stats(self, client: httpx.AsyncClient, event_id: str) -> List[ListingData]:
        """Fetch production-level price statistics as fallback"""
        listings = []

        try:
            prod_url = f"{self.api_url}/productions/{event_id}"
            response = await client.get(prod_url, headers=self.headers)

            if response.status_code != 200:
                return []

            data = response.json()

            min_price = data.get("minPrice")
            max_price = data.get("maxPrice")
            avg_price = data.get("avgPrice") or data.get("medianPrice")

            if min_price:
                listings.append(ListingData(
                    platform="vividseats",
                    section="Various (Low)",
                    row=None,
                    quantity=1,
                    price_per_ticket=float(min_price),
                    total_price=float(min_price),
                    listing_url=f"{self.base_url}/production/{event_id}",
                    raw_data={"type": "min_price", "source": "production_api"},
                ))

            if avg_price and avg_price != min_price:
                listings.append(ListingData(
                    platform="vividseats",
                    section="Various (Avg)",
                    row=None,
                    quantity=1,
                    price_per_ticket=float(avg_price),
                    total_price=float(avg_price),
                    listing_url=f"{self.base_url}/production/{event_id}",
                    raw_data={"type": "avg_price", "source": "production_api"},
                ))

            if max_price and max_price != avg_price:
                listings.append(ListingData(
                    platform="vividseats",
                    section="Various (High)",
                    row=None,
                    quantity=1,
                    price_per_ticket=float(max_price),
                    total_price=float(max_price),
                    listing_url=f"{self.base_url}/production/{event_id}",
                    raw_data={"type": "max_price", "source": "production_api"},
                ))

        except Exception as e:
            logger.debug(f"VividSeats: Production stats fetch failed: {e}")

        return listings

    async def get_production_details(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed production info including venue, date, and price stats"""
        try:
            await self._rate_limit()

            async with httpx.AsyncClient(timeout=30.0) as client:
                prod_url = f"{self.api_url}/productions/{event_id}"
                response = await client.get(prod_url, headers=self.headers)

                if response.status_code != 200:
                    return None

                data = response.json()

                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "date": data.get("localDate"),
                    "venue": data.get("venue", {}).get("name"),
                    "city": data.get("venue", {}).get("city"),
                    "min_price": data.get("minPrice"),
                    "max_price": data.get("maxPrice"),
                    "avg_price": data.get("avgPrice"),
                }

        except Exception as e:
            logger.error(f"VividSeats: get_production_details failed: {e}")
            return None

    async def search_event(self, artist: str, venue: str, date: datetime) -> Optional[str]:
        """Search for an event and return its production ID"""
        try:
            await self._rate_limit()

            # Search URL - scrape search results page
            search_query = artist.replace(" ", "+")
            url = f"{self.base_url}/search?searchTerm={search_query}"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    **self.headers,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                })

                if response.status_code != 200:
                    return None

                # Find production URLs with dates
                # Pattern: /artist-tickets-venue-date/production/ID
                date_str = date.strftime("%-m-%-d-%Y")

                # First try exact date match
                pattern = rf'href="[^"]*{date_str}[^"]*production/(\d+)"'
                matches = re.findall(pattern, response.text, re.IGNORECASE)

                if matches:
                    return matches[0]

                # Fallback: any production ID from search (first non-parking result)
                pattern = r'href="(/[^"]*-tickets-[^"]*production/(\d+))"'
                for url_match, prod_id in re.findall(pattern, response.text):
                    if "parking" not in url_match.lower():
                        return prod_id

            return None

        except Exception as e:
            logger.error(f"VividSeats: search_event failed: {e}")
            return None

    async def get_performer_events(self, performer_name: str) -> List[dict]:
        """Get all events for a performer by searching"""
        try:
            await self._rate_limit()

            search_query = performer_name.replace(" ", "+")
            url = f"{self.base_url}/search?searchTerm={search_query}"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    **self.headers,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                })

                if response.status_code != 200:
                    return []

                # Extract all production URLs
                pattern = rf'href="(/[^"]*{performer_name.lower().replace(" ", "-")}[^"]*production/(\d+))"'
                matches = re.findall(pattern, response.text, re.IGNORECASE)

                events = []
                seen_ids = set()

                for url_path, prod_id in matches:
                    if prod_id in seen_ids or "parking" in url_path.lower():
                        continue
                    seen_ids.add(prod_id)

                    # Extract date from URL
                    date_match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', url_path)
                    if date_match:
                        month, day, year = date_match.groups()
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    else:
                        date_str = None

                    events.append({
                        "production_id": prod_id,
                        "date": date_str,
                        "url": f"{self.base_url}{url_path}",
                    })

                # Sort by date
                events.sort(key=lambda x: x.get("date") or "9999")

                # Optionally fetch production details for each
                for event in events[:20]:  # Limit API calls
                    details = await self.get_production_details(event["production_id"])
                    if details:
                        event.update(details)
                    await self._rate_limit()

                return events

        except Exception as e:
            logger.error(f"VividSeats: get_performer_events failed: {e}")
            return []
