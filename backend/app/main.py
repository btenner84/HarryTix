from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import events, inventory, listings, analytics, comparison
from app.jobs.scheduler import start_scheduler, shutdown_scheduler
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database tables and seed data if needed."""
    from app.database import engine, Base, async_session_maker
    from app.models import Event, Inventory
    from sqlalchemy import select
    from datetime import datetime
    from decimal import Decimal

    logger.info("Initializing database...")

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")

    # Check if already seeded
    async with async_session_maker() as session:
        result = await session.execute(select(Event))
        if result.scalars().first():
            logger.info("Database already seeded")
            return

        logger.info("Seeding database with Harry Styles events...")

        # Events data
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

        # Inventory data (27 tickets)
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
             "quantity": 4, "cost_per_ticket": Decimal("368.00"), "notes": "Set E - 4 solo tickets"},
        ]

        for inv in inventory_data:
            item = Inventory(event_id=events[inv["event_idx"]].id, section=inv["section"],
                           row=inv["row"], seat_numbers=inv["seat_numbers"], quantity=inv["quantity"],
                           cost_per_ticket=inv["cost_per_ticket"],
                           total_cost=inv["cost_per_ticket"] * inv["quantity"], notes=inv["notes"])
            session.add(item)

        await session.commit()
        logger.info(f"Database seeded: {len(events)} events, {len(inventory_data)} inventory items")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting HarryTix API...")
    try:
        await init_database()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down HarryTix API...")
    shutdown_scheduler()


app = FastAPI(
    title="HarryTix Price Tracker",
    description="Track ticket prices for Harry Styles concerts across resale platforms",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(comparison.router, prefix="/api/comparison", tags=["comparison"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "harrytix"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HarryTix Price Tracker API",
        "docs": "/docs",
        "health": "/health",
    }
