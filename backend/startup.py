#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Creates database tables and seeds initial data if needed.
"""
import asyncio
import os
import sys
import traceback

print("=== STARTUP SCRIPT STARTING ===", flush=True)
print(f"DATABASE_URL env: {os.environ.get('DATABASE_URL', 'NOT SET')[:50]}...", flush=True)
print(f"ALLOWED_ORIGINS env: {os.environ.get('ALLOWED_ORIGINS', 'NOT SET')}", flush=True)

async def init_database():
    """Initialize database tables and seed data."""
    from app.database import engine, Base, async_session_maker
    from app.models import Event, Inventory
    from sqlalchemy import select, text
    from datetime import datetime
    from decimal import Decimal

    print("Initializing database...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully")

    # Check if already seeded
    async with async_session_maker() as session:
        result = await session.execute(select(Event))
        if result.scalars().first():
            print("Database already seeded - skipping")
            return

        print("Seeding database with Harry Styles events...")

        # Events data
        events_data = [
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 9, 2, 20, 0),
                "vividseats_id": "6564568",
                "stubhub_id": "160334450",
            },
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 9, 18, 20, 0),
                "vividseats_id": "6564610",
                "stubhub_id": "160334461",
            },
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 9, 19, 20, 0),
                "vividseats_id": "6564614",
                "stubhub_id": "160334462",
            },
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 9, 25, 20, 0),
                "vividseats_id": "6564623",
                "stubhub_id": "160334464",
            },
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 10, 9, 20, 0),
                "vividseats_id": "6564676",
                "stubhub_id": "160334466",
            },
            {
                "name": "Harry Styles - Love On Tour",
                "venue": "Madison Square Garden",
                "date": datetime(2026, 10, 17, 20, 0),
                "vividseats_id": "6564691",
                "stubhub_id": "160334468",
            },
        ]

        events = []
        for evt in events_data:
            event = Event(
                name=evt["name"],
                venue=evt["venue"],
                event_date=evt["date"],
                stubhub_event_id=evt["stubhub_id"],
                vividseats_event_id=evt["vividseats_id"],
            )
            session.add(event)
            events.append(event)

        await session.flush()

        # Inventory data (your 27 tickets)
        inventory_data = [
            # Set A: Sept 2 - Sec 200s Row 1 - 4 tickets
            {
                "event_idx": 0,
                "section": "Section 200s Row 1",
                "row": "1",
                "seat_numbers": "7-10",
                "quantity": 4,
                "cost_per_ticket": Decimal("471.25"),
                "notes": "Set A",
            },
            # Set B: Sept 19 - Left GA - 6 tickets
            {
                "event_idx": 2,
                "section": "Left GA",
                "row": "GA",
                "seat_numbers": None,
                "quantity": 6,
                "cost_per_ticket": Decimal("490.67"),
                "notes": "Set B",
            },
            # Set C: Sept 18 - Sec 112 - 8 tickets
            {
                "event_idx": 1,
                "section": "Section 112",
                "row": None,
                "seat_numbers": "11-18",
                "quantity": 8,
                "cost_per_ticket": Decimal("324.88"),
                "notes": "Set C",
            },
            # Set D: Oct 9 - Left GA - 5 tickets
            {
                "event_idx": 4,
                "section": "Left GA",
                "row": "GA",
                "seat_numbers": None,
                "quantity": 5,
                "cost_per_ticket": Decimal("433.20"),
                "notes": "Set D",
            },
            # Set E: Sept 25 - 100s solos - 4 tickets
            {
                "event_idx": 3,
                "section": "Section 100s",
                "row": None,
                "seat_numbers": None,
                "quantity": 4,
                "cost_per_ticket": Decimal("368.00"),
                "notes": "Set E - 4 solo tickets",
            },
            # Set F: Oct 17 - Section 109 Row 4 - 1 ticket
            {
                "event_idx": 5,
                "section": "Section 109",
                "row": "4",
                "seat_numbers": "7",
                "quantity": 1,
                "cost_per_ticket": Decimal("368.00"),
                "notes": "Set F - single ticket",
            },
            # Set G: Oct 17 - GA Pit - 5 tickets
            {
                "event_idx": 5,
                "section": "GA Pit",
                "row": "GA",
                "seat_numbers": None,
                "quantity": 5,
                "cost_per_ticket": Decimal("433.20"),
                "notes": "Set G - GA Pit",
            },
            # Set H: Oct 17 - Section 114 Row 21 - 2 tickets
            {
                "event_idx": 5,
                "section": "Section 114",
                "row": "21",
                "seat_numbers": "21-22",
                "quantity": 2,
                "cost_per_ticket": Decimal("368.00"),
                "notes": "Set H - pair",
            },
        ]

        for inv in inventory_data:
            item = Inventory(
                event_id=events[inv["event_idx"]].id,
                section=inv["section"],
                row=inv["row"],
                seat_numbers=inv["seat_numbers"],
                quantity=inv["quantity"],
                cost_per_ticket=inv["cost_per_ticket"],
                total_cost=inv["cost_per_ticket"] * inv["quantity"],
                notes=inv["notes"],
            )
            session.add(item)

        await session.commit()
        print("Database seeded successfully!")
        print(f"  - {len(events)} events")
        print(f"  - {len(inventory_data)} inventory items (35 tickets)")


if __name__ == "__main__":
    try:
        asyncio.run(init_database())
        print("=== STARTUP SCRIPT COMPLETED SUCCESSFULLY ===", flush=True)
    except Exception as e:
        print(f"=== STARTUP SCRIPT FAILED ===", flush=True)
        print(f"Error: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
