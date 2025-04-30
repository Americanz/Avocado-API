"""
Схеми даних для автентифікації через Telegram.
"""

from datetime import datetime
from typing import Optional
from pydantic import Field, EmailStr
from src.core.schemas.base import BaseResponseSchema, BaseSchema


class RequestTelegramAuthSchema(BaseSchema):
    """Схема для запиту на автентифікацію через Telegram."""

    email: EmailStr = Field(description="Email користувача для прив'язки")


class VerifyTelegramAuthSchema(BaseSchema):
    """Схема для перевірки автентифікації через Telegram."""

    auth_code: str = Field(description="Код автентифікації з Telegram")
    email: Optional[EmailStr] = Field(
        None, description="Email користувача для підтвердження"
    )


class TelegramCallbackSchema(BaseSchema):
    """Схема для обробки callback від Telegram."""

    auth_code: str = Field(description="Код автентифікації")
    telegram_id: int = Field(description="ID користувача в Telegram")
    telegram_username: Optional[str] = Field(
        None, description="Username користувача в Telegram"
    )
    first_name: Optional[str] = Field(None, description="Ім'я користувача в Telegram")
    last_name: Optional[str] = Field(
        None, description="Прізвище користувача в Telegram"
    )


# Схеми для CRUD операцій
class TelegramAuthBase(BaseSchema):
    """Базова схема для автентифікації через Telegram."""

    email: EmailStr = Field(description="Email користувача")
    auth_code: str = Field(description="Код автентифікації")
    expires_at: datetime = Field(description="Час закінчення терміну дії")


class TelegramAuthCreate(TelegramAuthBase):
    """Схема для створення запису про автентифікацію через Telegram."""

    telegram_id: Optional[int] = Field(None, description="ID користувача в Telegram")
    telegram_username: Optional[str] = Field(
        None, description="Username користувача в Telegram"
    )


class TelegramAuthUpdate(BaseSchema):
    """Схема для оновлення запису про автентифікацію через Telegram."""

    telegram_id: Optional[int] = Field(None, description="ID користувача в Telegram")
    telegram_username: Optional[str] = Field(
        None, description="Username користувача в Telegram"
    )
    is_used: Optional[bool] = Field(
        None, description="Чи був використаний код автентифікації"
    )
    processed_at: Optional[datetime] = Field(None, description="Час обробки коду")


class TelegramAuthResponse(BaseResponseSchema, TelegramAuthBase):
    """Схема для відповіді з інформацією про автентифікацію через Telegram."""

    telegram_id: Optional[int] = Field(None, description="ID користувача в Telegram")
    telegram_username: Optional[str] = Field(
        None, description="Username користувача в Telegram"
    )
    is_used: bool = Field(description="Чи був використаний код автентифікації")
    processed_at: Optional[datetime] = Field(None, description="Час обробки коду")
    is_expired: bool = Field(description="Чи минув термін дії")

    class Config:
        from_attributes = True


# Схема для відповіді з deep link
class TelegramAuthLinkResponse(BaseSchema):
    """Схема для відповіді з посиланням для автентифікації через Telegram."""

    auth_link: str = Field(
        description="Посилання для автентифікації через Telegram бота"
    )
    expires_in: int = Field(description="Час до закінчення терміну дії в секундах")
    email: EmailStr = Field(description="Email, для якого створено посилання")


# Додаємо всі схеми до __all__
__all__ = [
    "RequestTelegramAuthSchema",
    "VerifyTelegramAuthSchema",
    "TelegramCallbackSchema",
    "TelegramAuthBase",
    "TelegramAuthCreate",
    "TelegramAuthUpdate",
    "TelegramAuthResponse",
    "TelegramAuthLinkResponse",
]
