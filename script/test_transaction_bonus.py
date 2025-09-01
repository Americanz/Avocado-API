#!/usr/bin/env python3
"""
Простий тест для перевірки таблиці transaction_bonus
"""

import sys
import os

# Додаємо корневу папку до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.database.connection import SessionLocal
from src.features.telegram_bot.models import TransactionBonus


def test_transaction_bonus_table():
    """Тестує роботу з таблицею transaction_bonus"""

    with SessionLocal() as db:
        try:
            # Спробуємо зробити простий запит до таблиці
            count = db.query(TransactionBonus).count()
            print(f"✅ Таблиця transaction_bonus працює!")
            print(f"📊 Кількість записів: {count}")

            # Перевіримо структуру таблиці
            print(f"\n🏗️ Модель TransactionBonus:")
            print(f"- Таблиця: {TransactionBonus.__tablename__}")
            print(f"- Поля пошуку: {TransactionBonus.search_fields}")
            print(f"- Сортування: {TransactionBonus.default_order_by}")

            return True

        except Exception as e:
            print(f"❌ Помилка при роботі з таблицею transaction_bonus:")
            print(f"   {e}")
            return False


if __name__ == "__main__":
    test_transaction_bonus_table()
