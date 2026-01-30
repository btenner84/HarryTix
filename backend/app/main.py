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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info("Starting HarryTix API...")
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
