"""
Модуль виявлення та автоматичної генерації API маршрутів для моделей.

Цей модуль сканує зареєстровані моделі та створює для них стандартні CRUD API маршрути.
"""

import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
import logging

from fastapi import APIRouter

from src.core.models.base_model import BaseModel
from src.core.schemas.base import BaseResponseSchema
from src.core.security.jwt import require_auth, get_current_admin_user

# Імпорт універсальних компонентів API
from src.core.loader_factory.api_factory.controller import create_controller
from src.core.loader_factory.api_factory.routes import create_api_router

# Імпорт конфігурації модулів
from src.core.loader_factory.registry_factory.config import REGISTERED_MODULES

# Логер
from src.core.models.logging.providers import get_logger as get_global_logger

logger = get_global_logger()

if logger is None:
    logger = logging.getLogger(__name__)


# Реєстр схем для кожної моделі
_SCHEMA_REGISTRY: Dict[str, Dict[str, Type[Any]]] = {}


def register_schema(model_name: str, schema_type: str, schema_class: Type[Any]) -> None:
    """
    Реєструє схему для моделі.

    Args:
        model_name: Назва моделі
        schema_type: Тип схеми ('create', 'update', 'response')
        schema_class: Клас схеми
    """
    if model_name not in _SCHEMA_REGISTRY:
        _SCHEMA_REGISTRY[model_name] = {}

    _SCHEMA_REGISTRY[model_name][schema_type] = schema_class


def get_schema_for_model(model_name: str, schema_type: str) -> Optional[Type[Any]]:
    """
    Повертає зареєстровану схему для моделі.

    Args:
        model_name: Назва моделі
        schema_type: Тип схеми ('create', 'update', 'response')

    Returns:
        Optional[Type[Any]]: Клас схеми або None
    """
    if model_name in _SCHEMA_REGISTRY and schema_type in _SCHEMA_REGISTRY[model_name]:
        return _SCHEMA_REGISTRY[model_name][schema_type]
    return None


def discover_schemas_in_module(module_path: str) -> None:
    """
    Виявляє схеми в модулі та реєструє їх.

    Args:
        module_path: Шлях до модуля
    """
    try:
        module = importlib.import_module(module_path)

        # Отримуємо назву моделі з шляху модуля
        parts = module_path.split(".")
        if len(parts) > 0:
            # Отримуємо останню частину шляху і переводимо в CamelCase
            model_name_parts = parts[-1].split("_")
            model_name = "".join(part.capitalize() for part in model_name_parts)
        else:
            model_name = "Unknown"

        # Знаходимо схеми
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseResponseSchema)
                and obj != BaseResponseSchema
            ):
                if name.endswith("Response"):
                    register_schema(model_name, "response", obj)
                elif name.endswith("Create"):
                    register_schema(model_name, "create", obj)
                elif name.endswith("Update"):
                    register_schema(model_name, "update", obj)

    except Exception as e:
        logger.error(f"Помилка при виявленні схем у модулі {module_path}: {e}")


def create_api_router_for_model(
    model_class: Type[BaseModel],
    prefix: str,
    tags: List[str],
    auth_dependency=require_auth,
    admin_dependency=get_current_admin_user,
    public_routes: bool = False,
) -> Optional[APIRouter]:
    """
    Створює API маршрутизатор для моделі.

    Args:
        model_class: Клас моделі
        prefix: API префікс для маршрутів
        tags: Теги OpenAPI
        auth_dependency: Залежність для авторизації
        admin_dependency: Залежність для адміністративних маршрутів
        public_routes: Чи повинні маршрути бути публічними

    Returns:
        Optional[APIRouter]: Створений маршрутизатор або None у разі помилки
    """
    model_name = model_class.__name__

    try:
        # Знаходимо схеми для моделі
        response_schema = get_schema_for_model(model_name, "response")
        create_schema = get_schema_for_model(model_name, "create")
        update_schema = get_schema_for_model(model_name, "update")

        if not all([response_schema, create_schema, update_schema]):
            logger.warning(
                f"Не вдалося знайти всі необхідні схеми для моделі {model_name}"
            )
            return None

        # Створюємо контролер
        controller = create_controller(
            model=model_class,
            response_schema=response_schema,
            search_fields=getattr(model_class, "search_fields", None),
            default_order_by=getattr(model_class, "default_order_by", None),
            select_related=getattr(model_class, "select_related", None),
        )

        # Визначаємо залежності маршрутів
        route_dependency = None if public_routes else auth_dependency

        # Створюємо маршрутизатор
        router = create_api_router(
            controller=controller,
            create_schema=create_schema,
            update_schema=update_schema,
            response_schema=response_schema,
            prefix=prefix,
            tags=tags,
            auth_dependency=route_dependency,
            admin_dependency=admin_dependency,
            # Визначаємо типи маршрутів на основі public_routes
            include_public_routes=True,
            include_protected_routes=not public_routes,
            include_admin_routes=True,
        )

        logger.info(
            f"Створено API маршрутизатор для моделі {model_name} з префіксом {prefix}"
        )
        return router

    except Exception as e:
        logger.error(f"Помилка при створенні маршрутизатора для {model_name}: {e}")
        return None


def discover_and_create_generic_routes(api_router: APIRouter) -> None:
    """
    Автоматично знаходить моделі, для яких можна створити API маршрути.

    Args:
        api_router: Головний API маршрутизатор
    """
    # Спочатку виявляємо та реєструємо схеми в усіх модулях
    for module_path in REGISTERED_MODULES.keys():
        # Шукаємо схеми в модулі schemas.py в кожному зареєстрованому модулі
        schema_module_path = f"{module_path}.schemas"
        discover_schemas_in_module(schema_module_path)

    # Тепер створюємо маршрути для всіх моделей з повними схемами
    # Импортируем get_all_models внутри функции, чтобы избежать циклической зависимости
    from src.core.loader_factory.registry_factory.registry import get_all_models

    for model_name, model_class in get_all_models().items():
        # Перевіряємо, чи є в моделі маркер використання API маршрутів
        if (
            not hasattr(model_class, "use_generic_routes")
            or not model_class.use_generic_routes
        ):
            continue

        # Знаходимо схеми для моделі
        if (
            get_schema_for_model(model_name, "response")
            and get_schema_for_model(model_name, "create")
            and get_schema_for_model(model_name, "update")
        ):

            # Знаходимо API префікс для моделі
            prefix = None
            module_path = model_class.__module__

            # Шукаємо прямий модуль моделі в зареєстрованих
            direct_module = ".".join(
                module_path.split(".")[:-1]
            )  # видаляємо ".model" з кінця

            for registered_module, api_prefix in REGISTERED_MODULES.items():
                if direct_module == registered_module or module_path.startswith(
                    registered_module
                ):
                    prefix = api_prefix
                    break

            if prefix:
                # Визначаємо теги OpenAPI
                tags = [prefix.strip("/").split("/")[-1]]

                # Визначаємо публічність маршрутів
                public_routes = (
                    hasattr(model_class, "public_routes") and model_class.public_routes
                )

                # Створюємо та додаємо маршрутизатор
                router = create_api_router_for_model(
                    model_class=model_class,
                    prefix=prefix,
                    tags=tags,
                    public_routes=public_routes,
                )

                if router:
                    api_router.include_router(router)
                    logger.info(
                        f"Додано API маршрутизатор для {model_name} з префіксом {prefix}"
                    )
