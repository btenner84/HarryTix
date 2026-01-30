import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HarryTix Price Tracker",
    description="Track ticket prices for Harry Styles concerts",
    version="1.0.0",
)

# Parse ALLOWED_ORIGINS from env
def get_allowed_origins():
    origins_str = os.environ.get("ALLOWED_ORIGINS", '["*"]')
    if origins_str.startswith("["):
        import json
        try:
            return json.loads(origins_str)
        except:
            pass
    return origins_str.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "harrytix"}


@app.get("/")
def root():
    return {"message": "HarryTix API", "docs": "/docs"}


@app.on_event("startup")
async def startup():
    """Initialize database and routes on startup"""
    logger.info("Starting HarryTix API...")

    try:
        # Import and init database (config.py handles DATABASE_URL conversion)
        from app.database import engine, Base, async_session_maker
        from app.models import Event, Inventory
        from sqlalchemy import select
        from datetime import datetime
        from decimal import Decimal

        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ready")

        # Seed if empty
        async with async_session_maker() as session:
            result = await session.execute(select(Event))
            if not result.scalars().first():
                logger.info("Seeding database...")
                events_data = [
                    {"name": "Harry Styles - Love On Tour", "venue": "Madison Square Garden",
                     "date": datetime(2026, 9, 2, 20, 0), "vividseats_id": "6564568", "stubhub_id": "160334450"},
                    {"name": "Harry Styles - Love On Tour", "venue": "Madison Square Garden",
                     "date": datetime(2026, 9, 18, 20, 0), "vividseats_id": "6564610", "stubhub_id": "160334461"},
                    {"name": "Harry Styles - Love On Tour", "venue": "Madison Square Garden",
                     "date": datetime(2026, 9, 19, 20, 0), "vividseats_id": "6564614", "stubhub_id": "160334462"},
                    {"name": "Harry Styles - Love On Tour", "venue": "Madison Square Garden",
                     "date": datetime(2026, 9, 25, 20, 0), "vividseats_id": "6564623", "stubhub_id": "160334464"},
                    {"name": "Harry Styles - Love On Tour", "venue": "Madison Square Garden",
                     "date": datetime(2026, 10, 9, 20, 0), "vividseats_id": "6564676", "stubhub_id": "160334466"},
                ]
                events = []
                for evt in events_data:
                    event = Event(name=evt["name"], venue=evt["venue"], event_date=evt["date"],
                                 stubhub_event_id=evt["stubhub_id"], vividseats_event_id=evt["vividseats_id"])
                    session.add(event)
                    events.append(event)
                await session.flush()

                inventory_data = [
                    {"event_idx": 0, "section": "Section 200s Row 1", "row": "1", "seat_numbers": "7-10",
                     "quantity": 4, "cost_per_ticket": Decimal("471.25"), "notes": "Set A"},
                    {"event_idx": 2, "section": "Left GA", "row": "GA", "seat_numbers": None,
                     "quantity": 6, "cost_per_ticket": Decimal("490.67"), "notes": "Set B"},
                    {"event_idx": 1, "section": "Section 112", "row": None, "seat_numbers": "11-18",
                     "quantity": 8, "cost_per_ticket": Decimal("324.88"), "notes": "Set C"},
                    {"event_idx": 4, "section": "Left GA", "row": "GA", "seat_numbers": None,
                     "quantity": 5, "cost_per_ticket": Decimal("433.20"), "notes": "Set D"},
                    {"event_idx": 3, "section": "Section 100s", "row": None, "seat_numbers": None,
                     "quantity": 4, "cost_per_ticket": Decimal("368.00"), "notes": "Set E"},
                ]
                for inv in inventory_data:
                    item = Inventory(event_id=events[inv["event_idx"]].id, section=inv["section"],
                                   row=inv["row"], seat_numbers=inv["seat_numbers"], quantity=inv["quantity"],
                                   cost_per_ticket=inv["cost_per_ticket"],
                                   total_cost=inv["cost_per_ticket"] * inv["quantity"], notes=inv["notes"])
                    session.add(item)
                await session.commit()
                logger.info("Database seeded with 5 events and 27 tickets!")
            else:
                logger.info("Database already seeded")

        # Register routes
        from app.api.routes import comparison
        app.include_router(comparison.router, prefix="/api", tags=["comparison"])
        logger.info("Routes registered")

    except Exception as e:
        logger.error(f"Startup error: {e}")
        import traceback
        traceback.print_exc()
