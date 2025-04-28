"""
Base model for all database models in the application with support for generic routes.
"""

import uuid
from datetime import datetime
from typing import ClassVar, List, Optional, Dict, Any

from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.ext.declarative import declared_attr
from src.core.database.connection import Base


# Перевірка, чи використовується SQLite
def is_sqlite(engine):
    return engine.name == "sqlite"


class BaseModel(Base):
    """
    Базова модель для всіх моделей бази даних.
    Визначає спільні поля та поведінку.

    Атрибути класу для налаштування універсальних маршрутів:
    - use_generic_routes: Чи використовувати автоматичну генерацію CRUD API
    - public_routes: Чи повинні маршрути бути публічними (без авторизації)
    - search_fields: Поля для повнотекстового пошуку
    - default_order_by: Поля для сортування за замовчуванням
    - select_related: Відношення для жадібного завантаження (eager loading)
    """

    __abstract__ = True



    # Атрибути для налаштування універсальних маршрутів
    use_generic_routes: ClassVar[bool] = False  # За замовчуванням не використовується
    public_routes: ClassVar[bool] = False  # За замовчуванням маршрути захищені
    search_fields: ClassVar[List[str]] = []  # Поля для пошуку
    default_order_by: ClassVar[List[str]] = []  # Поля для сортування
    select_related: ClassVar[List[str]] = []  # Зв'язки для підвантаження

    # Примітка: id колонку треба створити в кожній моделі за допомогою методу
    # В BaseModel
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Унікальний ідентифікатор запису",
    )
    # після визначення engine

    # Поля для відстеження часу створення та оновлення
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Дата та час створення запису",
    )

    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment="Дата та час останнього оновлення запису",
    )

    # Поле для позначення активних/неактивних записів
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Чи є запис активним",
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Автоматично генерує назву таблиці з назви класу.
        Перетворює CamelCase на snake_case і додає множину (s в кінці).

        Returns:
            str: Назва таблиці
        """
        # Перетворюємо назву класу з CamelCase на snake_case
        parts = []
        for i, char in enumerate(cls.__name__):
            if char.isupper() and i > 0 and not cls.__name__[i - 1].isupper():
                parts.append("_")
            parts.append(char.lower())

        # Додаємо s в кінці для множини
        table_name = "".join(parts)
        if not table_name.endswith("s"):
            table_name += "s"

        return table_name

    def to_dict(self) -> Dict[str, Any]:
        """
        Перетворює об'єкт моделі в словник.

        Returns:
            Dict[str, Any]: Словник з атрибутами моделі
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Перетворення uuid.UUID на рядок
            if isinstance(value, uuid.UUID):
                value = str(value)

            # Перетворення datetime на ISO 8601 рядок
            elif isinstance(value, datetime):
                value = value.isoformat()

            result[column.name] = value

        return result

    @classmethod
    def enable_generic_routes(
        cls,
        search_fields: Optional[List[str]] = None,
        default_order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        public_routes: bool = False,
    ) -> None:
        """
        Вмикає автоматичну генерацію CRUD API для моделі.

        Args:
            search_fields: Поля для повнотекстового пошуку
            default_order_by: Поля для сортування за замовчуванням
            select_related: Відношення для eager loading
            public_routes: Чи повинні маршрути бути публічними
        """
        cls.use_generic_routes = True
        cls.public_routes = public_routes

        if search_fields is not None:
            cls.search_fields = search_fields

        if default_order_by is not None:
            cls.default_order_by = default_order_by

        if select_related is not None:
            cls.select_related = select_related

    def __repr__(self) -> str:
        """
        Рядкове представлення моделі.

        Returns:
            str: Рядкове представлення
        """
        return f"<{self.__class__.__name__}(id={self.id})>"


__all__ = ["BaseModel", "is_sqlite"]
