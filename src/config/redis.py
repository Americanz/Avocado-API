import redis
from src.config import settings

_redis_client = None


def get_redis_client():
    """Get Redis client with current settings"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    return _redis_client


def reset_redis_client():
    """Reset Redis client (useful for testing)"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
    _redis_client = None
