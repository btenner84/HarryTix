"""
Seed script to populate the database with Harry Styles events and your ticket inventory.

Run with: python seed_data.py

VIVID SEATS EVENT IDS (Verified):
- Aug 29, 2026 (Sat): 6564557
- Sept 18, 2026 (Fri): 6564610
- Sept 19, 2026 (Sat): 6564614
- Sept 25, 2026 (Fri): 6564623
- Oct 9, 2026 (Fri): 6564676
- Oct 17, 2026 (Sat): 6564691

STUBHUB EVENT IDS:
- Need to be found manually from your browser
- Go to stubhub.com, search for the event, and copy the ID from the URL
- URL format: https://www.stubhub.com/.../event/{EVENT_ID}
"""
import asyncio
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from app.database import async_session_maker, engine, Base
from app.models import Event, Inventory


# Harry Styles MSG Tour 2026 - Event IDs
EVENTS = [
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 8, 29, 20, 0),  # Sat Aug 29
        "vividseats_id": "6564557",
        "stubhub_id": "160334450",
        "seatgeek_id": None,
    },
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 9, 18, 20, 0),  # Fri Sept 18
        "vividseats_id": "6564610",
        "stubhub_id": "160334461",
        "seatgeek_id": None,
    },
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 9, 19, 20, 0),  # Sat Sept 19
        "vividseats_id": "6564614",
        "stubhub_id": "160334462",
        "seatgeek_id": None,
    },
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 9, 25, 20, 0),  # Fri Sept 25
        "vividseats_id": "6564623",
        "stubhub_id": "160334464",
        "seatgeek_id": None,
    },
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 10, 9, 20, 0),  # Fri Oct 9
        "vividseats_id": "6564676",
        "stubhub_id": "160334466",
        "seatgeek_id": None,
    },
    {
        "name": "Harry Styles - Love On Tour",
        "venue": "Madison Square Garden",
        "date": datetime(2026, 10, 17, 20, 0),  # Sat Oct 17
        "vividseats_id": "6564691",
        "stubhub_id": "160334468",  # StubHub disabled
        "seatgeek_id": None,
    },
]


