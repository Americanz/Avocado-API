"""
Pydantic schemas for TransactionProduct model
"""

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class TransactionProductBase(BaseModel):
    """Base schema for TransactionProduct"""

    # Product position in transaction
    position: int = Field(..., description="Product position in transaction")

    # Product details from Poster
    poster_product_id: Optional[int] = Field(None, description="Poster product ID")

    # Pricing and quantity
    count: Decimal = Field(..., description="Product quantity")
    price: Decimal = Field(..., description="Product price per unit")
    sum: Decimal = Field(..., description="Total sum for this product")

    # Tax information
    tax_id: Optional[int] = Field(None, description="Tax ID")
    tax_value: Optional[Decimal] = Field(None, description="Tax amount")
    tax_type: Optional[str] = Field(None, description="Tax type")

    # Link to Poster product catalog
    product: Optional[int] = Field(
        None, description="Link to Poster product catalog"
    )


class TransactionProductCreate(TransactionProductBase):
    """Schema for creating TransactionProduct"""

    transaction_id: int = Field(..., description="Poster transaction ID")

    @field_validator("count", "price", "sum", mode="before")
    @classmethod
    def validate_decimals(cls, v):
        """Convert string/int to Decimal"""
        if v is None:
            return Decimal("0")
        return Decimal(str(v))

    @field_validator("tax_value", mode="before")
    @classmethod
    def validate_tax_value(cls, v):
        """Convert tax value to Decimal or None"""
        if v is None or v == "":
            return None
        return Decimal(str(v))

    # 🚀 Removed individual product validation - too slow!
    # Product validation will be done in batch in TransactionService


class TransactionProductUpdate(TransactionProductBase):
    """Schema for updating TransactionProduct"""

    # All fields are optional for updates
    position: Optional[int] = None
    count: Optional[Decimal] = None
    price: Optional[Decimal] = None
    sum: Optional[Decimal] = None


class TransactionProductResponse(TransactionProductBase):
    """Schema for TransactionProduct response"""

    id: int
    transaction_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionProductFromPosterAPI(BaseModel):
    """Schema for converting Poster API product data to TransactionProduct"""

    # API fields (with different names)
    product_id: Optional[int] = Field(None, alias="product_id")
    product_name: str = Field("", alias="product_name")

    # Quantity and pricing from API
    num: Decimal = Field(Decimal("1"), alias="num")
    product_sum: Decimal = Field(Decimal("0"), alias="product_sum")

    # Tax information
    tax_id: Optional[int] = Field(None, alias="tax_id")
    tax_value: Optional[Decimal] = Field(None, alias="tax_value")
    tax_type: Optional[str] = Field(None, alias="tax_type")

    @field_validator("num", "product_sum", mode="before")
    @classmethod
    def validate_api_decimals(cls, v):
        """Convert API values to Decimal"""
        if v is None:
            return Decimal("0")
        return Decimal(str(v))

    @field_validator("tax_value", mode="before")
    @classmethod
    def validate_api_tax_value(cls, v):
        """Convert tax value to Decimal or None"""
        if v is None or v == "":
            return None
        return Decimal(str(v))

    @field_validator("tax_type", mode="before")
    @classmethod
    def validate_tax_type(cls, v):
        """Convert tax_type to string (API sends it as int)"""
        if v is None:
            return None
        return str(v)

    def to_transaction_product_create(
        self, transaction_id: int, position: int
    ) -> TransactionProductCreate:
        """Convert to TransactionProductCreate schema"""

        # Calculate price from product_sum and num
        calculated_price = self.product_sum / self.num if self.num > 0 else Decimal("0")

        return TransactionProductCreate(
            transaction_id=transaction_id,
            position=position,
            poster_product_id=self.product_id,
            count=self.num,
            price=calculated_price,
            sum=self.product_sum,
            tax_id=self.tax_id,
            tax_value=self.tax_value,
            tax_type=self.tax_type,
            product=self.product_id,  # � Set poster_product_id, validator will check if exists
        )

    class Config:
        populate_by_name = True
