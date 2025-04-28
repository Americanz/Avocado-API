from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select, func, Column, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import desc, asc
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload

from src.core.models.base_model import BaseModel as DBBaseModel

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовий CRUD класс для операцій з моделями SQLAlchemy
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model
        self.pk_attr = inspect(model).primary_key[0].name

    def _get_primary_key_field(self) -> Column:
        """Отримати атрибут первинного ключа моделі"""
        return getattr(self.model, self.pk_attr)

    async def get(
        self,
        db: AsyncSession,
        id: Union[int, str, UUID],
        select_related: Optional[List[str]] = None,
    ) -> Optional[ModelType]:
        """
        Отримати об'єкт за ID

        Args:
            db: Сесія бази даних
            id: Ідентифікатор об'єкту
            select_related: Список відношень для завантаження (еквівалент prefetch_related)

        Returns:
            Об'єкт моделі або None
        """
        query = select(self.model).where(self._get_primary_key_field() == id)

        # Додаємо eager loading для відношень
        if select_related:
            for relation in select_related:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_attribute(
        self,
        db: AsyncSession,
        attr_name: str,
        attr_value: Any,
        select_related: Optional[List[str]] = None,
    ) -> Optional[ModelType]:
        """
        Отримати об'єкт за значенням атрибуту

        Args:
            db: Сесія бази даних
            attr_name: Назва атрибуту
            attr_value: Значення атрибуту
            select_related: Список відношень для завантаження

        Returns:
            Об'єкт моделі або None
        """
        if not hasattr(self.model, attr_name):
            raise ValueError(
                f"Модель {self.model.__name__} не має атрибуту {attr_name}"
            )

        query = select(self.model).where(getattr(self.model, attr_name) == attr_value)

        if select_related:
            for relation in select_related:
                query = query.options(selectinload(getattr(self.model, relation)))

        result = await db.execute(query)
        return result.scalars().first()

    async def list(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 100,
        search_filter=None,
        order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        search_fields: Optional[List[str]] = None,
        search_term: Optional[str] = None,
    ) -> tuple[int, List[ModelType]]:
        """
        Отримати список об'єктів з пагінацією, пошуком та сортуванням

        Args:
            db: Сесія бази даних
            page: Номер сторінки (починаючи з 1)
            page_size: Розмір сторінки
            search_filter: SQLAlchemy фільтр для пошуку
            order_by: Список полів для сортування (з - для зворотнього порядку)
            select_related: Список відношень для завантаження
            search_fields: Поля для текстового пошуку
            search_term: Текст для пошуку в полях search_fields

        Returns:
            Кортеж (загальна кількість, список об'єктів)
        """
        # Базові запити
        query = select(self.model)
        count_query = select(func.count(self._get_primary_key_field()))

        # Додаємо eager loading для відношень
        if select_related:
            for relation in select_related:
                query = query.options(selectinload(getattr(self.model, relation)))

        # Додаємо фільтри пошуку
        if search_filter is not None:
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Додаємо текстовий пошук по вказаних полях
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    attr = getattr(self.model, field)
                    search_conditions.append(attr.ilike(f"%{search_term}%"))

            if search_conditions:
                search_expr = or_(*search_conditions)
                query = query.where(search_expr)
                count_query = count_query.where(search_expr)

        # Отримуємо загальну кількість
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Додаємо сортування
        if order_by:
            order_clauses = []
            for field in order_by:
                if field.startswith("-"):
                    field_name = field[1:]
                    if hasattr(self.model, field_name):
                        order_clauses.append(desc(getattr(self.model, field_name)))
                else:
                    if hasattr(self.model, field):
                        order_clauses.append(asc(getattr(self.model, field)))

            if order_clauses:
                query = query.order_by(*order_clauses)

        # Додаємо пагінацію
        if page_size > 0:
            query = query.offset((page - 1) * page_size).limit(page_size)

        # Виконуємо запит
        result = await db.execute(query)
        items = result.scalars().all()

        return total_count, list(items)

    async def create(
        self,
        db: AsyncSession,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        exclude: Optional[set] = None,
    ) -> ModelType:
        """
        Створити новий об'єкт

        Args:
            db: Сесія бази даних
            obj_in: Дані для створення об'єкту
            exclude: Поля для виключення

        Returns:
            Створений об'єкт
        """
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump(
                exclude_unset=True, exclude_none=True, exclude=exclude or set()
            )
        else:
            obj_data = {k: v for k, v in obj_in.items() if k not in (exclude or set())}

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Optional[ModelType] = None,
        id: Optional[Union[int, str, UUID]] = None,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        exclude: Optional[set] = None,
    ) -> Optional[ModelType]:
        """
        Оновити об'єкт

        Args:
            db: Сесія бази даних
            db_obj: Об'єкт для оновлення (якщо вже отримано)
            id: ID об'єкта для оновлення (використовується, якщо db_obj не вказано)
            obj_in: Дані для оновлення
            exclude: Поля для виключення

        Returns:
            Оновлений об'єкт або None, якщо об'єкт не знайдено
        """
        if db_obj is None:
            if id is None:
                raise ValueError("Потрібно вказати або db_obj, або id")
            db_obj = await self.get(db, id)

        if db_obj is None:
            return None

        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(
                exclude_unset=True, exclude_none=True, exclude=exclude or set()
            )
        else:
            update_data = {
                k: v for k, v in obj_in.items() if k not in (exclude or set())
            }

        # Оновлюємо об'єкт
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db: AsyncSession,
        *,
        id: Optional[Union[int, str, UUID]] = None,
        db_obj: Optional[ModelType] = None,
    ) -> bool:
        """
        Видалити об'єкт

        Args:
            db: Сесія бази даних
            id: ID об'єкта для видалення
            db_obj: Об'єкт для видалення (якщо вже отримано)

        Returns:
            True якщо об'єкт видалено, False якщо об'єкт не знайдено
        """
        if db_obj is None:
            if id is None:
                raise ValueError("Потрібно вказати або db_obj, або id")
            db_obj = await self.get(db, id)

        if db_obj is None:
            return False

        await db.delete(db_obj)
        await db.commit()
        return True

    async def count(
        self,
        db: AsyncSession,
        search_filter=None,
    ) -> int:
        """
        Підрахувати кількість об'єктів

        Args:
            db: Сесія бази даних
            search_filter: SQLAlchemy фільтр

        Returns:
            Кількість об'єктів
        """
        query = select(func.count(self._get_primary_key_field()))

        if search_filter is not None:
            query = query.where(search_filter)

        result = await db.execute(query)
        return result.scalar() or 0

    async def exists(
        self,
        db: AsyncSession,
        id: Union[int, str, UUID],
    ) -> bool:
        """
        Перевірити чи існує об'єкт з вказаним ID

        Args:
            db: Сесія бази даних
            id: ID об'єкта

        Returns:
            True якщо об'єкт існує, інакше False
        """
        query = select(func.count(self._get_primary_key_field())).where(
            self._get_primary_key_field() == id
        )
        result = await db.execute(query)
        return (result.scalar() or 0) > 0

    async def bulk_create(
        self,
        db: AsyncSession,
        objs_in: List[Union[CreateSchemaType, Dict[str, Any]]],
        exclude: Optional[set] = None,
    ) -> List[ModelType]:
        """
        Створити кілька об'єктів за один запит

        Args:
            db: Сесія бази даних
            objs_in: Список даних для створення об'єктів
            exclude: Поля для виключення

        Returns:
            Список створених об'єктів
        """
        db_objs = []

        for obj_in in objs_in:
            if isinstance(obj_in, BaseModel):
                obj_data = obj_in.model_dump(
                    exclude_unset=True, exclude_none=True, exclude=exclude or set()
                )
            else:
                obj_data = {
                    k: v for k, v in obj_in.items() if k not in (exclude or set())
                }

            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)
            db.add(db_obj)

        await db.commit()

        # Оновлюємо об'єкти для отримання ID та інших згенерованих значень
        for db_obj in db_objs:
            await db.refresh(db_obj)

        return db_objs