async def seed_database():
    """Seed the database with events and inventory"""

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # Check if already seeded
        result = await session.execute(select(Event))
        if result.scalars().first():
            print("Database already seeded! Run 'python reset_db.py' first to reseed.")
            return

        # Create events
        events = []
        for evt in EVENTS:
            event = Event(
                name=evt["name"],
                venue=evt["venue"],
                event_date=evt["date"],
                stubhub_event_id=evt["stubhub_id"],
                seatgeek_event_id=evt["seatgeek_id"],
                vividseats_event_id=evt["vividseats_id"],
            )
            session.add(event)
            events.append(event)

        await session.flush()  # Get IDs

        # Your ticket inventory (27 tickets across 5 sets)
        inventory_items = [
            # Set A: Sat Aug 29 - Sec 200s Row 1 (Seats 7-10) - 4 tickets - $1,885 total
            Inventory(
                event_id=events[0].id,
                section="Section 200s",
                row="1",
                seat_numbers="7-10",
                quantity=4,
                cost_per_ticket=Decimal("471.25"),
                total_cost=Decimal("1885.00"),
                target_sell_min=Decimal("800.00"),
                target_sell_max=Decimal("1400.00"),
                notes="Set A - Aug/Sept show",
            ),
            # Set B: Sat Sept 19 - Left GA - 6 tickets - $2,944 total
            Inventory(
                event_id=events[2].id,  # Sept 19
                section="Left GA",
                row="GA",
                seat_numbers=None,
                quantity=6,
                cost_per_ticket=Decimal("490.67"),
                total_cost=Decimal("2944.00"),
                target_sell_min=Decimal("800.00"),
                target_sell_max=Decimal("1300.00"),
                notes="Set B",
            ),
            # Set C: Fri Sept 18 - Sec 112 Seats 11-18 - 8 tickets - $2,599 total
            Inventory(
                event_id=events[1].id,  # Sept 18
                section="Section 112",
                row=None,
                seat_numbers="11-18",
                quantity=8,
                cost_per_ticket=Decimal("324.88"),
                total_cost=Decimal("2599.00"),
                target_sell_min=Decimal("700.00"),
                target_sell_max=Decimal("1200.00"),
                notes="Set C",
            ),
            # Set D: Fri Oct 9 - Left GA - 5 tickets - $2,166 total
            Inventory(
                event_id=events[4].id,  # Oct 9
                section="Left GA",
                row="GA",
                seat_numbers=None,
                quantity=5,
                cost_per_ticket=Decimal("433.20"),
                total_cost=Decimal("2166.00"),
                target_sell_min=Decimal("800.00"),
                target_sell_max=Decimal("1350.00"),
                notes="Set D",
            ),
            # Set E: Fri Sept 25 - Lower Bowl 100s (4 solos) - 4 tickets - $1,472 total
            Inventory(
                event_id=events[3].id,  # Sept 25
                section="Section 100s",
                row=None,
                seat_numbers=None,
                quantity=4,
                cost_per_ticket=Decimal("368.00"),
                total_cost=Decimal("1472.00"),
                target_sell_min=Decimal("750.00"),
                target_sell_max=Decimal("1300.00"),
                notes="Set E - 4 solo tickets",
            ),
            # Set F: Sat Oct 17 - Section 109 Row 4 Seat 7 - 1 ticket - $368 total
            Inventory(
                event_id=events[5].id,  # Oct 17
                section="Section 109",
                row="4",
                seat_numbers="7",
                quantity=1,
                cost_per_ticket=Decimal("368.00"),
                total_cost=Decimal("368.00"),
                target_sell_min=Decimal("750.00"),
                target_sell_max=Decimal("1300.00"),
                notes="Set F - single ticket",
            ),
            # Set G: Sat Oct 17 - GA Pit - 5 tickets - $2,166 total
            Inventory(
                event_id=events[5].id,  # Oct 17
                section="GA Pit",
                row="GA",
                seat_numbers=None,
                quantity=5,
                cost_per_ticket=Decimal("433.20"),
                total_cost=Decimal("2166.00"),
                target_sell_min=Decimal("800.00"),
                target_sell_max=Decimal("1350.00"),
                notes="Set G - GA Pit",
            ),
            # Set H: Sat Oct 17 - Section 114 Row 21 Seats 21-22 - 2 tickets - $736 total
            Inventory(
                event_id=events[5].id,  # Oct 17
                section="Section 114",
                row="21",
                seat_numbers="21-22",
                quantity=2,
                cost_per_ticket=Decimal("368.00"),
                total_cost=Decimal("736.00"),
                target_sell_min=Decimal("750.00"),
                target_sell_max=Decimal("1300.00"),
                notes="Set H - pair",
            ),
        ]

        for item in inventory_items:
            session.add(item)

        await session.commit()

        print("Database seeded successfully!")
        print(f"Created {len(events)} events")
        print(f"Created {len(inventory_items)} inventory items (35 total tickets)")
        print("\n=== YOUR INVENTORY ===")
        print("Set A: 4 tickets - Section 200s Row 1 - Aug 29 (Sat)")
        print("Set B: 6 tickets - GA/PIT - Sept 19 (Sat)")
        print("Set C: 8 tickets - Section 112 - Sept 18 (Fri)")
        print("Set D: 5 tickets - GA/PIT - Oct 9 (Fri)")
        print("Set E: 4 tickets - Lower 100s - Sept 25 (Fri)")
        print("Set F: 1 ticket - Section 109 Row 4 - Oct 17 (Sat)")
        print("Set G: 5 tickets - GA Pit - Oct 17 (Sat)")
        print("Set H: 2 tickets - Section 114 Row 21 - Oct 17 (Sat)")
        print("\nTotal: 35 tickets | Total Cost: $14,336")


if __name__ == "__main__":
    asyncio.run(seed_database())
