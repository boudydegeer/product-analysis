"""Background task for polling analysis workflows."""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session_maker
from app.services.polling_service import AnalysisPollingService

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def poll_analyzing_features() -> None:
    """Background task to poll features in ANALYZING status.

    This runs periodically to check workflow status and download results
    for features that haven't received webhook callbacks.
    """
    logger.info("Polling task: Started")

    try:
        async with async_session_maker() as db:
            polling_service = AnalysisPollingService(db)
            polled_count = await polling_service.poll_all_analyzing_features()

            logger.info(f"Polling task: Completed, processed {polled_count} features")

    except Exception as e:
        logger.error(f"Polling task: Failed with error - {e}", exc_info=True)


def start_polling_scheduler() -> AsyncIOScheduler:
    """Start the background polling scheduler.

    Returns:
        The scheduler instance
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return scheduler

    scheduler = AsyncIOScheduler()

    # Add job to poll every N seconds
    scheduler.add_job(
        poll_analyzing_features,
        trigger="interval",
        seconds=settings.analysis_polling_interval_seconds,
        id="poll_analyzing_features",
        name="Poll analyzing features for workflow results",
        replace_existing=True,
    )

    scheduler.start()

    logger.info(
        f"Started polling scheduler (interval: {settings.analysis_polling_interval_seconds}s)"
    )

    return scheduler


def stop_polling_scheduler() -> None:
    """Stop the background polling scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Stopped polling scheduler")


@asynccontextmanager
async def polling_lifespan():
    """Context manager for polling scheduler lifecycle."""
    start_polling_scheduler()
    yield
    stop_polling_scheduler()
