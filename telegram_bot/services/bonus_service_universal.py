from abc import ABC, abstractmethod
from typing import Any


# Абстрактний інтерфейс
class AbstractBonusService(ABC):
    @abstractmethod
    async def get_user_by_id(self, user_id: int):
        pass

    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_user_id: int):
        pass

    @abstractmethod
    async def upsert_user(self, user_id: int, username: str = None, **kwargs):
        pass

    @abstractmethod
    async def search_users(self, query: str, limit: int = 10):
        pass

    @abstractmethod
    async def add_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        pass

    @abstractmethod
    async def remove_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        pass

    @abstractmethod
    async def get_bonus_history(self, limit: int = 10):
        pass

    @abstractmethod
    async def get_user_balance(self, user_id: int) -> Any:
        pass

    @abstractmethod
    async def user_balance_exists(self, user_id: int) -> bool:
        pass

    @abstractmethod
    async def get_user_history(self, user_id: int):
        pass


# Реалізація для Supabase


# Імпортуємо реалізації з окремих файлів
from telegram_bot.config import settings


def get_bonus_service() -> AbstractBonusService:
    """Get appropriate bonus service based on configuration"""
    if getattr(settings, "USE_SUPABASE", False) and not getattr(settings, "USE_POSTGRESQL", False):
        from .bonus_service_supabase import SupabaseBonusServiceImpl
        return SupabaseBonusServiceImpl()
    else:
        # Use our PostgreSQL bonus service
        from .postgresql_bonus_service import get_postgresql_bonus_service
        from src.config.settings import settings as app_settings
        return get_postgresql_bonus_service(app_settings.DATABASE_URL)
