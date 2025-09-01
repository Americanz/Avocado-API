from typing import List, Dict, Any, Tuple
from telegram_bot.services.supabase.base import SupabaseBaseService


class AdminBonusService:
    """Сервіс для адміністративних операцій з бонусами"""

    def __init__(self, base_service: SupabaseBaseService):
        """Ініціалізує сервіс з базовим підключенням до Supabase

        Args:
            base_service: Базовий сервіс з підключенням до Supabase
        """
        self.base_service = base_service

    async def get_users_count(self) -> Tuple[int, int]:
        """
        Отримує кількість користувачів та скільки з них мають телефон

        Returns:
            Tuple[int, int]: (загальна_кількість, кількість_з_телефоном)
        """
        try:
            total_users = (
                self.base_service.client.table("bot_users")
                .select("*", count="exact")
                .execute()
            )

            users_with_phone = (
                self.base_service.client.table("bot_users")
                .select("*", count="exact")
                .neq("phone", None)
                .execute()
            )

            return (total_users.count or 0, users_with_phone.count or 0)
        except Exception as e:
            print(f"Error getting users count: {e}")
            return (0, 0)

    async def get_bonus_transactions_count(self) -> int:
        """
        Отримує загальну кількість транзакцій з бонусами

        Returns:
            int: Кількість транзакцій
        """
        try:
            total_bonuses = (
                self.base_service.client.table("bot_bonuses")
                .select("*", count="exact")
                .execute()
            )

            return total_bonuses.count or 0
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
        try:
            recent_bonuses = (
                self.base_service.client.table("bot_bonuses")
                .select("*")
                .order("updated_at", desc=True)
                .limit(limit)
                .execute()
            )

            return recent_bonuses.data or []
        except Exception as e:
            print(f"Error getting recent bonuses: {e}")
            return []

    async def get_total_balance_stats(self) -> Tuple[int, int]:
        """
        Отримує загальну суму балансів і кількість активних користувачів

        Returns:
            Tuple[int, int]: (загальний_баланс, активні_користувачі)
        """
        try:
            all_bonuses_query = (
                self.base_service.client.table("bot_bonuses")
                .select("balance")
                .execute()
            )

            total_balance = 0
            active_users = 0

            if all_bonuses_query.data:
                for bonus in all_bonuses_query.data:
                    balance = bonus.get("balance", 0)
                    total_balance += balance
                    if balance > 0:
                        active_users += 1

            return (total_balance, active_users)
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
