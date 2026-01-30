#!/usr/bin/env python3
"""Take StubHub screenshots for all 5 events to verify prices."""
import asyncio
from playwright.async_api import async_playwright

EVENTS = [
    ("Set A - Sept 2", "160334450", "200s Row 1"),
    ("Set C - Sept 18", "160334461", "Section 112"),
    ("Set B - Sept 19", "160334462", "Left GA"),
    ("Set E - Sept 25", "160334464", "100s"),
    ("Set D - Oct 9", "160334466", "Left GA"),
]

async def screenshot_events():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined});')

        for name, event_id, section in EVENTS:
            print(f"\n{'='*50}")
            print(f"{name} - Looking for {section}")
            print(f"StubHub Event ID: {event_id}")

            url = f'https://www.stubhub.com/event/{event_id}'
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(5000)

            # Close popup
            try:
                await page.click('button:has-text("Continue")', timeout=3000)
                await page.wait_for_timeout(1500)
            except:
                pass

            # Screenshot
            filename = f'/tmp/stubhub_{event_id}.png'
            await page.screenshot(path=filename)
            print(f"Screenshot saved: {filename}")

        await browser.close()
        print("\n\nAll screenshots saved! Check /tmp/stubhub_*.png")

if __name__ == "__main__":
    asyncio.run(screenshot_events())
