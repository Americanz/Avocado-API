from .redis import (
    get_redis_client,
    get_async_redis_client,
    close_redis_client,
    close_async_redis_client,
    is_redis_available,
    cache_user_data,
    get_cached_user_data,
    clear_user_cache,
)

# Імпорт settings з окремого файлу для уникнення циклічних імпортів
import os
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv()


class Settings:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # PostgreSQL connection components
    POSTGRES_USER = os.getenv("POSTGRES_USER", "avocado_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "avocado_pass")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "avocado_db")

    # PostgreSQL settings (динамічно формуємо з компонентів)
    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Legacy Supabase settings (for compatibility)
    SUPABASE_API_URL = os.getenv("SUPABASE_API_URL", "")
    SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY", "")

    # Database choice
    USE_POSTGRESQL = True  # Force PostgreSQL usage
    USE_SUPABASE = os.getenv("USE_SUPABASE", "False").lower() == "true"

    # Redis settings for telegram bot
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(
        os.getenv("REDIS_DB", "1")
    )  # DB 1 для бота (щоб не конфліктувати з FastAPI)
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Telegram bot Redis options
    USE_REDIS_STORAGE = os.getenv("USE_REDIS_STORAGE", "False").lower() == "true"

    # Logging settings for telegram bot
    LOG_USER_ACTIONS = os.getenv("LOG_USER_ACTIONS", "True").lower() == "true"
    LOG_BUTTON_CLICKS = os.getenv("LOG_BUTTON_CLICKS", "True").lower() == "true"
    LOG_COMMANDS = os.getenv("LOG_COMMANDS", "True").lower() == "true"
    LOG_MESSAGES = os.getenv("LOG_MESSAGES", "False").lower() == "true"

    # Детальність логування
    VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "False").lower() == "true"


settings = Settings()

__all__ = [
    "get_redis_client",
    "get_async_redis_client",
    "close_redis_client",
    "close_async_redis_client",
    "is_redis_available",
    "cache_user_data",
    "get_cached_user_data",
    "clear_user_cache",
    "settings",
]
