"""
Module loader for registering models and API routes with support for generic routes.

This module simplifies the process of loading and registering application modules.
When a new module is created, it needs to be registered in config.py to be included in the application.
It now supports automatic creation of generic CRUD routes for models.
"""

from typing import List
import importlib
from fastapi import APIRouter, FastAPI

# Імпортуємо функцію для отримання глобального логера
from src.core.models.logging.providers import get_logger as get_global_logger

# Імпортуємо конфігурацію модулів
from src.core.loader_factory.registry_factory.config import (
    BASE_MODULES,
    REGISTERED_MODULES,
)

# Отримуємо глобальний логер
logger = get_global_logger()

if logger is None:
    import logging

    logger = logging.getLogger(__name__)


def get_base_modules() -> List[str]:
    """
    Повертає список базових модулів, які повинні бути завантажені першими.
    """
    return BASE_MODULES


def get_all_registered_modules() -> List[str]:
    """
    Повертає список всіх зареєстрованих модулів.
    """
    return list(REGISTERED_MODULES.keys())


def get_model_import_paths() -> List[str]:
    """
    Повертає шляхи до моделей, які мають бути імпортовані, в правильному порядку.
    """
    ordered_modules = []

    # Спочатку додаємо базові модулі
    base_modules = get_base_modules()
    for module in base_modules:
        if module.endswith(".model"):
            # Якщо шлях вже закінчується на .model, не додаємо ще раз
            ordered_modules.append(module)
        else:
            ordered_modules.append(f"{module}.model")

    # Потім додаємо всі інші зареєстровані модулі
    for module in REGISTERED_MODULES:
        if module not in base_modules:
            if module.endswith(".model"):
                ordered_modules.append(module)
            else:
                ordered_modules.append(f"{module}.model")

    return ordered_modules


def load_module_routes(api_router: APIRouter, version_prefix: str = "") -> None:
    """
    Завантажує та реєструє маршрути API з усіх зареєстрованих модулів,
    включно з автоматично згенерованими маршрутами.

    Args:
        api_router: Головний API роутер
        version_prefix: Префікс версії API (наприклад, "/v1")
    """
    successful_modules = []
    failed_modules = []

    # Спочатку завантажуємо стандартні маршрути
    for module_path, route_prefix in REGISTERED_MODULES.items():
        try:
            # Перевіряємо, чи існує файл routes.py в модулі
            try:
                # Імпортуємо маршрути з модуля
                router_module = importlib.import_module(f"{module_path}.routes")

                # Додаємо маршрути до головного API роутера
                api_router.include_router(router_module.router, prefix=route_prefix)
                successful_modules.append(module_path)

            except (ImportError, AttributeError) as e:
                # Якщо файлу routes.py немає, це не помилка - можливо, модуль
                # використовує лише автоматично згенеровані маршрути
                logger.debug(
                    f"Модуль {module_path} не має файлу routes.py або атрибуту router",
                    module="module_loader",
                )

        except Exception as e:
            failed_modules.append(f"{module_path}: {str(e)}")
            logger.warning(
                f"Не вдалося завантажити маршрути з модуля {module_path}: {e}",
                module="module_loader",
            )

    # Логування результатів стандартних маршрутів
    if successful_modules:
        logger.info(
            f"Завантажено маршрути з {len(successful_modules)} модулів",
            module="module_loader",
        )

    if failed_modules:
        logger.warning(
            f"Не вдалося завантажити маршрути з {len(failed_modules)} модулів: {', '.join(failed_modules)}",
            module="module_loader",
        )

    # Тепер додаємо автоматично згенеровані маршрути для моделей з підтримкою generic_routes
    try:
        logger.info(
            "Запуск генерації універсальних маршрутів...", module="module_loader"
        )
        # Імпортуємо функцію всередині функції, щоб уникнути циклічної залежності
        from src.core.loader_factory.api_factory.discovery import (
            discover_and_create_generic_routes,
        )

        discover_and_create_generic_routes(api_router)
        logger.info("Універсальні маршрути успішно згенеровані", module="module_loader")
    except Exception as e:
        logger.error(f"Помилка при генерації універсальних маршрутів: {e}")


def register_models_from_modules() -> None:
    """
    Реєструє моделі з усіх зареєстрованих модулів.
    Ця функція автоматично імпортує всі моделі з модулів, які зареєстровані
    для використання в реєстрі моделей.
    """
    import_paths = get_model_import_paths()
    successful_imports = []
    failed_imports = []

    for module_path in import_paths:
        try:
            importlib.import_module(module_path)
            successful_imports.append(module_path)
        except Exception as e:
            failed_imports.append(f"{module_path}: {str(e)}")
            logger.error(f"Не вдалося імпортувати модуль {module_path}: {e}")

    # Логування результатів
    if successful_imports:
        logger.info(f"Імпортовано {len(successful_imports)} модулів з моделями")

    if failed_imports:
        logger.warning(
            f"Не вдалося імпортувати {len(failed_imports)} модулів з моделями: {', '.join(failed_imports)}"
        )


def setup_app_modules(app: FastAPI, api_version_prefix: str = "") -> None:
    """
    Налаштовує всі модулі для додатку FastAPI.

    Args:
        app: Екземпляр FastAPI додатку
        api_version_prefix: Префікс версії API (наприклад, "/v1")
    """
    # Створюємо головний API роутер
    api_router = APIRouter(prefix=api_version_prefix)

    # Завантажуємо маршрути з усіх модулів (включно з універсальними)
    load_module_routes(api_router, api_version_prefix)

    # Додаємо маршрут перевірки здоров'я API
    @api_router.get("/health", tags=["system"])
    async def health_check():
        """Перевірка здоров'я API."""
        return {"status": "ok"}

    # # Додаємо API ендпоінт для перевірки статусу міграцій
    # @api_router.get("/migrations/status", tags=["System"])
    # async def check_migrations_status():
    #     """Перевіряє статус міграцій."""
    #     from src.core.database.migrations import check_pending_migrations

    #     # Отримуємо інформацію про міграції
    #     status = await check_pending_migrations()

    #     # Спрощуємо результат для API
    #     return {
    #         "current_revision": status["current_revision"],
    #         "latest_revision": status["latest_revision"],
    #         "is_up_to_date": status["is_up_to_date"],
    #         "pending_count": status["pending_count"],
    #         "pending_migrations": [
    #             {"revision": m["revision"], "description": m["doc"]}
    #             for m in status["pending_migrations"]
    #         ],
    #     }

    # Додаємо головний API роутер до додатку
    app.include_router(api_router)

    # Логуємо результат
    logger.info(
        f"Всі модулі успішно налаштовані, API доступний за {api_version_prefix}",
        module="module_loader",
    )
