"""
StubHub Scraper - Robust Implementation

RELIABILITY: MEDIUM - StubHub has strong anti-bot protection (202 async responses)
ANTI-BOT: HIGH - Session tracking, rate limiting, async bot detection

URL Patterns:
- Event page: https://www.stubhub.com/event/{eventID}
- Example: https://www.stubhub.com/harry-styles-new-york-tickets-9-18-2026/event/158900746

HOW TO FIND EVENT IDS MANUALLY:
1. Go to stubhub.com in your browser
2. Search for the event
3. Click on the event to go to the ticket listing page
4. Look at the URL - the event ID is the number after /event/
   Example: .../event/158900746 -> Event ID is 158900746

Data Sources (in order of preference):
1. Page embedded JSON (modern Next.js Flight format or __NEXT_DATA__)
2. Script tag data extraction
3. Regex fallback for prices

NOTE: Due to bot detection, you may need to manually copy event IDs from your browser.
The scraper will work once you have valid event IDs.
"""
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import re
from bs4 import BeautifulSoup

from app.services.scrapers.base import BaseScraper, ListingData

logger = logging.getLogger(__name__)


class StubHubScraper(BaseScraper):
    """
    StubHub scraper with multiple extraction strategies.

    Handles both modern Next.js (React Server Components) and traditional __NEXT_DATA__.
    """

    platform_name = "stubhub"
    base_url = "https://www.stubhub.com"

    def __init__(self):
        super().__init__()
        # Full browser-like headers are critical
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Cache-Control": "max-age=0",
        }

    async def fetch_listings(self, event_id: str) -> List[ListingData]:
        """
        Fetch listings for a StubHub event using multiple strategies.

        Args:
            event_id: The event ID from the URL (e.g., "9670859")
        """
        try:
            await self._rate_limit()

            url = f"{self.base_url}/event/{event_id}"
            logger.info(f"StubHub: Fetching {url}")

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code == 202:
                    logger.warning("StubHub: 202 Accepted - bot detection triggered. Event ID may need to be accessed from a real browser.")
                    return []
                elif response.status_code == 403:
                    logger.warning("StubHub: 403 Forbidden - blocked")
                    return []
                elif response.status_code == 404:
                    logger.warning(f"StubHub: Event {event_id} not found")
                    return []
                elif response.status_code != 200:
                    logger.warning(f"StubHub: HTTP {response.status_code}")
                    return []

                html = response.text
                listings = []

                # Strategy 1: Parse Next.js Flight data (modern format)
                listings = self._parse_flight_data(html, event_id)
                if listings:
                    logger.info(f"StubHub: Flight data extracted {len(listings)} listings")
                    return listings

                # Strategy 2: Parse traditional __NEXT_DATA__
                listings = self._parse_next_data(html, event_id)
                if listings:
                    logger.info(f"StubHub: __NEXT_DATA__ extracted {len(listings)} listings")
                    return listings

                # Strategy 3: Parse script tags for JSON data
                listings = self._parse_script_tags(html, event_id)
                if listings:
                    logger.info(f"StubHub: Script tags extracted {len(listings)} listings")
                    return listings

                # Strategy 4: Regex fallback
                listings = self._regex_extraction(html, event_id)
                if listings:
                    logger.info(f"StubHub: Regex extracted {len(listings)} price points")
                    return listings

                logger.warning("StubHub: All extraction methods failed")
                return []

        except httpx.TimeoutException:
            logger.error("StubHub: Request timed out")
            return []
        except Exception as e:
            logger.error(f"StubHub: fetch_listings failed: {e}")
            return []

    def _parse_flight_data(self, html: str, event_id: str) -> List[ListingData]:
        """
        Parse Next.js 13+ React Server Components Flight data.

        Modern Next.js embeds data in script tags like:
        <script>self.__next_f.push([1, "...data..."])</script>
        """
        listings = []

        try:
            # Find all flight data chunks
            flight_pattern = r'self\.__next_f\.push\(\[1,\s*"([^"]+)"\]\)'
            matches = re.findall(flight_pattern, html)

            if not matches:
                return []

            # Combine and decode flight data
            combined_data = ""
            for chunk in matches:
                # Unescape the JSON string
                try:
                    decoded = chunk.encode().decode('unicode_escape')
                    combined_data += decoded
                except:
                    combined_data += chunk

            # Look for listing data patterns in the decoded content
            listings = self._extract_listings_from_text(combined_data, event_id)

            # Also try to find JSON objects within the flight data
            json_pattern = r'\{[^{}]*"price"[^{}]*\}'
            json_matches = re.findall(json_pattern, combined_data)

            for json_str in json_matches[:100]:
                try:
                    obj = json.loads(json_str)
                    listing = self._parse_listing_object(obj, event_id)
                    if listing:
                        listings.append(listing)
                except:
                    continue

        except Exception as e:
            logger.debug(f"StubHub: Flight data parsing error: {e}")

        return listings

    def _parse_next_data(self, html: str, event_id: str) -> List[ListingData]:
        """Parse traditional __NEXT_DATA__ JSON blob."""
        listings = []

        try:
            pattern = r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>'
            match = re.search(pattern, html, re.DOTALL)

            if not match:
                return []

            data = json.loads(match.group(1))

            # Navigate various possible paths
            page_props = data.get("props", {}).get("pageProps", {})

            # Try different listing locations
            listing_sources = [
                page_props.get("listings", []),
                page_props.get("eventListings", []),
                page_props.get("ticketListings", []),
                page_props.get("initialListings", []),
                page_props.get("inventory", {}).get("listings", []),
                page_props.get("data", {}).get("listings", []),
            ]

            for source in listing_sources:
                if source:
                    for item in source[:100]:
                        listing = self._parse_listing_object(item, event_id)
                        if listing:
                            listings.append(listing)
                    if listings:
                        return listings

            # Try event-level price stats if no listings
            event_data = (
                page_props.get("event", {}) or
                page_props.get("eventData", {}) or
                page_props.get("data", {}).get("event", {}) or
                {}
            )

            if event_data:
                listings = self._create_summary_from_event(event_data, event_id)

        except json.JSONDecodeError as e:
            logger.debug(f"StubHub: __NEXT_DATA__ JSON parse error: {e}")
        except Exception as e:
            logger.debug(f"StubHub: __NEXT_DATA__ parsing error: {e}")

        return listings

    def _parse_script_tags(self, html: str, event_id: str) -> List[ListingData]:
        """Parse all script tags for embedded JSON data."""
        listings = []

        try:
            soup = BeautifulSoup(html, 'lxml')
            script_tags = soup.find_all('script')

            for script in script_tags:
                content = script.string
                if not content:
                    continue

                # Look for JSON objects with listing data
                # Pattern: window.* = {...} or var * = {...}
                patterns = [
                    r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
                    r'window\.initialState\s*=\s*({.*?});',
                    r'"listings"\s*:\s*(\[.*?\])',
                    r'"inventory"\s*:\s*(\{.*?\})',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)

                            # Handle list of listings
                            if isinstance(data, list):
                                for item in data[:100]:
                                    listing = self._parse_listing_object(item, event_id)
                                    if listing:
                                        listings.append(listing)

                            # Handle object with listings key
                            elif isinstance(data, dict):
                                items = (
                                    data.get("listings", []) or
                                    data.get("items", []) or
                                    data.get("inventory", []) or
                                    []
                                )
                                for item in items[:100]:
                                    listing = self._parse_listing_object(item, event_id)
                                    if listing:
                                        listings.append(listing)

                            if listings:
                                return listings

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.debug(f"StubHub: Script tag parsing error: {e}")

        return listings

    def _extract_listings_from_text(self, text: str, event_id: str) -> List[ListingData]:
        """Extract listing information from raw text/JSON fragments."""
        listings = []
        prices_found = {}

        try:
            # Extract section-price pairs
            # Pattern: "sectionName":"Section 101"..."price":150
            section_pattern = r'"(?:sectionName|section)"\s*:\s*"([^"]+)"'
            price_pattern = r'"(?:price|amount|currentPrice)"\s*:\s*(\d+(?:\.\d+)?)'
            row_pattern = r'"row"\s*:\s*"([^"]+)"'
            qty_pattern = r'"quantity"\s*:\s*(\d+)'

            sections = re.findall(section_pattern, text)
            prices = re.findall(price_pattern, text)
            rows = re.findall(row_pattern, text)
            qtys = re.findall(qty_pattern, text)

            # Create listings from matched data
            # This is imperfect but captures price ranges
            valid_prices = []
            for p in prices:
                try:
                    price = float(p)
                    if 10 <= price <= 50000:  # Reasonable ticket price range
                        valid_prices.append(price)
                except:
                    continue

            if valid_prices:
                # Dedupe and create summary listings
                unique_prices = sorted(set(valid_prices))

                # Create low/median/high
                if unique_prices:
                    listings.append(ListingData(
                        platform="stubhub",
                        section=sections[0] if sections else "Various (Low)",
                        row=rows[0] if rows else None,
                        quantity=1,
                        price_per_ticket=unique_prices[0],
                        total_price=unique_prices[0],
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "extracted_min", "total_found": len(unique_prices)},
                    ))

                if len(unique_prices) > 2:
                    median_idx = len(unique_prices) // 2
                    listings.append(ListingData(
                        platform="stubhub",
                        section="Various (Median)",
                        row=None,
                        quantity=1,
                        price_per_ticket=unique_prices[median_idx],
                        total_price=unique_prices[median_idx],
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "extracted_median"},
                    ))

                if len(unique_prices) > 1:
                    listings.append(ListingData(
                        platform="stubhub",
                        section="Various (High)",
                        row=None,
                        quantity=1,
                        price_per_ticket=unique_prices[-1],
                        total_price=unique_prices[-1],
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "extracted_max"},
                    ))

        except Exception as e:
            logger.debug(f"StubHub: Text extraction error: {e}")

        return listings

    def _parse_listing_object(self, obj: Dict[Any, Any], event_id: str) -> Optional[ListingData]:
        """Parse a single listing object from any source."""
        try:
            # Try various price field names
            price = None
            price_fields = [
                ("currentPrice", "amount"),
                ("listingPrice", "amount"),
                ("price", "amount"),
                ("price", None),
                ("amount", None),
                ("pricePerTicket", None),
                ("ticketPrice", None),
            ]

            for field, subfield in price_fields:
                if field in obj:
                    val = obj[field]
                    if subfield and isinstance(val, dict):
                        price = val.get(subfield)
                    elif not subfield:
                        price = val
                    if price:
                        break

            if not price:
                return None

            try:
                price = float(price)
            except (TypeError, ValueError):
                return None

            if price <= 0 or price > 100000:
                return None

            # Extract other fields
            section = (
                obj.get("sectionName") or
                obj.get("section") or
                obj.get("sellerSectionName") or
                obj.get("zoneName") or
                obj.get("s") or
                "General"
            )

            row = obj.get("row") or obj.get("rowName") or obj.get("r")

            quantity = obj.get("quantity") or obj.get("qty") or obj.get("q") or 1
            try:
                quantity = int(quantity)
            except:
                quantity = 1

            return ListingData(
                platform="stubhub",
                section=str(section),
                row=str(row) if row else None,
                quantity=quantity,
                price_per_ticket=price,
                total_price=price * quantity,
                listing_url=f"{self.base_url}/event/{event_id}",
                raw_data=obj,
            )

        except Exception as e:
            logger.debug(f"StubHub: Failed to parse listing object: {e}")
            return None

    def _create_summary_from_event(self, event_data: dict, event_id: str) -> List[ListingData]:
        """Create summary listings from event-level price data."""
        listings = []

        min_price = (
            event_data.get("minPrice") or
            event_data.get("lowestPrice") or
            event_data.get("minListPrice") or
            event_data.get("stats", {}).get("minPrice")
        )

        max_price = (
            event_data.get("maxPrice") or
            event_data.get("highestPrice") or
            event_data.get("maxListPrice") or
            event_data.get("stats", {}).get("maxPrice")
        )

        ticket_count = (
            event_data.get("listingCount") or
            event_data.get("ticketCount") or
            event_data.get("totalListings")
        )

        if min_price:
            try:
                listings.append(ListingData(
                    platform="stubhub",
                    section="Various (Low)",
                    row=None,
                    quantity=1,
                    price_per_ticket=float(min_price),
                    total_price=float(min_price),
                    listing_url=f"{self.base_url}/event/{event_id}",
                    raw_data={"type": "event_min_price", "ticket_count": ticket_count},
                ))
            except:
                pass

        if max_price and max_price != min_price:
            try:
                listings.append(ListingData(
                    platform="stubhub",
                    section="Various (High)",
                    row=None,
                    quantity=1,
                    price_per_ticket=float(max_price),
                    total_price=float(max_price),
                    listing_url=f"{self.base_url}/event/{event_id}",
                    raw_data={"type": "event_max_price", "ticket_count": ticket_count},
                ))
            except:
                pass

        return listings

    def _regex_extraction(self, html: str, event_id: str) -> List[ListingData]:
        """Last resort: extract prices via regex patterns."""
        listings = []

        try:
            # Multiple patterns to find prices
            patterns = [
                r'"currentPrice"\s*:\s*\{\s*"amount"\s*:\s*(\d+(?:\.\d+)?)',
                r'"listingPrice"\s*:\s*\{\s*"amount"\s*:\s*(\d+(?:\.\d+)?)',
                r'"price"\s*:\s*(\d+(?:\.\d+)?)',
                r'"amount"\s*:\s*(\d+(?:\.\d+)?)',
                r'\$(\d{2,4}(?:\.\d{2})?)',
                r'(\d{2,4}(?:\.\d{2})?)\s*(?:per ticket|each|/ticket)',
            ]

            all_prices = []
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for m in matches:
                    try:
                        price = float(m)
                        if 20 <= price <= 50000:
                            all_prices.append(price)
                    except:
                        continue

            if all_prices:
                unique_prices = sorted(set(all_prices))

                if unique_prices:
                    listings.append(ListingData(
                        platform="stubhub",
                        section="Various (Low)",
                        row=None,
                        quantity=1,
                        price_per_ticket=unique_prices[0],
                        total_price=unique_prices[0],
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "regex_min", "prices_found": len(unique_prices)},
                    ))

                if len(unique_prices) > 2:
                    median_price = unique_prices[len(unique_prices) // 2]
                    listings.append(ListingData(
                        platform="stubhub",
                        section="Various (Median)",
                        row=None,
                        quantity=1,
                        price_per_ticket=median_price,
                        total_price=median_price,
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "regex_median"},
                    ))

                if len(unique_prices) > 1:
                    listings.append(ListingData(
                        platform="stubhub",
                        section="Various (High)",
                        row=None,
                        quantity=1,
                        price_per_ticket=unique_prices[-1],
                        total_price=unique_prices[-1],
                        listing_url=f"{self.base_url}/event/{event_id}",
                        raw_data={"type": "regex_max"},
                    ))

        except Exception as e:
            logger.error(f"StubHub: Regex extraction failed: {e}")

        return listings

    async def search_event(self, artist: str, venue: str, date: datetime) -> Optional[str]:
        """Search for an event and return its event ID."""
        try:
            await self._rate_limit()

            # Search page
            search_query = f"{artist}".replace(" ", "+")
            url = f"{self.base_url}/secure/search?q={search_query}"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code != 200:
                    logger.debug(f"StubHub: Search returned {response.status_code}")
                    return None

                # Find event IDs in the response
                # Pattern: /event/[7-8 digit ID]
                pattern = r'/event/(\d{7,8})'
                matches = re.findall(pattern, response.text)

                # Return first unique match
                seen = set()
                for match in matches:
                    if match not in seen:
                        return match
                    seen.add(match)

            return None

        except Exception as e:
            logger.error(f"StubHub: search_event failed: {e}")
            return None

    async def get_performer_events(self, performer_id: str) -> List[dict]:
        """Get all events for a performer."""
        events = []

        try:
            await self._rate_limit()

            url = f"{self.base_url}/performer/{performer_id}"

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)

                if response.status_code != 200:
                    return []

                # Extract event links
                pattern = r'href="(/[^"]*-tickets/event/(\d+))"'
                matches = re.findall(pattern, response.text)

                seen = set()
                for url_path, event_id in matches[:20]:
                    if event_id not in seen:
                        seen.add(event_id)
                        events.append({
                            "event_id": event_id,
                            "url": f"{self.base_url}{url_path}",
                        })

        except Exception as e:
            logger.error(f"StubHub: get_performer_events failed: {e}")

        return events
