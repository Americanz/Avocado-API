"""
Admin Bonuses Service for PostgreSQL - managing bonuses in the bot
"""

from typing import List, Dict, Any, Tuple
from src.features.telegram_bot.models import (
    Client,
    TelegramBonusAccount as BonusAccount,
    Transaction,
)
from ..base import PostgresBaseService


class AdminBonusService:
    """Сервіс для адміністративних операцій з бонусами"""

    def __init__(self, base_service: PostgresBaseService):
        """Ініціалізує сервіс з базовим підключенням до PostgreSQL

        Args:
            base_service: Базовий сервіс з підключенням до PostgreSQL
        """
        self.base_service = base_service

    async def get_users_count(self) -> Tuple[int, int]:
        """
        Отримує кількість користувачів та скільки з них мають телефон

        Returns:
            Tuple[int, int]: (загальна_кількість, кількість_з_телефоном)
        """

        def query(db):
            total_users = db.query(Client).count()
            users_with_phone = db.query(Client).filter(Client.phone.isnot(None)).count()
            return (total_users, users_with_phone)

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.base_service.execute_query, query
            )
        except Exception as e:
            print(f"Error getting users count: {e}")
            return (0, 0)

    async def get_bonus_transactions_count(self) -> int:
        """
        Отримує загальну кількість транзакцій з бонусами

        Returns:
            int: Кількість транзакцій
        """

        def query(db):
            return db.query(Transaction).count()

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.base_service.execute_query, query
            )
        except Exception as e:
            print(f"Error getting bonus transactions count: {e}")
            return 0

    async def get_recent_bonuses(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Отримує останні оновлення балансу користувачів

        Args:
            limit: Максимальна кількість записів

        Returns:
            List[Dict[str, Any]]: Список останніх операцій з балансами
        """

        def query(db):
            accounts = (
                db.query(BonusAccount)
                .order_by(BonusAccount.updated_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "user_id": account.client_id,
                    "balance": account.balance,
                    "updated_at": account.updated_at,
                }
                for account in accounts
            ]

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.base_service.execute_query, query
            )
        except Exception as e:
            print(f"Error getting recent bonuses: {e}")
            return []

    async def get_total_balance_stats(self) -> Tuple[int, int]:
        """
        Отримує загальну суму балансів і кількість активних користувачів

        Returns:
            Tuple[int, int]: (загальний_баланс, активні_користувачі)
        """

        def query(db):
            accounts = db.query(BonusAccount).all()
            total_balance = 0
            active_users = 0

            for account in accounts:
                balance = account.balance or 0
                total_balance += balance
                if balance > 0:
                    active_users += 1

            return (total_balance, active_users)

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.base_service.execute_query, query
            )
        except Exception as e:
            print(f"Error getting total balance stats: {e}")
            return (0, 0)

    async def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Отримує список останніх зареєстрованих користувачів

        Args:
            limit: Максимальна кількість користувачів

        Returns:
            List[Dict[str, Any]]: Список користувачів
        """

        def query(db):
            users = (
                db.query(Client).order_by(Client.created_at.desc()).limit(limit).all()
            )

            return [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "is_blocked": user.is_blocked,
                    "language_code": user.language_code,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
                for user in users
            ]

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self.base_service.execute_query, query
            )
        except Exception as e:
            print(f"Error getting recent users: {e}")
            return []
