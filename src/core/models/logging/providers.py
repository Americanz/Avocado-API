"""
Провайдери для оптимізованих сервісів логування
"""

from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from src.core.database.connection import get_db
from src.core.models.logging.logging_service import OptimizedLoggingService
from src.core.models.logging.loguru_service import OptimizedLoguruService

# Змінна для зберігання глобального екземпляру логера, що буде ініціалізований при запуску додатку
_global_logger: Optional[OptimizedLoguruService] = None


def get_logger(db: Session = Depends(get_db)) -> OptimizedLoguruService:
    """
    Провайдер для отримання логера з підтримкою loguru та запису в БД.
    Може використовуватись як FastAPI Dependency.

    Спочатку перевіряє наявність глобального логера, якщо він недоступний -
    створює новий екземпляр зі з'єднанням до БД.

    Args:
        db: Сесія бази даних

    Returns:
        OptimizedLoguruService: Сервіс логування з підтримкою loguru і БД
    """
    global _global_logger

    # Якщо глобальний логер вже ініціалізований, повертаємо його
    if _global_logger is not None:
        return _global_logger

    # Інакше створюємо новий логер
    db_logger = OptimizedLoggingService(db)
    logger = OptimizedLoguruService(db_service=db_logger)

    return logger


def set_global_logger(logger: OptimizedLoguruService) -> None:
    """
    Встановлює глобальний логер, який буде доступний через get_logger.
    Викликається при запуску додатку.

    Args:
        logger: Екземпляр OptimizedLoguruService для глобального доступу
    """
    global _global_logger
    _global_logger = logger


def get_global_logger() -> Optional[OptimizedLoguruService]:
    """
    Отримує глобальний логер без залежності від FastAPI.
    Повертає None, якщо логер ще не ініціалізований.

    Returns:
        Optional[OptimizedLoguruService]: Глобальний сервіс логування або None
    """
    return _global_logger
