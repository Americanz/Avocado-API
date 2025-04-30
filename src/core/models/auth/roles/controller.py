from typing import Dict, List, Optional, Union, Any
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud.crud_base import CRUDBase
from src.core.loader_factory.api_factory.controller import APIController
from .model import Role
from .schemas import RoleCreate, RoleUpdate, RoleRead
from src.core.models.auth.users import User


class RoleController(APIController[Role, RoleCreate, RoleUpdate, RoleRead]):
    """Контролер для управління ролями."""

    def __init__(self, db: AsyncSession = None):
        """
        Ініціалізувати контролер ролей.

        Args:
            db: Сесія бази даних
        """
        super().__init__(
            model=Role,
            response_schema=RoleRead,
            db=db,
            search_fields=["name", "description"],
            default_order_by=["name"],
        )

    async def get_by_name(self, name: str) -> Optional[Role]:
        """
        Отримати роль за ім'ям.

        Args:
            name: Назва ролі

        Returns:
            Об'єкт ролі або None
        """
        return await self.get_by_attribute("name", name)

    async def is_exists(self, name: str) -> bool:
        """
        Перевірити чи існує роль з вказаним ім'ям.

        Args:
            name: Назва ролі

        Returns:
            True якщо роль існує, інакше False
        """
        role = await self.get_by_name(name)
        return role is not None

    async def get_all(self) -> List[Role]:
        """
        Отримати всі ролі.

        Returns:
            Список ролей
        """
        db = await self.get_db_session()
        result = await db.execute(select(Role).order_by(Role.name))
        return result.scalars().all()

    async def update_permissions(
        self, role_id: uuid.UUID, permissions: Dict[str, bool]
    ) -> Optional[Role]:
        """
        Оновити дозволи ролі.

        Args:
            role_id: ID ролі
            permissions: Словник дозволів

        Returns:
            Оновлений об'єкт ролі або None
        """
        db = await self.get_db_session()
        role = await self.get_by_id(role_id)
        if not role:
            return None

        role.permissions = permissions
        await db.commit()
        await db.refresh(role)
        return role

    async def assign_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """
        Призначити роль користувачу.

        Args:
            user_id: ID користувача
            role_id: ID ролі

        Returns:
            True якщо роль призначено, інакше False
        """
        db = await self.get_db_session()
        role = await self.get_by_id(role_id)
        user = await db.get(User, user_id)

        if not role or not user:
            return False

        if role not in user.roles:
            user.roles.append(role)
            await db.commit()

        return True

    async def remove_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """
        Видалити роль у користувача.

        Args:
            user_id: ID користувача
            role_id: ID ролі

        Returns:
            True якщо роль видалено, інакше False
        """
        db = await self.get_db_session()
        role = await self.get_by_id(role_id)
        user = await db.get(User, user_id)

        if not role or not user:
            return False

        if role in user.roles:
            user.roles.remove(role)
            await db.commit()

        return True

    async def get_user_roles(self, user_id: uuid.UUID) -> List[Role]:
        """
        Отримати всі ролі користувача.

        Args:
            user_id: ID користувача

        Returns:
            Список ролей користувача
        """
        db = await self.get_db_session()
        user = await db.get(User, user_id)
        if not user:
            return []

        return user.roles


# Створюємо екземпляр контролера для глобального використання
role_controller = RoleController()
