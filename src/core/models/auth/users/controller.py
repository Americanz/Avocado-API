"""
Оновлений контролер користувачів з коректною серіалізацією.
"""

from datetime import timedelta
from typing import List, Optional, Dict, Any, Union
import uuid
import json

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import TypeAdapter

from src.config import settings
from src.core.database.connection import get_db
from src.core.security.jwt import create_access_token
from src.core.security.password import hash_password, verify_password

from src.core.models.auth.users.model import User
from src.core.models.auth.users.schemas import (
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.core.models.auth.roles.model import Role

# Додаємо імпорт GenericController
from src.core.loader_factory.api_factory.controller import APIController


class UserController(APIController[User, UserCreate, UserUpdate, UserResponse]):
    """Контролер для керування користувачами."""

    def __init__(
        self,
        db: AsyncSession = None,
    ):
        """
        Ініціалізувати контролер користувачів.

        Args:
            db: Сесія бази даних
        """
        super().__init__(
            model=User,
            response_schema=UserResponse,
            db=db,
            search_fields=["email", "username", "first_name", "last_name"],
            default_order_by=["email"],
            select_related=["role"],  # Змінено з "roles" на "role"
        )

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Отримати користувача за email.

        Args:
            email: Email користувача

        Returns:
            Optional[User]: Користувач або None
        """
        return await self.get_by_attribute("email", email)

    async def authenticate(
        self, email: str, password: str, request: Optional[Request] = None
    ) -> Optional[User]:
        """
        Автентифікувати користувача.

        Args:
            email: Email користувача
            password: Пароль користувача
            request: Об'єкт запиту FastAPI

        Returns:
            Optional[User]: Користувач, якщо автентифікація успішна, інакше None
        """
        user = await self.get_by_email(email)
        if not user:
            return None

        if not verify_password(password, user.password):
            return None

        return user

    async def create(
        self,
        obj_in: Union[UserCreate, Dict[str, Any]],
        exclude: Optional[set] = None,
        request: Optional[Request] = None,
    ) -> User:
        """
        Створити нового користувача.

        Args:
            obj_in: Дані для створення користувача
            exclude: Поля для виключення
            request: Об'єкт запиту FastAPI

        Returns:
            User: Створений користувач

        Raises:
            HTTPException: Якщо користувач з таким email вже існує
        """
        # Якщо obj_in - це словник, перетворюємо його в об'єкт UserCreate
        if isinstance(obj_in, dict):
            user_data = UserCreate(**obj_in)
        else:
            user_data = obj_in

        # Перевірити, чи існує користувач з таким email
        existing_user = await self.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувач з таким email вже існує",
            )

        # Хешувати пароль
        user_dict = user_data.model_dump(exclude={"password", "roles"})
        user_dict["password"] = hash_password(user_data.password)

        # Створити користувача через CRUD
        db = await self.get_db_session()
        db_obj = self.model(**user_dict)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # Призначити ролі, якщо вказані
        if hasattr(user_data, "roles") and user_data.roles:
            await self.assign_roles(db_obj.id, user_data.roles)

        return db_obj

    async def update(
        self,
        id: Union[uuid.UUID, str],
        obj_in: Union[UserUpdate, Dict[str, Any]],
        exclude: Optional[set] = None,
        request: Optional[Request] = None,
    ) -> Optional[User]:
        """
        Оновити користувача.

        Args:
            id: ID користувача
            obj_in: Дані для оновлення
            exclude: Поля для виключення
            request: Об'єкт запиту FastAPI

        Returns:
            Optional[User]: Оновлений користувач або None
        """
        # Отримати користувача
        user = await self.get_by_id(id)
        if not user:
            return None

        # Якщо obj_in - це словник, перетворюємо його в об'єкт UserUpdate
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True, exclude={"roles"})

        # Хешувати пароль, якщо наданий
        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])

        # Оновити користувача через CRUD
        db = await self.get_db_session()
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Оновити ролі, якщо вказані
        if (
            isinstance(obj_in, UserUpdate)
            and hasattr(obj_in, "roles")
            and obj_in.roles is not None
        ):
            await self.set_user_roles(user.id, obj_in.roles)

        return user

    def create_access_token_for_user(self, user: User) -> TokenResponse:
        """
        Створити токен доступу для користувача.

        Args:
            user: Користувач

        Returns:
            TokenResponse: Відповідь з токеном доступу та даними користувача
        """
        # Створити дані для токена
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "is_superuser": user.is_superuser,
        }

        # Створити токен доступу
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Підготувати відповідь з токеном
        user_data = self.prepare_user_response(user)

        # Використовуємо TypeAdapter для безпечної серіалізації
        adapter = TypeAdapter(UserResponse)
        user_response = adapter.validate_python(user_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response,
        )

    # Методи для роботи з ролями

    async def get_user_role(self, user_id: Union[str, uuid.UUID]) -> Optional[Role]:
        """
        Отримати роль користувача.

        Args:
            user_id: ID користувача

        Returns:
            Optional[Role]: Роль користувача або None
        """
        user = await self.get_by_id(str(user_id))
        if not user:
            return None

        return user.role

    async def assign_role(
        self, user_id: Union[str, uuid.UUID], role_id: Union[str, uuid.UUID]
    ) -> bool:
        """
        Призначити роль користувачу.

        Args:
            user_id: ID користувача
            role_id: ID ролі

        Returns:
            bool: True, якщо роль призначено, False у разі помилки
        """
        # Перетворити строкові ID в UUID, якщо потрібно
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except (ValueError, TypeError):
                return False

        if isinstance(role_id, str):
            try:
                role_id = uuid.UUID(role_id)
            except (ValueError, TypeError):
                return False

        # Отримати користувача та роль
        user = await self.get_by_id(str(user_id))
        db = await self.get_db_session()
        role = await db.get(Role, role_id)

        if not user or not role:
            return False

        # Призначити роль
        user.set_role(role)
        await db.commit()
        return True

    async def remove_role(self, user_id: Union[str, uuid.UUID]) -> bool:
        """
        Видалити роль у користувача.

        Args:
            user_id: ID користувача

        Returns:
            bool: True, якщо роль видалено, False у разі помилки
        """
        # Перетворити строкові ID в UUID, якщо потрібно
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except (ValueError, TypeError):
                return False

        # Отримати користувача
        user = await self.get_by_id(str(user_id))
        if not user:
            return False

        # Видалити роль
        user.remove_role()
        db = await self.get_db_session()
        await db.commit()
        return True

    async def assign_roles(
        self, user_id: Union[str, uuid.UUID], role_ids: List[Union[str, uuid.UUID]]
    ) -> bool:
        """
        Призначити роль користувачу (перша роль зі списку).
        Метод збережено для зворотної сумісності.

        Args:
            user_id: ID користувача
            role_ids: Список ID ролей

        Returns:
            bool: True, якщо роль призначено, False у разі помилки
        """
        if not role_ids:
            return True

        # Використовуємо лише перший ID з списку
        return await self.assign_role(user_id, role_ids[0])

    async def set_user_roles(
        self, user_id: Union[str, uuid.UUID], role_ids: List[Union[str, uuid.UUID]]
    ) -> bool:
        """
        Встановити роль користувача (використовує першу роль зі списку).
        Метод збережено для зворотної сумісності.

        Args:
            user_id: ID користувача
            role_ids: Список ID ролей (використовується лише перший)

        Returns:
            bool: True, якщо операція успішна, False у разі помилки
        """
        if not role_ids:
            return await self.remove_role(user_id)

        # Використовуємо лише перший ID з списку
        return await self.assign_role(user_id, role_ids[0])

    async def has_role(self, user_id: Union[str, uuid.UUID], role_name: str) -> bool:
        """
        Перевірити, чи користувач має певну роль.

        Args:
            user_id: ID користувача
            role_name: Назва ролі

        Returns:
            bool: True, якщо користувач має роль, False у протилежному випадку
        """
        user = await self.get_by_id(str(user_id))
        if not user:
            return False

        return user.has_role(role_name)

    async def has_permission(
        self, user_id: Union[str, uuid.UUID], permission_name: str
    ) -> bool:
        """
        Перевірити, чи користувач має певний дозвіл.

        Args:
            user_id: ID користувача
            permission_name: Назва дозволу

        Returns:
            bool: True, якщо користувач має дозвіл, False у протилежному випадку
        """
        user = await self.get_by_id(str(user_id))
        if not user:
            return False

        return user.has_permission(permission_name)

    def prepare_user_response(self, user: User) -> Dict[str, Any]:
        """
        Підготувати дані користувача для відповіді.

        Args:
            user: Об'єкт користувача

        Returns:
            Dict[str, Any]: Дані користувача для відповіді
        """
        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": (
                [
                    {
                        "id": str(role.id),
                        "name": role.name,
                        "description": (
                            role.description if hasattr(role, "description") else None
                        ),
                    }
                    for role in [user.role]
                    if user.role
                ]
                if hasattr(user, "role") and user.role
                else []
            ),
        }


def get_user_controller(db: AsyncSession = Depends(get_db)) -> UserController:
    """
    Отримати контролер користувачів.

    Args:
        db: Сесія бази даних

    Returns:
        UserController: Контролер користувачів
    """
    return UserController(db=db)
