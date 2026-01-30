from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    """Initialize and start the APScheduler"""
    from app.jobs.price_collector import collect_all_prices

    # Run price collection every hour at minute 0
    scheduler.add_job(
        collect_all_prices,
        trigger=CronTrigger(minute=0),  # Every hour on the hour
        id="hourly_price_collection",
        name="Collect prices from all platforms",
        replace_existing=True,
        max_instances=1,  # Prevent overlap
    )

    # Run initial collection 30 seconds after startup (to let things settle)
    from datetime import datetime, timedelta
    scheduler.add_job(
        collect_all_prices,
        trigger="date",
        run_date=datetime.now() + timedelta(seconds=30),
        id="startup_price_collection",
        name="Initial price collection on startup",
    )

    scheduler.start()
    logger.info("APScheduler started with hourly price collection")


def shutdown_scheduler():
    """Gracefully shutdown the scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shutdown complete")
