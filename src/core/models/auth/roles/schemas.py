from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from src.core.schemas.base import BaseSchema


class RoleBase(BaseSchema):
    """Базова схема для ролей."""

    name: str = Field(description="Назва ролі")
    description: Optional[str] = Field(None, description="Опис ролі")
    permissions: Optional[Dict[str, bool]] = Field(None, description="Права доступу")


class RoleCreate(RoleBase):
    """Схема для створення ролі."""

    pass


class RoleUpdate(BaseSchema):
    """Схема для оновлення ролі."""

    name: Optional[str] = Field(None, description="Назва ролі")
    description: Optional[str] = Field(None, description="Опис ролі")
    permissions: Optional[Dict[str, bool]] = Field(None, description="Права доступу")


class RoleRead(RoleBase):
    """Схема для читання ролі."""

    id: str = Field(description="ID ролі")

    @field_validator("id", mode="before")
    def validate_id(cls, v: Any) -> str:
        """Validate and convert id to string."""
        if isinstance(v, str):
            return v
        if isinstance(v, UUID):
            return str(v)
        return str(v)

    model_config = {
        "from_attributes": True,
    }


class RoleWithUsers(RoleRead):
    """Схема ролі з користувачами."""

    users: List["UserRead"] = Field(
        default_factory=list, description="Користувачі з цією роллю"
    )


class UserBase(BaseModel):
    """Базова схема для користувачів (для уникнення циклічних імпортів)."""

    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserRead(UserBase):
    """Скорочена схема користувача для відображення в ролі."""

    id: str

    @field_validator("id", mode="before")
    def validate_id(cls, v: Any) -> str:
        """Validate and convert id to string."""
        if isinstance(v, str):
            return v
        if isinstance(v, UUID):
            return str(v)
        return str(v)

    model_config = {
        "from_attributes": True,
    }


# Вирішення циклічної залежності
RoleWithUsers.model_rebuild()


# Схеми для роботи з дозволами
class PermissionAssignment(BaseModel):
    """Схема для призначення дозволів ролі."""

    permissions: Dict[str, bool] = Field(description="Словник з дозволами")


# Схеми для управління користувачами у ролі
class UserRoleAssignment(BaseModel):
    """Схема для призначення ролі користувачу."""

    user_id: str = Field(description="ID користувача")
    role_id: str = Field(description="ID ролі")
