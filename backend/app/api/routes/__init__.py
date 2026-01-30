from app.api.routes.events import router as events_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.listings import router as listings_router
from app.api.routes.analytics import router as analytics_router

__all__ = ["events_router", "inventory_router", "listings_router", "analytics_router"]
