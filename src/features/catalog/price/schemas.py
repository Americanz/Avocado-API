"""
Schemas for price operations.
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PriceBase(BaseModel):
    """Base schema for price data."""
    
    name: str
    price_value: float
    price_type: str = "regular"
    is_active: bool = True
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None
    product_id: UUID


class PriceCreate(PriceBase):
    """Schema for creating a price."""
    pass


class PriceUpdate(BaseModel):
    """Schema for updating a price."""
    
    name: Optional[str] = None
    price_value: Optional[float] = None
    price_type: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    
    @validator('price_value', pre=True)
    def validate_price(cls, value):
        if value is not None and value < 0:
            raise ValueError("Price value cannot be negative")
        return value
    
    @validator('valid_from', 'valid_to', pre=True)
    def validate_dates(cls, value, values):
        if values.get('valid_from') and values.get('valid_to'):
            if values['valid_from'] > values['valid_to']:
                raise ValueError("Valid from date must be before valid to date")
        return value


class PriceResponse(PriceBase):
    """Schema for price response."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class PriceWithProduct(PriceResponse):
    """Schema for price with product information."""
    
    product_name: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class PricePaginationResponse(BaseModel):
    """Schema for paginated price list response."""
    
    total: int
    items: List[PriceResponse]


class PriceFilter(BaseModel):
    """Schema for price filtering."""
    
    name: Optional[str] = None
    price_type: Optional[str] = None
    product_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    valid_at: Optional[datetime] = None  # Get prices valid at this date
