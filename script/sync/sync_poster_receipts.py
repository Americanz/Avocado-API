#!/usr/bin/env python3
"""
Manual script to sync receipts from Poster API to Telegram bot database
Run this script to fetch and sync transaction data with bonus calculations
"""

import asyncio
import logging

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.features.telegram_bot.poster.poster_service import get_poster_service
from src.config.settings import settings

# from telegram_bot.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("poster_receipts_sync")


async def sync_receipts(days_back: int = 7, interactive: bool = False):
    """Sync receipts from Poster API for the specified number of days"""

    total_start = time.time()  # Track total execution time

    try:
        # settings = get_settings()

        # Check if Poster is configured
        if not settings.POSTER_API_TOKEN or not settings.POSTER_ACCOUNT_NAME:
            logger.error(
                "Poster API not configured. Please set POSTER_API_TOKEN and POSTER_ACCOUNT_NAME in environment"
            )
            return

        # Interactive date selection
        if interactive:
            print("\n📅 Виберіть період для синхронізації:")
            print("1. Останні дні (введіть кількість)")
            print("2. Конкретний період (введіть дати)")
            print("3. Весь серпень 2025 (за замовчуванням)")
            print("4. Сьогодні")

            choice = input("\nВаш вибір (1-4): ").strip()

            if choice == "1":
                try:
                    days_back = int(input("Введіть кількість днів назад: "))
                    date_to = datetime.now()
                    date_from = datetime.now() - timedelta(days=days_back)
                    date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
                    print(f"📊 Синхронізація за останні {days_back} днів")
                except ValueError:
                    print("❌ Неправильне число, використовуємо за замовчуванням")
                    date_from = datetime(2025, 8, 1)
                    date_to = datetime(2025, 8, 31, 23, 59, 59)

            elif choice == "2":
                try:
                    date_from_str = input("Введіть дату початку (YYYY-MM-DD): ")
                    date_to_str = input("Введіть дату кінця (YYYY-MM-DD): ")

                    date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
                    date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
                    date_to = date_to.replace(hour=23, minute=59, second=59)

                    print(f"📊 Синхронізація з {date_from_str} по {date_to_str}")
                except ValueError:
                    print("❌ Неправильний формат дати, використовуємо за замовчуванням")
                    date_from = datetime(2025, 8, 1)
                    date_to = datetime(2025, 8, 31, 23, 59, 59)
            
            elif choice == "4":
                # Today's transactions
                today = datetime.now()
                date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = today.replace(hour=23, minute=59, second=59, microsecond=999999)
                print(f"📊 Синхронізація за сьогодні ({today.strftime('%Y-%m-%d')})")
            
            else:
                # Default: August 2025
                date_from = datetime(2025, 8, 1)
                date_to = datetime(2025, 8, 31, 23, 59, 59)
                print("📊 Синхронізація серпня 2025")
        else:
            if days_back > 0:
                # Use days_back parameter
                date_to = datetime.now()
                date_from = datetime.now() - timedelta(days=days_back)
                date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
            elif days_back == 0:
                # Today only
                today = datetime.now()
                date_from = today.replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                # Default: August 2025
                date_from = datetime(2025, 8, 1)
                date_to = datetime(2025, 8, 31, 23, 59, 59)

        logger.info(f"Starting receipt sync for last {days_back} days...")

        # Get Poster service
        poster_service = await get_poster_service()
        if not poster_service:
            logger.error("Failed to initialize Poster service")
            return

        logger.info(
            f"Fetching transactions from {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}"
        )

        # Performance tracking
        api_start = time.time()

        # Stream processing with immediate batch writes (no memory accumulation)
        page = 1
        per_page = 1000  # Max allowed by API
        sync_products = True  # Set to False to skip product sync for faster processing
        total_processed = 0

        # Aggregate stats across all batches
        stats = {"created": 0, "updated": 0, "errors": 0}

        logger.info(
            "Starting streaming transaction sync (processing batches immediately)..."
        )

        while True:
            logger.info(f"Fetching page {page} (up to {per_page} transactions)...")
            transactions = await poster_service.get_transactions(
                date_from, date_to, page=page, per_page=per_page
            )

            if not transactions:
                logger.info(
                    f"No more transactions found. Total pages processed: {page - 1}"
                )
                break

            logger.info(f"Got {len(transactions)} transactions from page {page}")

            # Immediately sync this batch to database (no memory accumulation)
            batch_start = time.time()
            logger.info(
                f"Syncing page {page} ({len(transactions)} transactions) to database..."
            )

            batch_stats = poster_service.sync_transactions_to_db(
                transactions, sync_products=sync_products
            )
            batch_time = time.time() - batch_start

            # Aggregate stats
            stats["created"] += batch_stats.get("created", 0)
            stats["updated"] += batch_stats.get("updated", 0)
            stats["errors"] += batch_stats.get("errors", 0)

            total_processed += len(transactions)

            logger.info(
                f"Page {page} synced in {batch_time:.2f}s - Total processed: {total_processed}"
            )
            logger.info(
                f"Stats so far - Created: {stats['created']}, Updated: {stats['updated']}, Errors: {stats['errors']}"
            )

            # If we got less than per_page transactions, this is the last page
            if len(transactions) < per_page:
                logger.info(f"Last page reached (got {len(transactions)} transactions)")
                break

            page += 1

        if total_processed == 0:
            logger.info("No transactions found for the specified period")
            return

        logger.info(
            f"Streaming sync completed! Total processed: {total_processed} transactions"
        )
        api_time = time.time() - api_start

        # No additional sync needed - already done for each page
        sync_start = time.time()
        sync_time = 0  # Already synced during API calls
        total_time = time.time() - total_start

        # Log results
        start_time = datetime.now()  # For compatibility with existing log_sync_result
        poster_service.log_sync_result(
            "manual_receipts_sync",
            "success" if stats["errors"] == 0 else "partial",
            {
                **stats,
                "start_time": start_time,
                "api_time": api_time,
                "sync_time": sync_time,
                "total_time": total_time,
                "total_transactions": total_processed,
            },
        )

        # Print summary with performance metrics
        print("\n" + "=" * 60)
        print("OPTIMIZED SYNC COMPLETED")
        print("=" * 60)
        print(f"📊 PERFORMANCE METRICS:")
        print(f"   API calls time: {api_time:.2f}s")
        print(f"   Database sync time: {sync_time:.2f}s")
        print(f"   Total time: {total_time:.2f}s")
        if total_processed > 0 and total_time > 0:
            print(f"   Transactions per second: {total_processed/total_time:.1f}")
        print()
        print(f"📈 SYNC RESULTS:")
        print(f"   Total transactions: {total_processed}")
        print(
            f"   Processed: {stats.get('processed', stats['created'] + stats['updated'])}"
        )
        print(f"   Created: {stats['created']} new records")
        print(f"   Updated: {stats['updated']} existing records")
        print(f"   Products synced: {stats.get('products_synced', 0)}")
        print(f"   Errors: {stats['errors']}")
        print("=" * 60)

        if stats["errors"] > 0:
            print(f"⚠️  Some transactions failed to process. Check logs for details.")
        else:
            print("✅ All transactions processed successfully!")

        # Sync clients with incremental approach
        logger.info("Starting incremental client sync...")

        # Get last client_id from database as starting offset
        last_client_id = poster_service.get_last_client_id()
        offset = last_client_id if last_client_id else 0

        logger.info(f"Using offset={offset} for incremental client sync")

        # Fetch clients incrementally (1000 at a time)
        batch_size = 1000
        total_synced = 0

        while True:
            clients = await poster_service.get_clients(
                offset=offset, num=batch_size, order_by="id", sort="asc"
            )

            if not clients:
                logger.info("No more clients to sync")
                break

            logger.info(f"Processing batch of {len(clients)} clients (offset={offset})")
            client_stats = poster_service.sync_clients_to_db(clients)
            total_synced += client_stats.get("processed", 0)

            logger.info(f"Batch sync completed: {client_stats}")

            # If we got less than batch_size, we're done
            if len(clients) < batch_size:
                logger.info("Reached end of client data")
                break

            # Move offset forward
            offset += len(clients)

        logger.info(
            f"Incremental client sync completed. Total processed: {total_synced} clients"
        )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        print(f"\n❌ Sync failed: {e}")


