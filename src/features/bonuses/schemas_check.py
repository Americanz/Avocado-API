from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


class CheckItem(BaseModel):
    product_id: UUID = Field(..., description="ID товару")
    quantity: int = Field(..., description="Кількість")
    price: float = Field(..., description="Ціна за одиницю")


class CheckRequest(BaseModel):
    client_id: UUID = Field(..., description="ID клієнта")
    items: List[CheckItem] = Field(..., description="Список товарів")
    total_amount: float = Field(..., description="Загальна сума чеку")


class CheckResponse(BaseModel):
    client_id: UUID
    bonuses_accrued: float
    details: List[dict]
