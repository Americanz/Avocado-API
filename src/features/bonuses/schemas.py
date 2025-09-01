from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class BonusAccountBase(BaseModel):
    client_id: UUID = Field(..., description="ID клієнта")
    balance: float = Field(..., description="Баланс бонусів")


class BonusAccountCreate(BonusAccountBase):
    pass


class BonusAccountUpdate(BaseModel):
    balance: Optional[float] = Field(None, description="Новий баланс")


class BonusAccountResponse(BonusAccountBase):
    id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True


class BonusTransactionBase(BaseModel):
    client_id: UUID = Field(..., description="ID клієнта")
    account_id: UUID = Field(..., description="ID бонусного рахунку")
    amount: float = Field(..., description="Сума операції")
    type: str = Field(..., description="Тип операції: 'accrual' або 'debit'")
    description: Optional[str] = Field(None, description="Опис операції")


class BonusTransactionCreate(BonusTransactionBase):
    pass


class BonusTransactionResponse(BonusTransactionBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "BonusAccountBase",
    "BonusAccountCreate",
    "BonusAccountUpdate",
    "BonusAccountResponse",
    "BonusTransactionBase",
    "BonusTransactionCreate",
    "BonusTransactionResponse",
]
