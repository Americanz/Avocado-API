"""
Schemas for product operations.
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Base schema for product data."""
    
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: float = 0.0
    cost_price: Optional[float] = None
    tax_rate: Optional[float] = 0.0
    is_active: bool = True
    stock_quantity: int = 0
    min_stock_quantity: Optional[int] = None
    category_id: Optional[UUID] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    tax_rate: Optional[float] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = None
    min_stock_quantity: Optional[int] = None
    category_id: Optional[UUID] = None
    
    @validator('price', 'cost_price', 'tax_rate', pre=True)
    def validate_prices(cls, value):
        if value is not None and value < 0:
            raise ValueError("Price values cannot be negative")
        return value
    
    @validator('stock_quantity', 'min_stock_quantity', pre=True)
    def validate_quantities(cls, value):
        if value is not None and value < 0:
            raise ValueError("Quantity values cannot be negative")
        return value


class ProductResponse(ProductBase):
    """Schema for product response."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class ProductWithCategory(ProductResponse):
    """Schema for product with category information."""
    
    category_name: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class ProductPaginationResponse(BaseModel):
    """Schema for paginated product list response."""
    
    total: int
    items: List[ProductResponse]


class ProductFilter(BaseModel):
    """Schema for product filtering."""
    
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None  # True to show only products in stock
