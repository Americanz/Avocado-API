from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr


class CredentialsSchema(BaseModel):
    user_name: str = Field(alias="userName", description="username")
    password: str = Field(description="password")

    class Config:
        populate_by_name = True

# OTP схеми
class RequestOTPSchema(BaseModel):
    email: EmailStr = Field(description="Email address")


class VerifyOTPSchema(BaseModel):
    email: EmailStr = Field(description="Email address")
    otp: str = Field(description="OTP code", min_length=6, max_length=6)

# JWT схеми
class JWTOut(BaseModel):
    access_token: Annotated[str | None, Field(alias="token", description="Request a token")] = None
    refresh_token: Annotated[str | None, Field(alias="refreshToken", description="Refresh token")] = None

    class Config:
        populate_by_name = True

class JWTPayload(BaseModel):
    data: dict
    iat: datetime
    exp: datetime

    class Config:
        populate_by_name = True

__all__ = [
    "CredentialsSchema",
    "JWTOut",
    "JWTPayload",
    "RequestOTPSchema",
    "VerifyOTPSchema",
]
