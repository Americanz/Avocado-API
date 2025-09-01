"""
History service for managing bonus history records
"""

from typing import List, Dict, Any, Optional
from telegram_bot.services.supabase.base import SupabaseBaseService


class HistoryService:
    """Сервіс для роботи з історією бонусів"""

    def __init__(self, base_service: SupabaseBaseService):
        """Ініціалізує сервіс з базовим підключенням до Supabase

        Args:
            base_service: Базовий сервіс з підключенням до Supabase
        """
        self.base_service = base_service

    async def get_user_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Отримує історію бонусів для конкретного користувача

        Args:
            user_id: ID користувача в Telegram

        Returns:
            List[Dict[str, Any]]: Список записів історії бонусів
        """
        if not self.base_service.table_exists("bot_bonuses_history"):
            raise Exception(
                "Таблиця bot_bonuses_history не існує. Створіть її у Supabase!"
            )

        try:
            response = (
                self.base_service.client.table("bot_bonuses_history")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

    async def add_history_record(
        self,
        user_id: int,
        change: int,
        description: str,
        admin_id: Optional[int] = None,
    ) -> bool:
        """
        Додає запис в історію бонусів

        Args:
            user_id: ID користувача
            change: Зміна балансу (додатне або від'ємне число)
            description: Опис операції
            admin_id: ID адміністратора, який виконав операцію (якщо є)

        Returns:
            bool: True якщо операція успішна, False в іншому випадку
        """
        if not self.base_service.table_exists("bot_bonuses_history"):
            raise Exception(
                "Таблиця bot_bonuses_history не існує. Створіть її у Supabase!"
            )

        try:
            record = {
                "user_id": user_id,
                "change": change,
                "description": description,
            }

            if admin_id:
                record["admin_id"] = admin_id

            response = (
                self.base_service.client.table("bot_bonuses_history")
                .insert(record)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            print(f"Error adding history record: {e}")
            return False

    async def get_global_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Отримує глобальну історію бонусів для всіх користувачів

        Args:
            limit: Максимальна кількість записів

        Returns:
            List[Dict[str, Any]]: Список записів історії бонусів
        """
        if not self.base_service.table_exists("bot_bonuses_history"):
            raise Exception(
                "Таблиця bot_bonuses_history не існує. Створіть її у Supabase!"
            )

        try:
            response = (
                self.base_service.client.table("bot_bonuses_history")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"Error getting global history: {e}")
            return []
