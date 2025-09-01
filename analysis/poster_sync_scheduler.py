#!/usr/bin/env python3
"""
Scheduled Poster sync script
Can be run as a cron job or scheduled task
"""

import asyncio
import logging
from datetime import datetime, timedelta
from src.features.telegram_bot.poster.service import get_poster_service
from src.config.settings import get_settings

logger = logging.getLogger("poster_sync_scheduler")


async def run_scheduled_sync():
    """Run scheduled Poster synchronization"""
    try:
        settings = get_settings()

        if not settings.POSTER_ENABLE_AUTO_SYNC:
            logger.info("Auto sync is disabled")
            return

        logger.info("Starting scheduled Poster sync...")

        poster_service = await get_poster_service()
        if not poster_service:
            logger.error("Poster service not configured")
            return

        # Sync transactions for the last day
        date_from = datetime.now() - timedelta(days=1)
        date_to = datetime.now()

        logger.info(f"Syncing transactions from {date_from} to {date_to}")

        # Get transactions
        transactions = await poster_service.get_transactions(date_from, date_to)

        if transactions:
            # Enhanced sync to both Poster and Telegram tables
            start_time = datetime.utcnow()
            stats = poster_service.sync_transactions_with_telegram(transactions)

            # Log result
            poster_service.log_sync_result(
                "transactions", "success", {**stats, "start_time": start_time}
            )

            logger.info(f"Sync completed: {stats}")

            # Sync products for new transactions
            if stats["created"] > 0:
                logger.info(f"Syncing products for {stats['created']} new transactions")
                # Add product sync logic here if needed
        else:
            logger.info("No new transactions found")

    except Exception as e:
        logger.error(f"Scheduled sync failed: {e}")

        # Log the error
        if "poster_service" in locals():
            poster_service.log_sync_result(
                "transactions",
                "error",
                {
                    "start_time": datetime.utcnow(),
                    "processed": 0,
                    "errors": 1,
                    "error_message": str(e),
                },
            )


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run sync
    asyncio.run(run_scheduled_sync())
