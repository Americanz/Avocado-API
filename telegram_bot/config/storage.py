from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from telegram_bot.config.redis import get_redis_client, is_redis_available
import logging

logger = logging.getLogger(__name__)


def get_storage():
    """
    Повертає відповідне сховище для FSM:
    - RedisStorage якщо Redis доступний і увімкнений
    - MemoryStorage як fallback
    """
    from telegram_bot.config import settings

    if settings.USE_REDIS_STORAGE and is_redis_available():
        try:
            # Створюємо Redis Storage для aiogram
            redis_client = get_redis_client()
            if redis_client:
                storage = RedisStorage.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                )
                logger.info("Використовується RedisStorage для FSM")
                return storage
        except Exception as e:
            logger.warning(
                f"Не вдалося створити RedisStorage: {e}. Використовується MemoryStorage"
            )

    logger.info("Використовується MemoryStorage для FSM")
    return MemoryStorage()


async def close_storage(storage):
    """Закрити сховище"""
    if hasattr(storage, "close"):
        try:
            await storage.close()
            logger.info("FSM Storage закрито")
        except Exception as e:
            logger.error(f"Помилка при закритті FSM Storage: {e}")
