#!/usr/bin/env python3
"""
Відновлення продуктів після видалення poster_products
"""

import asyncio
import os
import sys
import logging

from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

# Додаємо кореневу папку проекту до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("restore_products")


async def restore_products():
    """Відновлення продуктів з Poster API"""
    logger.info("🔄 Початок відновлення продуктів...")

    # Отримуємо налаштування API
    api_token = os.getenv("POSTER_API_TOKEN")
    account_name = os.getenv("POSTER_ACCOUNT_NAME")

    if not api_token or not account_name:
        logger.error(
            "❌ Не знайдено POSTER_API_TOKEN або POSTER_ACCOUNT_NAME в змінних середовища"
        )
        return

    try:
        from src.features.telegram_bot.poster.services.api_service import (
            PosterAPIService,
        )
        from src.features.telegram_bot.poster.services.product_service import (
            ProductService,
        )

        # Створюємо API сервіс
        api_service = PosterAPIService(api_token=api_token, account_name=account_name)

        # Завантажуємо продукти з API
        logger.info("📡 Завантажуємо продукти з Poster API...")
        products = await api_service.get_products()

        if not products:
            logger.warning("⚠️ Не отримано продуктів з API")
            return

        logger.info(f"📦 Отримано {len(products)} продуктів з API")

        # Створюємо product service
        product_service = ProductService(api_token=api_token, account_name=account_name)

        # Синхронізуємо з базою даних
        stats = product_service.sync_products_to_db(products)

        logger.info("✅ Синхронізація завершена:")
        logger.info(f"   📊 Оброблено: {stats.get('processed', 0)}")
        logger.info(f"   ➕ Створено: {stats.get('created', 0)}")
        logger.info(f"   🔄 Оновлено: {stats.get('updated', 0)}")

        # Перевіримо результат через AsyncSession
        from src.core.database.connection import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
            logger.info(f"🎯 Всього продуктів в БД: {count}")

    except Exception as e:
        logger.error(f"❌ Помилка при відновленні продуктів: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(restore_products())
