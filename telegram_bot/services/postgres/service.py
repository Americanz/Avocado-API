"""
Main PostgreSQL Service combining all sub-services
"""

import logging
from typing import List, Dict, Any, Optional
from .user import PostgresUserService
from .bonuses import PostgresBonusService

logger = logging.getLogger("telegram_bot.postgres")


class PostgresBonusesService:
    """Main PostgreSQL service combining user and bonus operations"""

    def __init__(self):
        self.user_service = PostgresUserService()
        self.bonus_service = PostgresBonusService()

    # User management methods
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        return self.user_service.get_user_by_id(user_id)

    def upsert_user(self, user_id: int, username: str = None, **kwargs) -> Dict[str, Any]:
        """Create or update user"""
        return self.user_service.upsert_user(user_id, username, **kwargs)

    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users"""
        return self.user_service.search_users(query)

    # Bonus management methods
    def get_user_balance(self, user_id: int) -> int:
        """Get user bonus balance"""
        return self.bonus_service.get_user_balance(user_id)

    def add_bonus(self, user_id: int, amount: int, reason: str = None, admin_id: int = None) -> bool:
        """Add bonuses to user"""
        return self.bonus_service.add_bonus(user_id, amount, reason, admin_id)

    def remove_bonus(self, user_id: int, amount: int, reason: str = None, admin_id: int = None) -> bool:
        """Remove bonuses from user"""
        return self.bonus_service.remove_bonus(user_id, amount, reason, admin_id)

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user bonus history"""
        return self.bonus_service.get_user_history(user_id, limit)

    def get_bonus_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get bonus history for all users"""
        return self.bonus_service.get_bonus_history(limit)

    def get_users_with_bonuses_count(self) -> int:
        """Get count of users with bonuses"""
        return self.bonus_service.get_users_with_bonuses_count()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        return self.bonus_service.table_exists(table_name)


# Create singleton instance
postgres_bonuses_service = PostgresBonusesService()