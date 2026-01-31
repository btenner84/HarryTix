"""
StubHub scraper using Playwright to get real prices
"""
import asyncio
import re
from typing import Optional
from playwright.async_api import async_playwright


async def get_stubhub_prices(event_id: str, section_filter: str, min_qty: int = 2) -> dict:
    """
    Scrape StubHub for real prices in a specific section.
    Returns dict with listings_count, total_seats, min_price, avg_lowest_2, etc.
    """
    result = {
        "listings_count": 0,
        "total_seats": 0,
        "min_price": None,
        "max_price": None,
        "avg_lowest_2": None,
        "prices": []
    }
    
    url = f"https://www.stubhub.com/event/{event_id}"
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Navigate to event page
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Wait for listings to load
            await page.wait_for_selector('[data-testid="listing-card"], .ListingCard', timeout=10000)
            
            # Get all listing cards
            listings = await page.query_selector_all('[data-testid="listing-card"], .ListingCard, [class*="listing"]')
            
            prices = []
            for listing in listings:
                try:
                    # Get section text
                    section_el = await listing.query_selector('[class*="section"], [class*="Section"]')
                    section_text = await section_el.inner_text() if section_el else ""
                    
                    # Check if section matches filter
                    if section_filter.upper() not in section_text.upper():
                        continue
                    
                    # Get quantity
                    qty_el = await listing.query_selector('[class*="quantity"], [class*="Quantity"], [class*="ticket"]')
                    qty_text = await qty_el.inner_text() if qty_el else "1"
                    qty_match = re.search(r'(\d+)', qty_text)
                    qty = int(qty_match.group(1)) if qty_match else 1
                    
                    # Skip if less than min quantity
                    if qty < min_qty:
                        continue
                    
                    # Get price
                    price_el = await listing.query_selector('[class*="price"], [class*="Price"]')
                    price_text = await price_el.inner_text() if price_el else ""
                    price_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', price_text.replace(',', ''))
                    
                    if price_match:
                        price = float(price_match.group(1))
                        if price > 100:  # Filter out unrealistic prices
                            prices.append(price)
                            result["total_seats"] += qty
                            
                except Exception as e:
                    continue
            
            await browser.close()
            
            if prices:
                prices.sort()
                result["listings_count"] = len(prices)
                result["min_price"] = prices[0]
                result["max_price"] = prices[-1]
                result["prices"] = prices[:5]  # Keep top 5 lowest
                
                if len(prices) >= 2:
                    result["avg_lowest_2"] = round((prices[0] + prices[1]) / 2, 2)
                else:
                    result["avg_lowest_2"] = prices[0]
                    
    except Exception as e:
        print(f"StubHub scraper error for event {event_id}: {e}")
    
    return result


# Test function
async def test_scraper():
    # Test with Set A event (Sept 2)
    result = await get_stubhub_prices("160334450", "SECTION 2", min_qty=1)
    print(f"Set A (200s): {result}")


if __name__ == "__main__":
    asyncio.run(test_scraper())
