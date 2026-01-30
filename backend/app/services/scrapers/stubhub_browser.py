"""
StubHub Scraper using Playwright (headless Chromium)
Bypasses bot protection by using a real browser engine.
"""
import asyncio
import json
import re
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser


class StubHubBrowserScraper:
    """Scrapes StubHub using headless Chromium to bypass bot protection."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.base_url = "https://www.stubhub.com"

    async def _get_browser(self):
        """Get or create browser instance."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
        return self.browser

    async def _create_page(self) -> Page:
        """Create a new page with stealth settings."""
        browser = await self._get_browser()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )
        page = await context.new_page()

        # Add stealth scripts to avoid detection
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

        return page

    async def get_event_listings(self, event_url: str) -> dict:
        """
        Fetch all ticket listings for a StubHub event.

        Args:
            event_url: Full StubHub event URL or event ID

        Returns:
            Dict with listings, stats, and metadata
        """
        # Handle both full URL and event ID
        if event_url.isdigit():
            url = f"{self.base_url}/event/{event_url}"
        elif not event_url.startswith('http'):
            url = f"{self.base_url}/{event_url}"
        else:
            url = event_url

        page = await self._create_page()
        listings = []

        try:
            print(f"[StubHub] Navigating to: {url}")

            # Navigate with longer timeout and don't wait for full network idle
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # Wait for page to stabilize
            await page.wait_for_timeout(5000)

            # Try to wait for price elements to appear
            try:
                await page.wait_for_selector('[class*="price"], [class*="Price"], [data-testid*="price"]', timeout=15000)
                print("[StubHub] Found price elements")
            except:
                print("[StubHub] No price elements found, continuing anyway...")

            # Scroll to load more content
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(2000)

            # Try to find and extract listing data from the page
            # StubHub loads data via JavaScript, so we need to extract from DOM or intercept API calls

            # Method 1: Extract from DOM
            listing_elements = await page.query_selector_all('[data-testid="listing-row"], .ListingRow, [class*="listing"]')

            if listing_elements:
                print(f"[StubHub] Found {len(listing_elements)} listing elements")
                for elem in listing_elements[:100]:  # Limit to 100
                    try:
                        text = await elem.inner_text()
                        # Parse listing info from text
                        listing = self._parse_listing_text(text)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        continue

            # Method 2: Extract from page's JavaScript data
            if not listings:
                print("[StubHub] Trying to extract from page data...")
                page_data = await page.evaluate("""
                    () => {
                        // Try to find listing data in window object
                        if (window.__NEXT_DATA__) return window.__NEXT_DATA__;
                        if (window.__data) return window.__data;
                        if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;

                        // Try to find in script tags
                        const scripts = document.querySelectorAll('script');
                        for (const script of scripts) {
                            const text = script.textContent;
                            if (text && text.includes('listings')) {
                                try {
                                    const match = text.match(/\\{[^{}]*"listings"[^{}]*\\}/);
                                    if (match) return JSON.parse(match[0]);
                                } catch {}
                            }
                        }
                        return null;
                    }
                """)

                if page_data:
                    listings = self._extract_listings_from_data(page_data)

            # Method 3: Extract all prices from page content
            if not listings:
                print("[StubHub] Extracting prices from page content...")
                content = await page.content()
                listings = self._extract_prices_from_html(content)

            # Method 4: Intercept network requests (slowest, last resort)
            if not listings:
                print("[StubHub] Trying network interception...")
                listings = await self._intercept_api_calls(page, url)

            # Get page title for event name
            title = await page.title()

            # Calculate stats
            if listings:
                prices = [l['price'] for l in listings if l.get('price')]
                stats = {
                    'min_price': min(prices) if prices else None,
                    'max_price': max(prices) if prices else None,
                    'avg_price': sum(prices) / len(prices) if prices else None,
                    'listing_count': len(listings),
                }
            else:
                stats = {'min_price': None, 'max_price': None, 'avg_price': None, 'listing_count': 0}

            return {
                'url': url,
                'title': title,
                'listings': listings,
                'stats': stats,
                'source': 'stubhub',
            }

        except Exception as e:
            print(f"[StubHub] Error: {e}")
            return {
                'url': url,
                'error': str(e),
                'listings': [],
                'stats': {'min_price': None, 'max_price': None, 'avg_price': None, 'listing_count': 0},
                'source': 'stubhub',
            }
        finally:
            await page.close()

    async def _intercept_api_calls(self, page: Page, url: str) -> list:
        """Intercept XHR/Fetch calls to find listing data."""
        listings = []
        api_data = []

        async def handle_response(response):
            if 'inventory' in response.url or 'listing' in response.url:
                try:
                    data = await response.json()
                    api_data.append(data)
                except:
                    pass

        page.on('response', handle_response)

        # Reload to capture API calls
        await page.reload(wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(3000)

        # Process captured API data
        for data in api_data:
            extracted = self._extract_listings_from_data(data)
            listings.extend(extracted)

        return listings

    def _extract_prices_from_html(self, html: str) -> list:
        """Extract all prices from HTML content."""
        listings = []

        # Find all price patterns in the HTML
        price_patterns = re.findall(r'\$([0-9,]+(?:\.[0-9]{2})?)', html)

        # Filter reasonable ticket prices (between $50 and $50,000)
        valid_prices = []
        for p in price_patterns:
            try:
                price = float(p.replace(',', ''))
                if 50 <= price <= 50000:
                    valid_prices.append(price)
            except:
                continue

        # Create listings from unique prices (approximation)
        seen_prices = set()
        for price in valid_prices:
            if price not in seen_prices:
                seen_prices.add(price)
                listings.append({
                    'section': None,
                    'row': None,
                    'quantity': 1,
                    'price': price,
                })

        print(f"[StubHub] Extracted {len(listings)} prices from HTML")
        return listings

    def _parse_listing_text(self, text: str) -> Optional[dict]:
        """Parse listing info from DOM text."""
        try:
            # Look for price pattern like $500 or $1,200
            price_match = re.search(r'\$([0-9,]+(?:\.[0-9]{2})?)', text)
            price = float(price_match.group(1).replace(',', '')) if price_match else None

            # Look for section
            section_match = re.search(r'(Section\s*\d+|GA|PIT|Floor|General Admission)', text, re.I)
            section = section_match.group(1) if section_match else None

            # Look for row
            row_match = re.search(r'Row\s*([A-Z0-9]+)', text, re.I)
            row = row_match.group(1) if row_match else None

            # Look for quantity
            qty_match = re.search(r'(\d+)\s*ticket', text, re.I)
            quantity = int(qty_match.group(1)) if qty_match else 1

            if price:
                return {
                    'section': section,
                    'row': row,
                    'quantity': quantity,
                    'price': price,
                    'raw_text': text[:200],
                }
            return None
        except:
            return None

    def _extract_listings_from_data(self, data: dict) -> list:
        """Extract listings from JSON data structure."""
        listings = []

        if not isinstance(data, dict):
            return listings

        # Try common data paths
        possible_paths = [
            data.get('listings', []),
            data.get('items', []),
            data.get('tickets', []),
            data.get('props', {}).get('pageProps', {}).get('listings', []),
            data.get('data', {}).get('listings', []),
        ]

        for path_data in possible_paths:
            if isinstance(path_data, list):
                for item in path_data:
                    if isinstance(item, dict):
                        listing = {
                            'section': item.get('section') or item.get('sectionName') or item.get('s'),
                            'row': item.get('row') or item.get('rowName') or item.get('r'),
                            'quantity': item.get('quantity') or item.get('qty') or item.get('q') or 1,
                            'price': item.get('price') or item.get('listPrice') or item.get('currentPrice', {}).get('amount'),
                        }
                        if listing['price']:
                            listings.append(listing)

        return listings

    async def close(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None


# Test function
async def test_stubhub_scraper():
    """Test the StubHub scraper."""
    scraper = StubHubBrowserScraper()

    try:
        # Test with Harry Styles event
        result = await scraper.get_event_listings("harry-styles-new-york-tickets-9-18-2026/event/157543284")

        print(f"\n=== StubHub Scraper Results ===")
        print(f"URL: {result.get('url')}")
        print(f"Title: {result.get('title')}")
        print(f"Listings found: {result['stats']['listing_count']}")
        print(f"Price range: ${result['stats']['min_price']} - ${result['stats']['max_price']}")

        if result.get('listings'):
            print(f"\nSample listings:")
            for listing in result['listings'][:5]:
                print(f"  {listing.get('section')} Row {listing.get('row')} - ${listing.get('price')} ({listing.get('quantity')} tickets)")

        if result.get('error'):
            print(f"Error: {result['error']}")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_stubhub_scraper())
