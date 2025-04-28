import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Базова схема товарної позиції
class ProductSaleBase(BaseModel):
    product_code: str
    product_name: str
    ukt_zed_code: Optional[str] = None
    barcode: Optional[str] = None
    receipt_numbers: Optional[str] = None
    operation_type: str
    price: float
    quantity: float
    amount: float
    receipts_count: int
    tax_name: Optional[str] = None
    tax_rate: Optional[str] = None
    additional_fee: float = 0
    discount_amount: float = 0
    markup_amount: float = 0
    total_amount: float
    sale_date: datetime.date
    sale_datetime: Optional[datetime.datetime] = None
    shift_number: Optional[int] = None
    fiscal_number: Optional[str] = None
    register_address: Optional[str] = None
    excise_stamp: Optional[str] = None
    payment_type: Optional[str] = None
    is_return: bool = False
    check_link: Optional[str] = None


# Схема для створення товарної позиції
class ProductSaleCreate(ProductSaleBase):
    report_id: UUID


# Схема для відповіді
class ProductSaleResponse(ProductSaleBase):
    id: UUID
    report_id: UUID
    date_created: datetime.datetime

    model_config = {
        "from_attributes": True
    }  # Розкоментовано для правильної роботи з ORM об'єктами


class ProductSaleUpdate(ProductSaleBase):
    id: UUID
    report_id: UUID
    updated_fields: dict
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


# Схема для фільтрації товарних позицій
class ProductSaleFilter(BaseModel):
    report_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# Схема для агрегованої статистики
class ProductSaleStats(BaseModel):
    total_products: int
    total_quantity: float
    total_amount: float
    sales_by_date: dict
    top_products: List[dict]
