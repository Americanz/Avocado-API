"""
Admin Users Service for managing users in the bot
"""

from typing import List, Dict, Any, Optional, Tuple
from telegram_bot.services.supabase.base import SupabaseBaseService


class AdminUserService:
    """Сервіс для адміністративних операцій з користувачами"""

    def __init__(self, base_service: SupabaseBaseService):
        """Ініціалізує сервіс з базовим підключенням до Supabase

        Args:
            base_service: Базовий сервіс з підключенням до Supabase
        """
        self.base_service = base_service

    async def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримує детальну інформацію про користувача

        Args:
            user_id: ID користувача в Telegram

        Returns:
            Optional[Dict[str, Any]]: Інформація про користувача або None
        """
        try:
            user_response = (
                self.base_service.client.table("bot_users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if user_response.data:
                return user_response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user details: {e}")
            return None

    async def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Отримує список останніх зареєстрованих користувачів

        Args:
            limit: Максимальна кількість користувачів

        Returns:
            List[Dict[str, Any]]: Список користувачів
        """
        try:
            recent_users = (
                self.base_service.client.table("bot_users")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return recent_users.data or []
        except Exception as e:
            print(f"Error getting recent users: {e}")
            return []

    async def toggle_user_block(self, user_id: int, is_blocked: bool) -> bool:
        """
        Блокує або розблоковує користувача

        Args:
            user_id: ID користувача
            is_blocked: True для блокування, False для розблокування

        Returns:
            bool: True якщо операція успішна, False в іншому випадку
        """
        try:
            response = (
                self.base_service.client.table("bot_users")
                .update({"is_blocked": is_blocked})
                .eq("user_id", user_id)
                .execute()
            )

            return bool(response.data)
        except Exception as e:
            print(f"Error toggling user block status: {e}")
            return False

    async def export_users_list(
        self, with_phone_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Експортує список користувачів (з можливістю фільтрації за наявністю телефону)

        Args:
            with_phone_only: Якщо True, повертає лише користувачів з номером телефону

        Returns:
            List[Dict[str, Any]]: Список користувачів
        """
        try:
            query = self.base_service.client.table("bot_users").select("*")

            if with_phone_only:
                query = query.neq("phone", None)

            response = query.execute()

            return response.data or []
        except Exception as e:
            print(f"Error exporting users list: {e}")
            return []
