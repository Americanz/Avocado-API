"""
Спрощені універсальні маршрути для API з кастомними відповідями.
"""

from typing import List, Optional, Type, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.base_model import BaseModel as DBBaseModel
from src.core.schemas.base import (
    BaseResponseSchema,
    PaginationParams,
)
from src.core.security.jwt import get_current_user, require_auth
from src.core.schemas.responses import Success, Fail, SuccessExtra

from .сontroller import GenericController


ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseResponseSchema)


def create_api_router(
    controller: GenericController,
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    prefix: str,
    tags: List[str],
    get_controller=None,
    auth_dependency=None,
    admin_dependency=None,
    include_endpoints=None,  # Новий параметр для вибору ендпоінтів
):
    """
    Створити API-маршрути для моделі з кастомними відповідями.

    Args:
        controller: Контролер для обробки запитів
        create_schema: Схема для створення об'єктів
        update_schema: Схема для оновлення об'єктів
        response_schema: Схема для відповіді
        prefix: Префікс для маршрутів
        tags: Теги для маршрутів
        get_controller: Функція для отримання контролера з залежностями
        auth_dependency: Залежність для авторизації
        admin_dependency: Залежність для адміністраторів
        include_endpoints: Список ендпоінтів для включення (доступні: 'list', 'get', 'create', 'update', 'delete', 'bulk')
                          Якщо None - включаються всі ендпоінти

    Returns:
        APIRouter: Маршрутизатор з налаштованими маршрутами
    """
    # Всі можливі ендпоінти для API
    available_endpoints = {"list", "get", "create", "update", "delete", "bulk"}

    # Якщо не вказано, які ендпоінти включити, включаємо всі
    if include_endpoints is None:
        include_endpoints = available_endpoints
    else:
        # Перевіряємо, чи всі вказані ендпоінти є допустимими
        invalid_endpoints = set(include_endpoints) - available_endpoints
        if invalid_endpoints:
            raise ValueError(f"Невідомі ендпоінти: {', '.join(invalid_endpoints)}")

        # Конвертуємо в множину для швидкого пошуку
        include_endpoints = set(include_endpoints)

    router = APIRouter(
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(auth_dependency)] if auth_dependency else [],
    )

    # Залежності для авторизації
    auth_dependency = auth_dependency or require_auth
    admin_dependency = admin_dependency or auth_dependency

    # Якщо передано функцію для отримання контролера, використовуємо її
    if get_controller is None:

        def get_controller(db: AsyncSession = Depends(get_db)):
            return controller.with_db(db)

    # Список всіх об'єктів
    if "list" in include_endpoints:

        @router.get("/")
        async def list_items(
            pagination: PaginationParams = Depends(),
            search: Optional[str] = Query(None, description="Пошуковий запит"),
            controller=Depends(get_controller),
        ):
            """Отримати список об'єктів з пагінацією."""
            total, items = await controller.list(
                page=pagination.page,
                page_size=pagination.limit,
                search_term=search,
            )

            response_items = controller.prepare_responses(items)

            return SuccessExtra(
                data=response_items,
                total=total,
                current=pagination.page,
                size=pagination.limit,
            )

    # Отримання об'єкта за ID
    if "get" in include_endpoints:

        @router.get("/{item_id}")
        async def get_item(
            item_id: UUID = Path(..., description="ID об'єкта"),
            controller=Depends(get_controller),
        ):
            """Отримати об'єкт за ID."""
            item = await controller.get_by_id(item_id)
            if not item:
                return Fail(code="4004", msg="Об'єкт не знайдено")

            response_item = controller.prepare_response(item)
            return Success(data=response_item)

    # Створення об'єкта
    if "create" in include_endpoints:

        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_item(
            item_data: CreateSchemaType,
            controller=Depends(get_controller),
        ):
            """Створити новий об'єкт."""
            try:
                item = await controller.create(item_data)
                response_item = controller.prepare_response(item)
                return Success(data=response_item, msg="Об'єкт успішно створено")
            except Exception as e:
                return Fail(code="4000", msg=f"Помилка при створенні об'єкта: {str(e)}")

    # Оновлення об'єкта (захищений маршрут)
    if "update" in include_endpoints:

        @router.patch("/{item_id}")
        async def update_item(
            item_id: UUID = Path(..., description="ID об'єкта"),
            item_data: UpdateSchemaType = None,
            controller=Depends(get_controller),
            current_user: dict = Depends(get_current_user),
        ):
            """Оновити об'єкт за ID."""
            item = await controller.update(item_id, item_data)
            if not item:
                return Fail(code="4004", msg="Об'єкт не знайдено")

            response_item = controller.prepare_response(item)
            return Success(data=response_item, msg="Об'єкт успішно оновлено")

    # Видалення об'єкта (захищений маршрут)
    if "delete" in include_endpoints:

        @router.delete("/{item_id}")
        async def delete_item(
            item_id: UUID = Path(..., description="ID об'єкта"),
            controller=Depends(get_controller),
            current_user: dict = Depends(get_current_user),
        ):
            """Видалити об'єкт за ID."""
            success = await controller.delete(item_id)
            if not success:
                return Fail(code="4004", msg="Об'єкт не знайдено")

            return Success(data=None, msg="Об'єкт успішно видалено")

    # Масове створення об'єктів (адміністративний маршрут)
    if "bulk" in include_endpoints:

        @router.post("/bulk", dependencies=[Depends(admin_dependency)])
        async def bulk_create_items(
            items_data: List[CreateSchemaType],
            controller=Depends(get_controller),
        ):
            """Масово створити об'єкти."""
            try:
                items = []
                db = await controller.get_db_session()

                for item_data in items_data:
                    item = await controller.crud.create(db, item_data)
                    items.append(item)

                response_items = controller.prepare_responses(items)

                return Success(
                    data=response_items, msg=f"Успішно створено {len(items)} об'єктів"
                )
            except Exception as e:
                return Fail(
                    code="4000",
                    msg=f"Помилка при масовому створенні об'єктів: {str(e)}",
                )

    return router
