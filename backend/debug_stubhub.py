#!/usr/bin/env python3
"""Click Section 112 on StubHub map to filter listings."""
import asyncio
import re
from playwright.async_api import async_playwright

async def click_section_112():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined});')

        url = 'https://www.stubhub.com/event/160334461'
        print(f"Loading: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(6000)

        # Close popup
        try:
            await page.click('button:has-text("Continue")', timeout=3000)
            await page.wait_for_timeout(2000)
        except:
            pass

        # Take initial screenshot
        await page.screenshot(path='/tmp/stubhub_before_click.png')
        print("Saved screenshot before clicking")

        # Try to find and click on Section 112 text/element on the map
        # First, look for any element containing "112"
        clicked = False

        # Method 1: Try to find a clickable section 112 element
        try:
            section_elem = await page.locator('text=112').first
            if section_elem:
                await section_elem.click(timeout=5000)
                clicked = True
                print("Clicked on '112' text element")
        except:
            pass

        if not clicked:
            # Method 2: Click on the approximate location of Section 112 on the map
            # From the screenshot, Section 112 is in the lower left area of the venue map
            # The map seems to be roughly centered, and 112 is on the lower-left
            # Let's estimate coordinates: map is on left side of page, 112 is bottom-left of floor
            try:
                # Click approximately where Section 112 should be on the map
                # Map appears to start around x=50 and go to x=600
                # Section 112 is roughly at x=270, y=350 based on the screenshot
                await page.mouse.click(270, 350)
                print("Clicked at coordinates (270, 350)")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Click failed: {e}")

        await page.wait_for_timeout(3000)

        # Take screenshot after clicking
        await page.screenshot(path='/tmp/stubhub_after_click.png')
        print("Saved screenshot after clicking")

        # Now get the listings that appear
        text = await page.evaluate("() => document.body.innerText")
        lines = text.split('\n')

        all_listings = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('Section 112'):
                section = line
                row = None
                price = None
                tickets = None

                for j in range(i+1, min(i+8, len(lines))):
                    next_line = lines[j].strip()
                    if next_line.startswith('Row '):
                        row = next_line.replace('Row ', '')
                    if 'tickets' in next_line.lower():
                        match = re.match(r'(\d+)', next_line)
                        if match:
                            tickets = int(match.group(1))
                    if next_line.startswith('$'):
                        try:
                            price = float(next_line.replace('$', '').replace(',', ''))
                        except:
                            pass

                if price and price > 100:
                    all_listings.append({
                        'section': section,
                        'row': row,
                        'price': price,
                        'qty': tickets or 1
                    })
            i += 1

        print(f"\n=== SECTION 112 LISTINGS FOUND: {len(all_listings)} ===")
        for l in sorted(all_listings, key=lambda x: x['price']):
            print(f"  Row {l['row']}: ${l['price']:.0f} ({l['qty']} tickets)")

        # Also look for any 100-level section prices
        print("\n=== ALL VISIBLE PRICES ===")
        price_pattern = re.compile(r'Section (\d+).*?Row (\w+).*?\$(\d{1,3}(?:,\d{3})*)', re.DOTALL)
        matches = price_pattern.findall(text)
        for m in matches[:20]:
            sec, row, price = m
            print(f"  Section {sec} Row {row}: ${price}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_section_112())
