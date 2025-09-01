from telegram_bot.services.supabase.base import SupabaseBaseService
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from telegram_bot.services.supabase.admin.bonuses import AdminBonusService
from telegram_bot.services.supabase.admin.users import AdminUserService
from telegram_bot.services.supabase.history import HistoryService
from telegram_bot.services.supabase.user import UserService


class SupabaseBonusesService(SupabaseBaseService):
    def __init__(self):
        super().__init__()
        # Ініціалізуємо сервіси
        self.admin_bonuses = AdminBonusService(self)
        self.admin_users = AdminUserService(self)
        self.history = HistoryService(self)
        self.user = UserService(self)
    async def get_user_balance(self, user_id: int) -> int:
        if not self.table_exists("bot_bonuses"):
            raise Exception("Таблиця bot_bonuses не існує. Створіть її у Supabase!")
        response = (
            self.client.table("bot_bonuses")
            .select("balance")
            .eq("user_id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]["balance"]
        return 0

    async def user_balance_exists(self, user_id: int) -> bool:
        """Перевіряє, чи існує запис балансу для користувача"""
        if not self.table_exists("bot_bonuses"):
            return False
        response = (
            self.client.table("bot_bonuses")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        return bool(response.data)
    async def get_user_history(self, user_id: int):
        """
        Отримує історію бонусів для конкретного користувача (метод для зворотної сумісності)

        Args:
            user_id: ID користувача в Telegram

        Returns:
            List[Dict[str, Any]]: Список записів історії бонусів
        """
        # Використовуємо новий history сервіс
        return await self.history.get_user_history(user_id)

    async def add_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        """
        Додає бонуси користувачу

        Args:
            user_id: ID користувача
            amount: Кількість бонусів (додатне число)
            reason: Причина додавання бонусів
            admin_id: ID адміністратора, який додав бонуси

        Returns:
            bool: True якщо операція успішна, False в іншому випадку
        """
        if amount <= 0:
            raise ValueError("Кількість бонусів повинна бути додатнім числом")

        try:
            # Перевіряємо чи існує користувач
            user_response = (
                self.client.table("bot_users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not user_response.data:
                return False

            # Отримуємо поточний баланс
            current_balance = await self.get_user_balance(user_id)
            new_balance = current_balance + amount

            # Перевіряємо, чи існує запис балансу для користувача
            balance_exists = await self.user_balance_exists(user_id)

            if balance_exists:
                # Оновлюємо існуючий баланс
                balance_response = (
                    self.client.table("bot_bonuses")
                    .update({"balance": new_balance})
                    .eq("user_id", user_id)
                    .execute()
                )
            else:
                # Створюємо новий запис балансу
                balance_response = (
                    self.client.table("bot_bonuses")
                    .insert({"user_id": user_id, "balance": new_balance})
                    .execute()
                )            # Додаємо запис в історію бонусів через спеціалізований сервіс
            description = f"Додано {amount} бонусів. Причина: {reason}"
            await self.history.add_history_record(
                user_id=user_id,
                change=amount,
                description=description,
                admin_id=admin_id
            )

            return True
        except Exception as e:
            print(f"Error adding bonus: {e}")
            return False

    async def remove_bonus(
        self, user_id: int, amount: int, reason: str, admin_id: int
    ) -> bool:
        """
        Знімає бонуси з користувача

        Args:
            user_id: ID користувача
            amount: Кількість бонусів для зняття (додатне число)
            reason: Причина зняття бонусів
            admin_id: ID адміністратора, який зняв бонуси

        Returns:
            bool: True якщо операція успішна, False в іншому випадку
        """
        if amount <= 0:
            raise ValueError("Кількість бонусів повинна бути додатнім числом")

        try:
            # Перевіряємо чи існує користувач
            user_response = (
                self.client.table("bot_users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if not user_response.data:
                return False

            # Отримуємо поточний баланс
            current_balance = await self.get_user_balance(user_id)

            # Перевіряємо чи достатньо бонусів
            if current_balance < amount:
                return False

            new_balance = current_balance - amount            # Оновлюємо баланс
            balance_response = (
                self.client.table("bot_bonuses")
                .update({"balance": new_balance})
                .eq("user_id", user_id)
                .execute()
            )

            # Додаємо запис в історію бонусів через спеціалізований сервіс
            description = f"Списано {amount} бонусів. Причина: {reason}"
            await self.history.add_history_record(
                user_id=user_id,
                change=-amount,  # Від'ємне значення для зняття
                description=description,
                admin_id=admin_id
            )

            return True
        except Exception as e:
            print(f"Error removing bonus: {e}")
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
                    self.client.table("bot_users")
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
                self.client.table("bot_users")
                .select("*")
                .or_(f"username.ilike.%{query}%,phone.ilike.%{query}%")
                .limit(limit)
                .execute()
            )

            return response.data or []
        except Exception as e:
            print(f"Error searching users: {e}")
            return []

    async def get_bonus_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Отримує загальну історію бонусів для всіх користувачів

        Args:
            limit: Максимальна кількість результатів

        Returns:
            List[Dict[str, Any]]: Список записів історії бонусів
        """
        try:
            response = (
                self.client.table("bot_bonuses_history")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data or []
        except Exception as e:
            print(f"Error getting bonus history: {e}")
            return []
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Отримує інформацію про користувача за ID

        Args:
            user_id: ID користувача

        Returns:
            Optional[Dict[str, Any]]: Інформація про користувача або None
        """
        try:
            response = (
                self.client.table("bot_users")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    async def get_user_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Отримує історію бонусів користувача за ID

        Args:
            user_id: ID користувача

        Returns:
            List[Dict[str, Any]]: Історія бонусів користувача
        """
        try:
            response = (
                self.client.table("bot_bonuses_history")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data or []
        except Exception as e:
            print(f"Error getting user history: {e}")
            return []

# Інстанс сервісу тепер створюється в __init__.py
