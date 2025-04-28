from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from src.core.schemas.base import BaseSchema, BaseResponseSchema

class CompanyCreate(BaseSchema):
    """Схема для створення компанії."""
    name: str
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True

class CompanyUpdate(BaseSchema):
    """Схема для оновлення компанії."""
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class CompanyResponse(BaseResponseSchema):
    """Схема для відповіді з даними компанії."""
    id: UUID
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