async def main():
    """Main function"""
    import sys

    days_back = 7
    interactive = False

    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg in ['-i', '--interactive', 'interactive']:
            interactive = True
            print("🔄 Запуск інтерактивного режиму...")
        else:
            try:
                days_back = int(sys.argv[1])
                print(f"🔄 Starting Poster receipts sync for last {days_back} days...")
            except ValueError:
                print("Usage:")
                print("  python sync_poster_receipts.py [days_back]")
                print("  python sync_poster_receipts.py --interactive")
                print("")
                print("Examples:")
                print("  python sync_poster_receipts.py 30          # Last 30 days")
                print("  python sync_poster_receipts.py -i          # Interactive mode")
                print("  python sync_poster_receipts.py             # Default (August 2025)")
                return
    else:
        # No arguments - show menu
        print("\n🔄 Poster Receipts Sync")
        print("=" * 40)
        print("Виберіть режим:")
        print("1. Швидкий запуск (серпень 2025)")
        print("2. Інтерактивний вибір періоду")
        print("3. Сьогодні")

        choice = input("\nВаш вибір (1-3, Enter = 1): ").strip()

        if choice == "2":
            interactive = True
        elif choice == "3":
            # Today's sync
            days_back = 0  # Will trigger today's sync in logic above
            today = datetime.now()
            print(f"🔄 Запуск синхронізації за сьогодні ({today.strftime('%Y-%m-%d')})...")

    await sync_receipts(days_back, interactive)


if __name__ == "__main__":
    asyncio.run(main())
