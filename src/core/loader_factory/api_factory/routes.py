"""
Універсальна фабрика API маршрутів для CRUD операцій.
"""

from typing import List, Optional, Type, TypeVar, Set, Callable, Dict
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
from src.core.security.jwt import get_current_user, require_auth, get_current_admin_user
from src.core.schemas.responses import Success, Fail, SuccessExtra

from .controller import APIController


ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseResponseSchema)


def create_api_router(
    controller: APIController,
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    prefix: str,
    tags: List[str],
    get_controller: Optional[Callable] = None,
    auth_dependency=None,
    admin_dependency=None,
    include_public_routes: bool = True,
    include_protected_routes: bool = True,
    include_admin_routes: bool = True,
    include_endpoints: Optional[List[str]] = None,
    protected_endpoints: Optional[List[str]] = None,
) -> APIRouter:
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
        include_public_routes: Включати публічні маршрути (список, отримання)
        include_protected_routes: Включати захищені маршрути (створення, оновлення, видалення)
        include_admin_routes: Включати адміністративні маршрути (масові операції)
        include_endpoints: Список конкретних ендпоінтів, які потрібно включити ("list", "get", "create", "update", "delete", "bulk")
                          Якщо вказано, цей параметр має пріоритет над include_*_routes параметрами
        protected_endpoints: Список ендпоінтів, які потрібно захистити auth_dependency.
                            За замовчуванням ["create", "update", "delete", "bulk"]

    Returns:
        APIRouter: Маршрутизатор з налаштованими маршрутами
    """
    # Визначаємо, які ендпоінти включати на основі параметрів
    endpoints_to_include: Set[str] = set()

    # Якщо передано конкретний список ендпоінтів, використовуємо його
    if include_endpoints:
        endpoints_to_include.update(include_endpoints)
    else:
        # Інакше використовуємо групи ендпоінтів
        if include_public_routes:
            endpoints_to_include.update(["list", "get"])

        if include_protected_routes:
            endpoints_to_include.update(["create", "update", "delete"])

        if include_admin_routes:
            endpoints_to_include.update(["bulk"])

    # Визначаємо, які ендпоінти повинні бути захищені
    default_protected = ["list", "create", "update", "delete", "bulk"]
    endpoints_to_protect = set(
        protected_endpoints if protected_endpoints is not None else default_protected
    )

    # Перевіряємо, чи потрібно захищати маршрутизатор в цілому
    need_router_protection = auth_dependency and any(
        endpoint in endpoints_to_include and endpoint in endpoints_to_protect
        for endpoint in endpoints_to_include
    )

    # Створюємо роутер
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        dependencies=[Depends(auth_dependency)] if need_router_protection else [],
    )

    # Залежності для авторизації
    auth_dependency = auth_dependency or require_auth
    admin_dependency = admin_dependency or get_current_admin_user

    # Якщо передано функцію для отримання контролера, використовуємо її
    if get_controller is None:

        def get_controller(db: AsyncSession = Depends(get_db)):
            return controller.with_db(db)

    # Список всіх об'єктів
    if "list" in endpoints_to_include:
        # Визначаємо, чи потрібна авторизація для list, якщо роутер не захищений глобально
        list_dependencies = (
            [Depends(auth_dependency)]
            if not need_router_protection and "list" in endpoints_to_protect
            else []
        )

        @router.get("/", dependencies=list_dependencies)
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
    if "get" in endpoints_to_include:
        # Визначаємо, чи потрібна авторизація для get, якщо роутер не захищений глобально
        get_dependencies = (
            [Depends(auth_dependency)]
            if not need_router_protection and "get" in endpoints_to_protect
            else []
        )

        @router.get("/{item_id}", dependencies=get_dependencies)
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
    if "create" in endpoints_to_include:
        # Для create не додаємо додаткові залежності, оскільки вони вже додані на рівні роутера
        # або будуть додані через current_user у визначенні функції

        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_item(
            item_data: CreateSchemaType,
            controller=Depends(get_controller),
            current_user: dict = (
                Depends(get_current_user)
                if "create" in endpoints_to_protect and not need_router_protection
                else None
            ),
        ):
            """Створити новий об'єкт."""
            try:
                item = await controller.create(item_data)
                response_item = controller.prepare_response(item)
                return Success(data=response_item, msg="Об'єкт успішно створено")
            except Exception as e:
                return Fail(code="4000", msg=f"Помилка при створенні об'єкта: {str(e)}")

    # Оновлення об'єкта (захищений маршрут)
    if "update" in endpoints_to_include:

        @router.patch("/{item_id}")
        async def update_item(
            item_id: UUID = Path(..., description="ID об'єкта"),
            item_data: UpdateSchemaType = None,
            controller=Depends(get_controller),
            current_user: dict = (
                Depends(get_current_user)
                if "update" in endpoints_to_protect or not need_router_protection
                else Depends(lambda: None)
            ),
        ):
            """Оновити об'єкт за ID."""
            item = await controller.update(item_id, item_data)
            if not item:
                return Fail(code="4004", msg="Об'єкт не знайдено")

            response_item = controller.prepare_response(item)
            return Success(data=response_item, msg="Об'єкт успішно оновлено")

    # Видалення об'єкта (захищений маршрут)
    if "delete" in endpoints_to_include:

        @router.delete("/{item_id}")
        async def delete_item(
            item_id: UUID = Path(..., description="ID об'єкта"),
            controller=Depends(get_controller),
            current_user: dict = (
                Depends(get_current_user)
                if "delete" in endpoints_to_protect or not need_router_protection
                else Depends(lambda: None)
            ),
        ):
            """Видалити об'єкт за ID."""
            success = await controller.delete(item_id)
            if not success:
                return Fail(code="4004", msg="Об'єкт не знайдено")

            return Success(data=None, msg="Об'єкт успішно видалено")

    # Масове створення об'єктів (адміністративний маршрут)
    if "bulk" in endpoints_to_include:

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
