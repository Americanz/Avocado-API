"""
User service for managing user data
"""

from typing import List, Dict, Any, Optional
from telegram_bot.services.supabase.base import SupabaseBaseService


class UserService:
    """Сервіс для роботи з користувачами"""

    def __init__(self, base_service: SupabaseBaseService):
        """Ініціалізує сервіс з базовим підключенням до Supabase

        Args:
            base_service: Базовий сервіс з підключенням до Supabase
        """
        self.base_service = base_service

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримує дані користувача за ID

        Args:
            user_id: ID користувача в Telegram

        Returns:
            Optional[Dict[str, Any]]: Дані користувача або None
        """
        try:
            response = (
                self.base_service.client.table("bot_users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None

    async def user_exists(self, user_id: int) -> bool:
        """
        Перевіряє чи існує користувач за ID

        Args:
            user_id: ID користувача в Telegram

        Returns:
            bool: True якщо користувач існує, False в іншому випадку
        """
        try:
            response = (
                self.base_service.client.table("bot_users")
                .select("user_id")
                .eq("user_id", user_id)
                .execute()
            )

            return bool(response.data)
        except Exception as e:
            print(f"Error checking if user exists: {e}")
            return False

    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Створює нового користувача

        Args:
            user_data: Дані користувача

        Returns:
            bool: True якщо користувач створений успішно, False в іншому випадку
        """
        try:
            required_fields = ["user_id", "username"]
            if not all(field in user_data for field in required_fields):
                return False

            response = (
                self.base_service.client.table("bot_users").insert(user_data).execute()
            )

            return bool(response.data)
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Оновлює дані користувача

        Args:
            user_id: ID користувача в Telegram
            user_data: Нові дані користувача

        Returns:
            bool: True якщо дані оновлені успішно, False в іншому випадку
        """
        try:
            response = (
                self.base_service.client.table("bot_users")
                .update(user_data)
                .eq("user_id", user_id)
                .execute()
            )

            return bool(response.data)
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Шукає користувачів за ім'ям, номером телефону або ID

        Args:
            query: Пошуковий запит
            limit: Максимальна кількість результатів

        Returns:
            List[Dict[str, Any]]: Список знайдених користувачів
        """
        try:
            # Спробуємо конвертувати запит в int для пошуку за ID
            try:
                user_id = int(query)
                id_response = (
                    self.base_service.client.table("bot_users")
                    .select("*")
                    .eq("user_id", user_id)
                    .execute()
                )
                if id_response.data:
                    return id_response.data
            except ValueError:
                pass

            # Пошук за username або phone
            response = (
                self.base_service.client.table("bot_users")
                .select("*")
                .or_(f"username.ilike.%{query}%,phone.ilike.%{query}%")
                .limit(limit)
                .execute()
            )

            return response.data or []
        except Exception as e:
            print(f"Error searching users: {e}")
            return []
