#!/usr/bin/env python
"""
Скрипт для ручного створення всіх таблиць в базі даних.
Використовуйте цей скрипт, якщо у вас виникають проблеми з міграціями alembic.
"""

import os
import logging
from sqlalchemy import inspect

# Налаштовуємо логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Імпортуємо необхідні модулі
from src.core.database.connection import Base, engine
from src.core.models.loader.registry import register_all_models

def create_database():
    """Створює всі таблиці в базі даних."""
    try:
        # Спочатку видаляємо файл бази даних, якщо він існує
        db_path = "database.db"
        if os.path.exists(db_path):
            logger.info(f"Видаляю існуючий файл бази даних: {db_path}")
            os.remove(db_path)
            logger.info("Файл бази даних видалено")

        # Реєструємо всі моделі
        logger.info("Реєстрація всіх моделей...")
        register_all_models()

        # Виводимо список всіх таблиць в метаданих
        logger.info("Таблиці в метаданих:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"- {table_name}")

        # Створюємо всі таблиці
        logger.info("Створення таблиць в базі даних...")
        Base.metadata.create_all(bind=engine)

        # Перевіряємо, що таблиці були створені
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"Створено {len(tables)} таблиць:")
        for table in tables:
            logger.info(f"- {table}")

        logger.info("База даних успішно створена!")
        return True
    except Exception as e:
        logger.error(f"Помилка при створенні бази даних: {e}")
        return False

if __name__ == "__main__":
    create_database()
