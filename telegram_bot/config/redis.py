import redis
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_redis_client = None
_async_redis_client = None


def _get_settings():
    """Отримуємо settings без циклічного імпорту"""
    from telegram_bot.config import settings

    return settings


def get_redis_client():
    """Get synchronous Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            settings = _get_settings()
            _redis_client = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "localhost"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 1),  # Використовуємо DB 1 для бота
                password=getattr(settings, "REDIS_PASSWORD", None),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Тестуємо підключення
            _redis_client.ping()
            logger.info("Redis підключено успішно")
        except Exception as e:
            logger.warning(
                f"Не вдалося підключити Redis: {e}. Буде використано MemoryStorage"
            )
            _redis_client = None
    return _redis_client


async def get_async_redis_client():
    """Get asynchronous Redis client"""
    global _async_redis_client
    if _async_redis_client is None:
        try:
            import redis.asyncio as aioredis

            settings = _get_settings()
            _async_redis_client = aioredis.Redis(
                host=getattr(settings, "REDIS_HOST", "localhost"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 1),  # Використовуємо DB 1 для бота
                password=getattr(settings, "REDIS_PASSWORD", None),
                decode_responses=True,
            )
            # Тестуємо підключення
            await _async_redis_client.ping()
            logger.info("Async Redis підключено успішно")
        except Exception as e:
            logger.warning(f"Не вдалося підключити Async Redis: {e}")
            _async_redis_client = None
    return _async_redis_client


def close_redis_client():
    """Закрити Redis підключення"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("Redis підключення закрито")
        except Exception as e:
            logger.error(f"Помилка при закритті Redis: {e}")
        finally:
            _redis_client = None


async def close_async_redis_client():
    """Закрити async Redis підключення"""
    global _async_redis_client
    if _async_redis_client:
        try:
            await _async_redis_client.close()
            logger.info("Async Redis підключення закрито")
        except Exception as e:
            logger.error(f"Помилка при закритті Async Redis: {e}")
        finally:
            _async_redis_client = None


def is_redis_available() -> bool:
    """Перевірити чи доступний Redis"""
    try:
        client = get_redis_client()
        return client is not None and client.ping()
    except:
        return False


# Функції для роботи з кешем бота
def cache_user_data(user_id: int, data: dict, expire_seconds: int = 3600) -> bool:
    """Кешувати дані користувача"""
    try:
        client = get_redis_client()
        if client:
            key = f"bot:user:{user_id}"
            import json

            client.setex(key, expire_seconds, json.dumps(data))
            return True
    except Exception as e:
        logger.error(f"Помилка кешування даних користувача {user_id}: {e}")
    return False


def get_cached_user_data(user_id: int) -> Optional[dict]:
    """Отримати кешовані дані користувача"""
    try:
        client = get_redis_client()
        if client:
            key = f"bot:user:{user_id}"
            data = client.get(key)
            if data:
                import json

                return json.loads(data)
    except Exception as e:
        logger.error(f"Помилка отримання кешованих даних користувача {user_id}: {e}")
    return None


def clear_user_cache(user_id: int) -> bool:
    """Очистити кеш користувача"""
    try:
        client = get_redis_client()
        if client:
            key = f"bot:user:{user_id}"
            client.delete(key)
            return True
    except Exception as e:
        logger.error(f"Помилка очищення кешу користувача {user_id}: {e}")
    return False
