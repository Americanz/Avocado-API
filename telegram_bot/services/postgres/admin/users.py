"""
Admin Users Service for PostgreSQL - managing users in the bot
"""

from typing import List, Dict, Any, Optional, Tuple
from src.features.telegram_bot.models import Client as Client
from ..base import PostgresBaseService


class AdminUserService:
    """Сервіс для адміністративних операцій з користувачами"""

    def __init__(self, base_service: PostgresBaseService):
        """Ініціалізує сервіс з базовим підключенням до PostgreSQL

        Args:
            base_service: Базовий сервіс з підключенням до PostgreSQL
        """
        self.base_service = base_service

    def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримує детальну інформацію про користувача

        Args:
            user_id: ID користувача в Telegram

        Returns:
            Optional[Dict[str, Any]]: Інформація про користувача або None
        """

        def query(db):
            user = db.query(Client).filter(Client.user_id == user_id).first()
            if user:
                return {
                    "user_id": user.telegram_user_id,
                    "username": user.telegram_username,
                    "first_name": user.telegram_first_name,
                    "last_name": user.telegram_last_name,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "is_blocked": user.is_blocked,
                    "language_code": user.language_code,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                }
            return None

        return self.base_service.execute_query(query)

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
                    "user_id": user.telegram_user_id,
                    "username": user.telegram_username,
                    "first_name": user.telegram_first_name,
                    "last_name": user.telegram_last_name,
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
