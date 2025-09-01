#!/usr/bin/env python3
"""
Sync Poster transactions for the current month
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from src.config.settings import settings
from src.features.telegram_bot.poster.service import PosterAPIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "logs/application_" + datetime.now().strftime("%Y-%m-%d") + ".log"
        ),
    ],
)

logger = logging.getLogger("poster_monthly_sync")


async def get_poster_service() -> PosterAPIService:
    """Get configured Poster service"""
    api_token = os.getenv("POSTER_API_TOKEN")
    account_name = os.getenv("POSTER_ACCOUNT_NAME")

    if not api_token or not account_name:
        return None

    return PosterAPIService(api_token, account_name)


async def sync_month_transactions():
    """Main function to sync Poster transactions for current month"""
    print("🔄 Starting Poster transactions sync for current month...")

    try:
        # Check if Poster API is configured
        if not os.getenv("POSTER_API_TOKEN") or not os.getenv("POSTER_ACCOUNT_NAME"):
            logger.error(
                "Poster API not configured. Please set POSTER_API_TOKEN and POSTER_ACCOUNT_NAME in environment"
            )
            return

        logger.info("Starting monthly transactions sync...")

        # Get Poster service
        poster_service = await get_poster_service()
        if not poster_service:
            logger.error("Failed to initialize Poster service")
            return

        # Calculate date range for current month (August 2025)
        date_to = datetime.now()
        date_from = datetime(2025, 8, 1)  # August 1st, 2025

        logger.info(
            f"Fetching transactions from {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}"
        )

        # Get ALL transactions from Poster API with pagination
        all_transactions = []
        page = 1
        start_time = datetime.now()

        while True:
            logger.info(f"Fetching page {page}...")
            transactions = await poster_service.get_transactions(
                date_from, date_to, page=page
            )

            if not transactions:
                logger.info(f"No more transactions found on page {page}")
                break

            all_transactions.extend(transactions)
            logger.info(
                f"Got {len(transactions)} transactions from page {page}, total: {len(all_transactions)}"
            )

            # If we got less than expected (usually 100), this is the last page
            if len(transactions) < 100:
                break

            page += 1

        if not all_transactions:
            logger.info("No transactions found for the specified period")
            return

        logger.info(f"Found {len(all_transactions)} total transactions to process")

        # Sync to database
        stats = poster_service.sync_transactions_to_db(all_transactions)

        # Log results
        poster_service.log_sync_result(
            "monthly_transactions_sync",
            "success" if stats["errors"] == 0 else "partial",
            {**stats, "start_time": start_time},
        )

        # Print summary
        print("\n" + "=" * 60)
        print("MONTHLY TRANSACTIONS SYNC COMPLETED")
        print("=" * 60)
        print(
            f"Period: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}"
        )
        print(f"Processed: {stats['processed']} transactions")
        print(f"Created: {stats['created']} new records")
        print(f"Updated: {stats['updated']} existing records")
        print(f"Bonuses processed: {stats['bonuses_processed']} transactions")
        print(f"Errors: {stats['errors']}")
        print("=" * 60)

        if stats["errors"] == 0:
            print("✅ All transactions processed successfully!")
        else:
            print(f"⚠️ {stats['errors']} transactions had errors during processing")

        # Show sync time
        sync_duration = datetime.now() - start_time
        print(f"⏱️ Sync completed in {sync_duration}")

    except Exception as e:
        logger.error(f"Error during monthly sync: {e}")
        print(f"❌ Error during sync: {e}")


if __name__ == "__main__":
    asyncio.run(sync_month_transactions())
