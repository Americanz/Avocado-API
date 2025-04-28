"""
User schemas for request and response validation.
"""

from typing import Optional, List, Any, Union
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from src.core.schemas.base import BaseResponseSchema, BaseSchema


class RoleInfo(BaseSchema):
    """Schema for role information."""

    id: str
    name: str
    description: Optional[str] = None

    @field_validator("id", mode="before")
    def validate_id(cls, v: Any) -> str:
        """Validate and convert id to string."""
        if isinstance(v, str):
            return v
        if hasattr(v, "__str__"):
            return str(v)
        return v


class UserBase(BaseSchema):
    """Base schema for user data."""

    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)
    roles: Optional[List[Union[str, UUID]]] = Field(
        default_factory=list, description="List of role IDs to assign"
    )


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    roles: Optional[List[Union[str, UUID]]] = None


class UserResponse(UserBase, BaseResponseSchema):
    """Schema for user response."""

    roles: List[RoleInfo] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }


class UserLogin(BaseSchema):
    """Schema for user login."""

    email: str  # Changed from EmailStr to str to be more flexible
    password: str

    # Allow either "username" or "email" as field name
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Support 'username' field as alias for 'email'."""
        if isinstance(obj, dict) and "username" in obj and "email" not in obj:
            obj = obj.copy()
            obj["email"] = obj.pop("username")
        return super().model_validate(obj, **kwargs)


class TokenResponse(BaseSchema):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserRoleAssignment(BaseSchema):
    """Schema for assigning/removing roles to/from users."""

    user_id: UUID
    role_id: UUID


class UserRolesUpdate(BaseSchema):
    """Schema for updating user roles."""

    role_ids: List[UUID] = Field(
        default_factory=list, description="List of role IDs to assign"
    )
