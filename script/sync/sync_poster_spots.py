#!/usr/bin/env python3
"""
Завантаження spots з Poster API
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

logger = logging.getLogger("restore_spots")


async def restore_spots():
    """Завантаження spots з Poster API"""
    logger.info("🏪 Початок завантаження spots...")

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

        # Створюємо API сервіс
        api_service = PosterAPIService(api_token=api_token, account_name=account_name)

        # Завантажуємо spots з API
        logger.info("📡 Завантажуємо spots з Poster API...")
        spots = await api_service.get_spots()

        if not spots:
            logger.warning("⚠️ Не отримано spots з API")
            return

        logger.info(f"🏪 Отримано {len(spots)} spots з API")

        # Тепер вставляємо їх в базу даних через SQLAlchemy
        from src.core.database.connection import AsyncSessionLocal
        from src.features.telegram_bot.models.spot import Spot

        async with AsyncSessionLocal() as session:
            spots_created = 0
            spots_updated = 0

            for spot_data in spots:
                try:
                    spot_id = spot_data.get("spot_id")
                    if not spot_id:
                        logger.warning(f"Spot без ID: {spot_data}")
                        continue

                    # Перевіряємо чи існує spot
                    from sqlalchemy import select

                    existing_spot = await session.execute(
                        select(Spot).where(Spot.spot_id == spot_id)
                    )
                    existing_spot = existing_spot.scalar_one_or_none()

                    if existing_spot:
                        # Оновлюємо існуючий spot
                        existing_spot.name = spot_data.get("name")
                        existing_spot.address = spot_data.get("address")
                        existing_spot.raw_data = spot_data
                        spots_updated += 1
                        logger.debug(f"Оновлено spot {spot_id}")
                    else:
                        # Створюємо новий spot
                        new_spot = Spot(
                            spot_id=spot_id,
                            name=spot_data.get("name"),
                            address=spot_data.get("address"),
                            raw_data=spot_data,
                        )
                        session.add(new_spot)
                        spots_created += 1
                        logger.debug(f"Створено spot {spot_id}")

                except Exception as e:
                    logger.error(
                        f"Помилка при обробці spot {spot_data.get('spot_id', 'unknown')}: {e}"
                    )
                    continue

            # Збережуємо зміни
            await session.commit()

            logger.info("✅ Синхронізація spots завершена:")
            logger.info(f"   🏪 Створено: {spots_created}")
            logger.info(f"   🔄 Оновлено: {spots_updated}")

            # Перевіримо результат
            from sqlalchemy import text

            result = await session.execute(text("SELECT COUNT(*) FROM spots"))
            count = result.scalar()
            logger.info(f"🎯 Всього spots в БД: {count}")

    except Exception as e:
        logger.error(f"❌ Помилка при завантаженні spots: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(restore_spots())
