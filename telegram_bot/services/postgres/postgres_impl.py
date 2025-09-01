"""
PostgreSQL implementation for Universal Bonus Service
"""

import asyncio
import logging
from typing import Any, List, Dict, Optional
from ..bonus_service_universal import AbstractBonusService
from .service import postgres_bonuses_service
from .admin.users import AdminUserService
from .admin.bonuses import AdminBonusService
from .base import PostgresBaseService

logger = logging.getLogger("telegram_bot.postgres_impl")


class PostgresBonusServiceImpl(AbstractBonusService):
    """PostgreSQL implementation of AbstractBonusService"""

    def __init__(self):
        self.service = postgres_bonuses_service
        # Initialize admin services
        base_service = PostgresBaseService()
        self.admin_users = AdminUserService(base_service)
        self.admin_bonuses = AdminBonusService(base_service)

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.get_user_by_id, user_id)
    
    async def upsert_user(self, user_id: int, username: str = None, **kwargs) -> Dict[str, Any]:
        """Create or update user"""
        def wrapper():
            return self.service.upsert_user(user_id, username, **kwargs)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, wrapper)

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search users"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.search_users, query)

    async def add_bonus(self, user_id: int, amount: int, reason: str, admin_id: int) -> bool:
        """Add bonuses to user"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.service.add_bonus, user_id, amount, reason, admin_id
        )

    async def remove_bonus(self, user_id: int, amount: int, reason: str, admin_id: int) -> bool:
        """Remove bonuses from user"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.service.remove_bonus, user_id, amount, reason, admin_id
        )

    async def get_bonus_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get bonus history for all users"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.get_bonus_history, limit)

    async def get_user_balance(self, user_id: int) -> int:
        """Get user balance"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.get_user_balance, user_id)

    async def user_balance_exists(self, user_id: int) -> bool:
        """Check if user has bonus account"""
        balance = await self.get_user_balance(user_id)
        return balance > 0

    async def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user bonus history"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.get_user_history, user_id, limit)

    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.service.table_exists, table_name)