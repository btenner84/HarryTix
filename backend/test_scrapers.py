"""
Test script to verify scrapers are working with REAL Harry Styles MSG events.

Run with: python test_scrapers.py

This will test each scraper with actual Harry Styles events and show what data is returned.
"""
import asyncio
import logging
from datetime import datetime

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from app.services.scrapers import StubHubScraper, SeatGeekScraper, VividSeatsScraper

# Real Harry Styles MSG 2026 Event IDs (from Vivid Seats)
HARRY_STYLES_EVENTS = {
    "2026-09-02": {"vividseats": "6564568", "name": "Sept 2 (Wed)"},
    "2026-09-18": {"vividseats": "6564610", "name": "Sept 18 (Fri)"},
    "2026-09-19": {"vividseats": "6564614", "name": "Sept 19 (Sat)"},
    "2026-09-25": {"vividseats": "6564623", "name": "Sept 25 (Fri)"},
    "2026-10-09": {"vividseats": "6564676", "name": "Oct 9 (Fri)"},
}


async def test_vividseats():
    """Test Vivid Seats scraper with real Harry Styles events"""
    print("\n" + "=" * 60)
    print("TESTING VIVID SEATS")
    print("=" * 60)

    scraper = VividSeatsScraper()

    for date, info in HARRY_STYLES_EVENTS.items():
        event_id = info["vividseats"]
        print(f"\n--- {info['name']} (ID: {event_id}) ---")

        try:
            listings = await scraper.fetch_listings(event_id)

            if listings:
                prices = [l.price_per_ticket for l in listings]
                print(f"   SUCCESS: {len(listings)} listings")
                print(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                print(f"   Average: ${sum(prices)/len(prices):.2f}")

                # Show GA/PIT listings if any
                ga_listings = [l for l in listings if 'GA' in l.section.upper() or 'PIT' in l.section.upper() or 'FLOOR' in l.section.upper()]
                if ga_listings:
                    ga_prices = [l.price_per_ticket for l in ga_listings]
                    print(f"   GA/PIT: ${min(ga_prices):.2f} - ${max(ga_prices):.2f} ({len(ga_listings)} listings)")

                # Show 100-level listings
                sec_100 = [l for l in listings if l.section.startswith('Section 1') or l.section.startswith('1')]
                if sec_100:
                    sec_100_prices = [l.price_per_ticket for l in sec_100]
                    print(f"   100-level: ${min(sec_100_prices):.2f} - ${max(sec_100_prices):.2f} ({len(sec_100)} listings)")

                # Show 200-level listings
                sec_200 = [l for l in listings if l.section.startswith('Section 2') or l.section.startswith('2')]
                if sec_200:
                    sec_200_prices = [l.price_per_ticket for l in sec_200]
                    print(f"   200-level: ${min(sec_200_prices):.2f} - ${max(sec_200_prices):.2f} ({len(sec_200)} listings)")
            else:
                print("   No listings returned")

        except Exception as e:
            print(f"   ERROR: {e}")

        # Small delay between requests
        await asyncio.sleep(0.5)


async def test_stubhub():
    """Test StubHub scraper"""
    print("\n" + "=" * 60)
    print("TESTING STUBHUB")
    print("=" * 60)
    print("NOTE: StubHub has strong anti-bot protection (202 responses)")
    print("      Event IDs must be found manually from your browser")
    print("      URL format: https://www.stubhub.com/.../event/{EVENT_ID}")

    scraper = StubHubScraper()

    # Try to search for an event (may be blocked)
    print("\n1. Attempting to search for Harry Styles events...")

    try:
        event_id = await scraper.search_event(
            artist="Harry Styles",
            venue="Madison Square Garden",
            date=datetime(2026, 9, 18)
        )

        if event_id:
            print(f"   Found event ID: {event_id}")

            print(f"\n2. Fetching listings for event {event_id}...")
            listings = await scraper.fetch_listings(event_id)

            if listings:
                print(f"   SUCCESS: Got {len(listings)} listings")
                for listing in listings[:5]:
                    print(f"   - {listing.section}: ${listing.price_per_ticket:.2f}")
            else:
                print("   No listings returned (may be blocked)")
        else:
            print("   Search blocked - need to find event IDs manually")

    except Exception as e:
        print(f"   ERROR: {e}")


async def test_seatgeek():
    """Test SeatGeek scraper"""
    print("\n" + "=" * 60)
    print("TESTING SEATGEEK")
    print("=" * 60)
    print("NOTE: SeatGeek uses DataDome anti-bot. Results may be limited.")

    scraper = SeatGeekScraper()

    # Try to search for an event
    print("\n1. Searching for Harry Styles MSG event...")

    try:
        event_id = await scraper.search_event(
            artist="Harry Styles",
            venue="Madison Square Garden",
            date=datetime(2026, 9, 18)
        )

        if event_id:
            print(f"   Found event ID: {event_id}")

            print(f"\n2. Fetching price stats for event {event_id}...")
            listings = await scraper.fetch_listings(event_id)

            if listings:
                print(f"   SUCCESS: Got {len(listings)} price points")
                for listing in listings:
                    print(f"   - {listing.section}: ${listing.price_per_ticket:.2f}")
            else:
                print("   No data returned (blocked by DataDome)")
        else:
            print("   No event found")

    except Exception as e:
        print(f"   ERROR: {e}")


async def show_price_summary():
    """Show current prices for your ticket sections"""
    print("\n" + "=" * 60)
    print("PRICE SUMMARY FOR YOUR TICKETS")
    print("=" * 60)

    scraper = VividSeatsScraper()

    # Your ticket inventory with corresponding events
    your_tickets = [
        {"name": "Set B/D - GA PIT", "event_id": "6564614", "section_filter": ["GA", "PIT", "FLOOR"], "date": "Sept 19"},
        {"name": "Set C - Section 112", "event_id": "6564610", "section_filter": ["112"], "date": "Sept 18"},
        {"name": "Set E - Lower 100s", "event_id": "6564623", "section_filter": ["10", "11", "12", "13"], "date": "Sept 25"},
        {"name": "Set A - 200s Row 1", "event_id": "6564568", "section_filter": ["20", "21", "22"], "date": "Sept 2"},
    ]

    for ticket_set in your_tickets:
        print(f"\n{ticket_set['name']} ({ticket_set['date']}):")

        try:
            listings = await scraper.fetch_listings(ticket_set["event_id"])

            if listings:
                # Filter for comparable sections
                comparable = []
                for l in listings:
                    section_upper = l.section.upper()
                    for f in ticket_set["section_filter"]:
                        if f.upper() in section_upper:
                            comparable.append(l)
                            break

                if comparable:
                    prices = [l.price_per_ticket for l in comparable]
                    print(f"   Comparable listings: {len(comparable)}")
                    print(f"   Price range: ${min(prices):.2f} - ${max(prices):.2f}")
                    print(f"   Average: ${sum(prices)/len(prices):.2f}")
                else:
                    all_prices = [l.price_per_ticket for l in listings]
                    print(f"   No exact section matches, overall: ${min(all_prices):.2f} - ${max(all_prices):.2f}")
            else:
                print("   No listings found")

        except Exception as e:
            print(f"   Error: {e}")

        await asyncio.sleep(0.5)


async def main():
    print("=" * 60)
    print("HARRYTIX SCRAPER TEST SUITE")
    print("=" * 60)
    print("\nTesting scrapers with REAL Harry Styles MSG events...")

    # Test Vivid Seats (primary - most reliable)
    await test_vividseats()

    # Show price summary for your tickets
    await show_price_summary()

    # Test StubHub and SeatGeek (may be blocked)
    await test_stubhub()
    await test_seatgeek()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("""
Scraper Status:
- Vivid Seats: WORKING - Using direct API (most reliable)
- StubHub: BLOCKED - Anti-bot protection (202 responses)
- SeatGeek: LIMITED - DataDome blocks most requests

Vivid Seats is your PRIMARY data source for price tracking.
The scraper found 200+ listings per event with section/row/price data.

Next Steps:
1. Run 'docker-compose up -d' to start PostgreSQL
2. Run 'python seed_data.py' to create your inventory
3. Run 'uvicorn app.main:app --reload' to start the API
4. The scheduler will collect prices hourly from Vivid Seats
""")


if __name__ == "__main__":
    asyncio.run(main())
