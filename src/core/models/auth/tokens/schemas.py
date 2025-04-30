"""
API token schemas module.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    """Base schema for API token."""

    name: str = Field(..., description="Назва токену для ідентифікації користувачем")
    description: Optional[str] = Field(None, description="Опис токену")
    scopes: Optional[List[str]] = Field(None, description="Права доступу токену")
    expires_at: Optional[datetime] = Field(None, description="Дата та час закінчення терміну дії токену")


class TokenCreate(TokenBase):
    """Schema for creating API token."""

    user_id: Optional[str] = Field(None, description="ID користувача, якому належить токен")


class TokenUpdate(BaseModel):
    """Schema for updating API token."""

    name: Optional[str] = Field(None, description="Назва токену для ідентифікації користувачем")
    description: Optional[str] = Field(None, description="Опис токену")
    scopes: Optional[List[str]] = Field(None, description="Права доступу токену")
    is_active: Optional[bool] = Field(None, description="Чи активний токен")
    expires_at: Optional[datetime] = Field(None, description="Дата та час закінчення терміну дії токену")


class TokenResponse(TokenBase):
    """Schema for API token response."""

    id: str = Field(..., description="ID токену")
    token: str = Field(..., description="API токен для автентифікації")
    user_id: str = Field(..., description="ID користувача, якому належить токен")
    is_active: bool = Field(..., description="Чи активний токен")
    created_at: datetime = Field(..., description="Дата та час створення токену")
    updated_at: datetime = Field(..., description="Дата та час останнього оновлення токену")
    last_used_at: Optional[datetime] = Field(None, description="Дата та час останнього використання токену")
    created_from_ip: Optional[str] = Field(None, description="IP-адреса, з якої був створений токен")

    class Config:
        """Pydantic config."""

        orm_mode = True


class TokenResponseWithoutToken(TokenResponse):
    """Schema for API token response without token value (for security)."""

    token: Optional[str] = Field(None, description="Токен приховано з міркувань безпеки")


__all__ = ["TokenBase", "TokenCreate", "TokenUpdate", "TokenResponse", "TokenResponseWithoutToken"]
