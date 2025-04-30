"""
Схеми даних для авторизації та OTP.
"""

from datetime import datetime
from typing import Annotated, Optional
from pydantic import Field, EmailStr
from src.core.schemas.base import BaseResponseSchema
from src.core.schemas.base import BaseSchema


class CredentialsSchema(BaseSchema):
    user_name: str = Field(alias="userName", description="username")
    password: str = Field(description="password")

    class Config:
        populate_by_name = True


# OTP схеми для авторизації
class RequestOTPSchema(BaseSchema):
    email: EmailStr = Field(description="Email address")


class VerifyOTPSchema(BaseSchema):
    email: EmailStr = Field(description="Email address")
    otp: str = Field(description="OTP code", min_length=6, max_length=6)


# JWT схеми
class JWTOut(BaseSchema):
    access_token: Annotated[
        str | None, Field(alias="token", description="Request a token")
    ] = None
    refresh_token: Annotated[
        str | None, Field(alias="refreshToken", description="Refresh token")
    ] = None

    class Config:
        populate_by_name = True


class JWTPayload(BaseSchema):
    data: dict
    iat: datetime
    exp: datetime

    class Config:
        populate_by_name = True


# Схеми для OTP (необхідні для автоматичної генерації CRUD API)
# Перейменовуємо відповідно до стандарту іменування системи
class OTPBase(BaseSchema):
    """Базова схема для OTP."""

    email: EmailStr = Field(..., description="Email користувача")
    code: str = Field(..., description="Код OTP (6 цифр)")
    expires_at: datetime = Field(..., description="Час закінчення терміну дії")


# Схема для запиту на створення OTP
class OTPCreate(OTPBase):
    """Схема для створення OTP."""

    pass


# Схема для запиту на оновлення OTP
class OTPUpdate(BaseSchema):
    """Схема для оновлення OTP."""

    is_used: Optional[bool] = Field(None, description="Чи був використаний OTP")
    processed_at: Optional[datetime] = Field(None, description="Час обробки OTP")


# Схема для відповіді OTP
class OTPResponse(BaseResponseSchema, OTPBase):
    """Схема для відповіді OTP."""

    is_used: bool = Field(..., description="Чи був використаний OTP")
    processed_at: Optional[datetime] = Field(None, description="Час обробки OTP")
    is_expired: bool = Field(..., description="Чи минув термін дії OTP")

    class Config:
        from_attributes = True





# Додаємо всі схеми до __all__, щоб вони були доступні для імпорту
__all__ = [
    "CredentialsSchema",
    "JWTOut",
    "JWTPayload",
    "RequestOTPSchema",
    "VerifyOTPSchema",


    "OTPCreate",
    "OTPUpdate",
    "OTPResponse",
]
