#!/usr/bin/env python
"""
Run application locally using uvicorn.
"""
import os
import sys
import contextlib

import uvicorn

from src.config import settings

# from src.config.logging import configure_logging

# Потрібні імпорти для оптимізованої системи логування
from sqlalchemy.orm import Session
from src.core.database.connection import get_sync_db
from src.core.models.logging.logging_service import OptimizedLoggingService
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.models.logging.providers import set_global_logger
from src.core.models.loader.registry import register_all_models


def setup_logger():
    """
    Створює тимчасовий логер для роботи скрипта

    Returns:
        OptimizedLoguruService: Екземпляр OptimizedLoguruService для логування
    """
    # Отримуємо сесію БД для логування
    db = None
    try:
        # Використовуємо контекстний менеджер для правильного закриття з'єднання
        with contextlib.closing(next(get_sync_db())) as db_session:
            db = db_session
            db_logger = OptimizedLoggingService(db=db)
            logger = OptimizedLoguruService(db_service=db_logger)

            # Встановлюємо його як глобальний для доступу з інших частин додатку
            set_global_logger(logger)

            return logger
    except Exception as e:
        # Якщо не вдалося підключитися до БД, повертаємо OptimizedLoguruService без БД
        print(f"Warning: could not connect to database for logging: {e}")
        logger = OptimizedLoguruService(db_service=None)
        set_global_logger(logger)
        return logger


def setup_environment(logger):
    """
    Setup environment before running the application.
    This ensures all models are properly imported and initialized.

    Args:
        logger: OptimizedLoguruService екземпляр для логування
    """
    # Add project root to sys.path if needed
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Реєструємо всі моделі перед запуском застосунку
    logger.info("Registering all models...", module="run")
    models = register_all_models()
    logger.info(f"Registered {len(models)} models", module="run")


if __name__ == "__main__":
    # Configure logging
    # configure_logging()

    # Створюємо логер
    logger = setup_logger()

    # Log startup info
    logger.info(f"Starting {settings.APP_NAME} API", module="run")
    logger.info(f"Debug mode: {settings.DEBUG}", module="run")

    # Setup environment and register all models
    setup_environment(logger)

    # Run uvicorn server
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
