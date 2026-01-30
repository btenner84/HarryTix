"""
Helper script to find event IDs on each platform for your Harry Styles MSG shows.
Run with: python find_events.py

This will search each platform and show you the event IDs to add to your database.
"""
import asyncio
import httpx
import re
import json
from datetime import datetime


async def find_stubhub_events():
    """Find Harry Styles MSG events on StubHub"""
    print("\n=== STUBHUB ===")
    print("Searching for Harry Styles at MSG...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://www.stubhub.com/harry-styles-tickets/performer/834992",
            headers=headers,
            follow_redirects=True,
        )

        # Find event URLs and IDs
        pattern = r'href="([^"]*harry-styles[^"]*madison-square-garden[^"]*)"'
        matches = re.findall(pattern, response.text, re.IGNORECASE)

        if matches:
            print("\nFound events:")
            seen = set()
            for url in matches[:10]:
                # Extract event ID from URL
                event_match = re.search(r'/event/(\d+)', url)
                if event_match and event_match.group(1) not in seen:
                    event_id = event_match.group(1)
                    seen.add(event_id)
                    print(f"  Event ID: {event_id}")
                    print(f"  URL: https://www.stubhub.com{url}")
                    print()
        else:
            print("No MSG events found. Try searching manually:")
            print("  https://www.stubhub.com/harry-styles-tickets/performer/834992")


async def find_seatgeek_events():
    """Find Harry Styles MSG events on SeatGeek"""
    print("\n=== SEATGEEK ===")
    print("Searching for Harry Styles at MSG...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://seatgeek.com/harry-styles-tickets",
            headers=headers,
            follow_redirects=True,
        )

        # Find event URLs with IDs
        # Pattern: /harry-styles-tickets/new-york-new-york-madison-square-garden-YYYY-MM-DD/12345678
        pattern = r'href="(/[^"]*harry-styles[^"]*madison-square-garden[^"]*)"'
        matches = re.findall(pattern, response.text, re.IGNORECASE)

        if matches:
            print("\nFound events:")
            seen = set()
            for url in matches[:10]:
                # Extract event ID (last number in URL)
                id_match = re.search(r'/(\d{7,})$', url)
                if id_match and id_match.group(1) not in seen:
                    event_id = id_match.group(1)
                    seen.add(event_id)
                    print(f"  Event ID: {event_id}")
                    print(f"  URL: https://seatgeek.com{url}")
                    print()
        else:
            print("No MSG events found. Try searching manually:")
            print("  https://seatgeek.com/harry-styles-tickets")


async def find_vividseats_events():
    """Find Harry Styles MSG events on Vivid Seats"""
    print("\n=== VIVID SEATS ===")
    print("Searching for Harry Styles at MSG...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://www.vividseats.com/harry-styles-tickets--concerts/performer/29498",
            headers=headers,
            follow_redirects=True,
        )

        # Find production URLs with IDs
        # Pattern: /production/12345
        pattern = r'href="(/[^"]*harry-styles[^"]*madison-square-garden[^"]*)"'
        matches = re.findall(pattern, response.text, re.IGNORECASE)

        # Also try production pattern
        prod_pattern = r'/production/(\d+)'
        prod_matches = re.findall(prod_pattern, response.text)

        if prod_matches:
            print("\nFound production IDs:")
            seen = set()
            for prod_id in prod_matches[:10]:
                if prod_id not in seen:
                    seen.add(prod_id)
                    print(f"  Production ID: {prod_id}")
                    print(f"  URL: https://www.vividseats.com/production/{prod_id}")
                    print()
        else:
            print("No MSG events found. Try searching manually:")
            print("  https://www.vividseats.com/harry-styles-tickets--concerts/performer/29498")


async def main():
    print("=" * 60)
    print("HARRY STYLES MSG EVENT FINDER")
    print("=" * 60)
    print("\nThis script searches each platform for Harry Styles events")
    print("at Madison Square Garden. Copy the event IDs to your database.")

    try:
        await find_stubhub_events()
    except Exception as e:
        print(f"StubHub search failed: {e}")

    try:
        await find_seatgeek_events()
    except Exception as e:
        print(f"SeatGeek search failed: {e}")

    try:
        await find_vividseats_events()
    except Exception as e:
        print(f"Vivid Seats search failed: {e}")

    print("\n" + "=" * 60)
    print("HOW TO ADD EVENT IDs TO YOUR DATABASE")
    print("=" * 60)
    print("""
After finding the event IDs above, update your events using the API:

curl -X PUT http://localhost:8000/api/events/1 \\
  -H "Content-Type: application/json" \\
  -d '{
    "stubhub_event_id": "YOUR_STUBHUB_ID",
    "seatgeek_event_id": "YOUR_SEATGEEK_ID",
    "vividseats_event_id": "YOUR_VIVIDSEATS_ID"
  }'

Or directly in the database:

UPDATE events SET
  stubhub_event_id = 'YOUR_ID',
  seatgeek_event_id = 'YOUR_ID',
  vividseats_event_id = 'YOUR_ID'
WHERE id = 1;
""")


if __name__ == "__main__":
    asyncio.run(main())
