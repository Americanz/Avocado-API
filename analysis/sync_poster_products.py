#!/usr/bin/env python3
"""
Sync Poster products to database
"""

import asyncio
import logging
import os
from datetime import datetime
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

logger = logging.getLogger("products_sync")


async def get_poster_service() -> PosterAPIService:
    """Get configured Poster service"""
    api_token = os.getenv("POSTER_API_TOKEN")
    account_name = os.getenv("POSTER_ACCOUNT_NAME")

    if not api_token or not account_name:
        return None

    return PosterAPIService(api_token, account_name)


async def sync_poster_products():
    """Main function to sync Poster products"""
    print("🔄 Starting Poster products sync...")

    try:
        # Check if Poster API is configured
        if not os.getenv("POSTER_API_TOKEN") or not os.getenv("POSTER_ACCOUNT_NAME"):
            logger.error(
                "Poster API not configured. Please set POSTER_API_TOKEN and POSTER_ACCOUNT_NAME in environment"
            )
            return

        logger.info("Starting Poster products sync...")

        # Get Poster service
        poster_service = await get_poster_service()
        if not poster_service:
            logger.error("Failed to initialize Poster service")
            return

        # Get products from Poster API
        products = await poster_service.get_products()

        if not products:
            logger.info("No products found in Poster")
            return

        logger.info(f"Found {len(products)} products to process")

        # Sync products to database
        start_time = datetime.now()
        stats = poster_service.sync_products_to_db(products)

        # Log results
        poster_service.log_sync_result(
            "manual_products_sync",
            "success" if stats["errors"] == 0 else "partial",
            {**stats, "start_time": start_time},
        )

        # Print summary
        print("\n" + "=" * 50)
        print("PRODUCTS SYNC COMPLETED")
        print("=" * 50)
        print(f"Processed: {stats['processed']} products")
        print(f"Created: {stats['created']} new records")
        print(f"Updated: {stats['updated']} existing records")
        print(f"Errors: {stats['errors']}")
        print("=" * 50)

        if stats["errors"] == 0:
            print("✅ All products processed successfully!")
        else:
            print(f"⚠️ {stats['errors']} products had errors during processing")

    except Exception as e:
        logger.error(f"Error during products sync: {e}")
        print(f"❌ Error during sync: {e}")


if __name__ == "__main__":
    asyncio.run(sync_poster_products())
