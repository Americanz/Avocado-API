"""
Скрипт для створення всіх таблиць в базі даних
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.database.connection import Base, async_engine


async def create_all_tables():
    """Створити всі таблиці"""
    print("🔧 Створення всіх таблиць...")

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Всі таблиці створено успішно!")

        # Виводимо список створених таблиць
        print("\n📋 Створені таблиці:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")


if __name__ == "__main__":
    asyncio.run(create_all_tables())
