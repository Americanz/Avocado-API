"""
Model registry for centralized management of all SQLAlchemy models.

This module imports and registers all models in a controlled order to avoid circular
import issues and ensure all relationships are properly established.

Usage:
    from src.core.models.registry import register_all_models

    # Call this function at application startup
    register_all_models()
"""

import importlib
import inspect
import logging
import os
from pathlib import Path
from typing import Dict, List, Type, Optional, Tuple

from sqlalchemy.orm import configure_mappers

from src.core.models.base_model import BaseModel
from src.core.loader.module_registry.loader import get_model_import_paths
from src.core.loader.module_registry.config import ALL_MODULES, MODEL_SEARCH_PATHS

# Глобальний реєстр моделей
_MODELS: Dict[str, Type[BaseModel]] = {}
_MODELS_LOADED = False
_KNOWN_MISSING_PACKAGES = {
    "tortoise": "Це модель використовує Tortoise ORM замість SQLAlchemy. Потрібен перехід на SQLAlchemy."
}


def _get_model_import_order() -> List[str]:
    """
    Повертає список модулів з моделями в порядку, який забезпечує коректне завантаження.
    """
    # Використовуємо центральний реєстр модулів для визначення порядку завантаження
    return get_model_import_paths()


def _discover_model_modules() -> List[str]:
    """
    Автоматично знаходить всі модулі, які можуть містити моделі в дозволених папках.
    """
    discovered_modules = []

    # Визначаємо корінь проекту
    project_root = Path(__file__).parent.parent.parent.parent

    # Конвертуємо шляхи в об'єкти Path
    search_paths = [
        project_root / path.replace("/", os.sep) for path in MODEL_SEARCH_PATHS
    ]

    # Проходимо по дозволених папках
    for base_path in search_paths:
        if not base_path.exists():
            continue

        for root, _, files in os.walk(base_path):
            for file in files:
                if file in ["model.py", "models.py"]:
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    module_path = rel_path.replace(os.sep, ".").replace(".py", "")

                    # Додаємо модуль, якщо його ще немає в списку
                    if module_path not in discovered_modules:
                        discovered_modules.append(module_path)

    return discovered_modules


def _analyze_import_error(module_path: str, error: ImportError) -> Tuple[bool, str]:
    """
    Аналізує помилку імпорту і визначає, чи це відома проблема.

    Args:
        module_path: Шлях до модуля
        error: Виключення ImportError

    Returns:
        Tuple[bool, str]: (Чи є відомою проблемою, опис проблеми)
    """
    error_msg = str(error)

    for package, description in _KNOWN_MISSING_PACKAGES.items():
        if f"No module named '{package}'" in error_msg:
            return True, f"Не вдалося імпортувати модуль {module_path}: {description}"

    return False, f"Не вдалося імпортувати модуль {module_path}: {error_msg}"


def _import_and_register_models(module_paths: List[str]) -> None:
    """
    Імпортує модулі за вказаними шляхами та реєструє всі знайдені моделі.

    Args:
        module_paths: Список шляхів до модулів для імпорту
    """
    global _MODELS

    for module_path in module_paths:
        try:
            # Імпортуємо модуль
            module = importlib.import_module(module_path)

            # Знаходимо всі класи в модулі, які успадковуються від BaseModel
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseModel)
                    and obj != BaseModel
                    and not obj.__name__.startswith("_")
                ):

                    # Реєструємо модель
                    _MODELS[obj.__name__] = obj
                    logging.debug(
                        f"Registered model: {obj.__name__} from {module_path}"
                    )

        except ImportError as e:
            is_known, message = _analyze_import_error(module_path, e)
            if is_known:
                logging.warning(message)
            else:
                logging.error(message)
        except Exception as e:
            logging.error(f"Error processing module {module_path}: {e}")


def register_all_models() -> Dict[str, Type[BaseModel]]:
    """
    Реєструє всі моделі в системі в правильному порядку.

    Returns:
        Dict[str, Type[BaseModel]]: Словник зареєстрованих моделей
    """
    global _MODELS, _MODELS_LOADED

    if _MODELS_LOADED:
        return _MODELS

    # Додамо логування для діагностики процесу реєстрації моделей
    logging.info("Starting model registration process")

    # Отримуємо модулі для реєстрації
    model_modules = []

    # Додаємо модулі з конфігурації ALL_MODULES
    for module in ALL_MODULES:
        if module.endswith(".model"):
            model_modules.append(module)
        else:
            model_modules.append(f"{module}.model")

    unique_modules = []
    for module in model_modules:
        if module not in unique_modules:
            unique_modules.append(module)


    # # Отримуємо модулі в правильному порядку завантаження
    # ordered_modules = _get_model_import_order()
    # logging.info(f"Ordered modules to import: {ordered_modules}")

    # # Об'єднуємо всі джерела модулів і видаляємо дублікати
    # all_modules = list(dict.fromkeys(model_modules + ordered_modules))

    # # Додаємо автоматично виявлені модулі, якщо вони не вже включені
    # if MODEL_SEARCH_PATHS:
    #     discovered_modules = _discover_model_modules()
    #     logging.info(f"Discovered additional modules: {discovered_modules}")

    #     for module in discovered_modules:
    #         if module not in all_modules:
    #             all_modules.append(module)

    # Імпортуємо та реєструємо моделі
    _import_and_register_models(unique_modules)

    # Налаштовуємо всі mappers після завантаження всіх моделей
    # Це вирішує проблеми з циклічними залежностями та відношеннями між моделями
    try:
        configure_mappers()
        logging.info("All SQLAlchemy mappers configured successfully")
    except Exception as e:
        logging.error(f"Error configuring SQLAlchemy mappers: {e}")
        # Тут можна додати більш детальний аналіз помилки, якщо потрібно

    # Логуємо результат
    logging.info(f"Registered {len(_MODELS)} models: {', '.join(_MODELS.keys())}")

    _MODELS_LOADED = True
    return _MODELS


def get_model_by_name(model_name: str) -> Optional[Type[BaseModel]]:
    """
    Отримати модель за її назвою.

    Args:
        model_name: Назва моделі

    Returns:
        Optional[Type[BaseModel]]: Клас моделі або None, якщо модель не знайдена
    """
    global _MODELS

    if not _MODELS_LOADED:
        register_all_models()

    return _MODELS.get(model_name)


def get_all_models() -> Dict[str, Type[BaseModel]]:
    """
    Повертає словник усіх зареєстрованих моделей.

    Returns:
        Dict[str, Type[BaseModel]]: Словник зареєстрованих моделей
    """
    global _MODELS

    if not _MODELS_LOADED:
        register_all_models()

    return _MODELS
