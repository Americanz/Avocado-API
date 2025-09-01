#!/usr/bin/env python3

import asyncio
import logging
from src.config.settings import settings
from src.features.telegram_bot.poster.service import PosterAPIService

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_transaction_details():
    """Test getting transaction details"""

    api_service = PosterAPIService(
        api_token=settings.POSTER_API_TOKEN, account_name=settings.POSTER_ACCOUNT_NAME
    )

    # Get a transaction ID from database
    import psycopg2

    conn = psycopg2.connect(settings.DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT transaction_id FROM transactions LIMIT 1;")
    result = cursor.fetchone()
    conn.close()

    if not result:
        logger.error("No transactions found in database")
        return

    transaction_id = result[0]
    logger.info(f"Testing transaction details for ID: {transaction_id}")

    # Get transaction details
    details = await api_service.get_transaction_details(transaction_id)

    if details:
        logger.info(f"Transaction details keys: {list(details.keys())}")
        if "products" in details:
            logger.info(f"Found {len(details['products'])} products")
            logger.info(
                f"First product sample: {details['products'][0] if details['products'] else 'None'}"
            )
        else:
            logger.warning("No 'products' key in transaction details")
            logger.info(f"Available keys: {list(details.keys())}")
    else:
        logger.error("Failed to get transaction details")


if __name__ == "__main__":
    asyncio.run(test_transaction_details())
