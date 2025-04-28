"""
Спрощений універсальний контролер для CRUD операцій.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID


from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud.crud_base import CRUDBase, ModelType, CreateSchemaType, UpdateSchemaType
from src.core.database.connection import get_db
from src.core.models.base_model import BaseModel as DBBaseModel
from src.core.schemas.base import BaseResponseSchema


ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseResponseSchema)


class GenericController(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """Універсальний контролер для CRUD операцій."""

    def __init__(
        self,
        model: Type[ModelType],
        response_schema: Type[ResponseSchemaType],
        db: AsyncSession = None,
        search_fields: List[str] = None,
        default_order_by: List[str] = None,
        select_related: List[str] = None,
    ):
        """
        Ініціалізувати контролер.

        Args:
            model: SQLAlchemy модель
            response_schema: Схема відповіді
            db: Сесія бази даних
            search_fields: Поля для пошуку
            default_order_by: Поля для сортування за замовчуванням
            select_related: Відношення для завантаження за замовчуванням
        """
        self.model = model
        self.response_schema = response_schema
        self.db = db
        self.crud = CRUDBase(model)
        self.search_fields = search_fields or []
        self.default_order_by = default_order_by or []
        self.select_related = select_related or []

    async def get_db_session(self) -> AsyncSession:
        """Отримати сесію бази даних."""
        if self.db:
            return self.db
        raise ValueError("База даних не налаштована, використовуйте with_db")

    def with_db(self, db: AsyncSession) -> "GenericController":
        """Встановити сесію бази даних."""
        self.db = db
        return self

    async def get_by_id(
        self, id: Union[int, str, UUID], select_related: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Отримати об'єкт за ID."""
        db = await self.get_db_session()
        final_select_related = select_related if select_related is not None else self.select_related
        return await self.crud.get(db, id, select_related=final_select_related)

    async def get_by_attribute(
        self, attr_name: str, attr_value: Any, select_related: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """Отримати об'єкт за значенням атрибуту."""
        db = await self.get_db_session()
        final_select_related = select_related if select_related is not None else self.select_related
        return await self.crud.get_by_attribute(db, attr_name, attr_value, select_related=final_select_related)

    async def list(
        self,
        page: int = 1,
        page_size: int = 100,
        search_filter=None,
        order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        search_fields: Optional[List[str]] = None,
        search_term: Optional[str] = None,
    ) -> tuple[int, List[ModelType]]:
        """Отримати список об'єктів з пагінацією."""
        db = await self.get_db_session()
        final_order_by = order_by if order_by is not None else self.default_order_by
        final_select_related = select_related if select_related is not None else self.select_related
        final_search_fields = search_fields if search_fields is not None else self.search_fields

        return await self.crud.list(
            db,
            page=page,
            page_size=page_size,
            search_filter=search_filter,
            order_by=final_order_by,
            select_related=final_select_related,
            search_fields=final_search_fields,
            search_term=search_term,
        )

    async def create(
        self,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        exclude: Optional[set] = None,
    ) -> ModelType:
        """Створити об'єкт."""
        db = await self.get_db_session()
        return await self.crud.create(db, obj_in, exclude=exclude)

    async def update(
        self,
        id: Union[int, str, UUID],
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        exclude: Optional[set] = None,
    ) -> Optional[ModelType]:
        """Оновити об'єкт."""
        db = await self.get_db_session()
        return await self.crud.update(db, id=id, obj_in=obj_in, exclude=exclude)

    async def delete(self, id: Union[int, str, UUID]) -> bool:
        """Видалити об'єкт."""
        db = await self.get_db_session()
        return await self.crud.remove(db, id=id)

    def prepare_response(self, obj: Optional[ModelType]) -> Optional[ResponseSchemaType]:
        """Підготувати відповідь для об'єкта."""
        if obj is None:
            return None
        return self.response_schema.model_validate(obj)

    def prepare_responses(self, objs: List[ModelType]) -> List[ResponseSchemaType]:
        """Підготувати відповіді для списку об'єктів."""
        return [self.prepare_response(obj) for obj in objs]


def create_controller(
    model: Type[ModelType],
    response_schema: Type[ResponseSchemaType],
    db: Optional[AsyncSession] = None,
    search_fields: Optional[List[str]] = None,
    default_order_by: Optional[List[str]] = None,
    select_related: Optional[List[str]] = None,
) -> GenericController:
    """Створити контролер."""
    return GenericController(
        model=model,
        response_schema=response_schema,
        db=db,
        search_fields=search_fields,
        default_order_by=default_order_by,
        select_related=select_related,
    )
