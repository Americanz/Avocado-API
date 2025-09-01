#!/usr/bin/env python3
"""
Sync Poster clients to database
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.features.telegram_bot.poster.poster_service import get_poster_service

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

logger = logging.getLogger("clients_sync")



async def sync_clients():
    """Main function to sync Poster clients"""
    print("🔄 Starting Poster clients sync...")

    try:
        # Check if Poster API is configured
        if not os.getenv("POSTER_API_TOKEN") or not os.getenv("POSTER_ACCOUNT_NAME"):
            logger.error(
                "Poster API not configured. Please set POSTER_API_TOKEN and POSTER_ACCOUNT_NAME in environment"
            )
            return

        logger.info("Starting Poster clients sync...")

        # Get Poster service
        poster_service = await get_poster_service()
        if not poster_service:
            logger.error("Failed to initialize Poster service")
            return

        # Get ALL clients from Poster API (num=0 means no limit)
        logger.info("Fetching all clients from Poster API...")
        clients = await poster_service.get_clients(
            offset=0, 
            num=0,  # 0 means get all clients without limit
            order_by="id", 
            sort="asc"
        )

        if not clients:
            logger.info("No clients found in Poster")
            return

        # Option to limit clients for testing (only if 'test' argument is passed)
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            clients = clients[:1000]
            logger.info(f"Test mode: limiting to first {len(clients)} clients")

        logger.info(f"Found {len(clients)} clients total to process")

        # Sync clients to database
        start_time = datetime.now()
        stats = poster_service.sync_clients_to_db(clients)

        # Log results
        poster_service.log_sync_result(
            "manual_clients_sync",
            "success" if stats["errors"] == 0 else "partial",
            {**stats, "start_time": start_time},
        )

        # Print summary
        print("\n" + "=" * 50)
        print("CLIENTS SYNC COMPLETED")
        print("=" * 50)
        print(f"Total fetched: {len(clients)} clients")
        print(f"Processed: {stats['processed']} clients")
        print(f"Created: {stats['created']} new records")
        print(f"Updated: {stats['updated']} existing records")
        print(f"Errors: {stats['errors']}")
        print("=" * 50)

        if stats["errors"] == 0:
            print("✅ All clients processed successfully!")
        else:
            print(f"⚠️ {stats['errors']} clients had errors during processing")

    except Exception as e:
        logger.error(f"Error during clients sync: {e}")
        print(f"❌ Error during sync: {e}")


if __name__ == "__main__":
    asyncio.run(sync_clients())
