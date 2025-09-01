"""
Schemas for Poster Spot (establishments)
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class SpotBase(BaseModel):
    """Base schema for Poster spot"""
    spot_id: int
    name: str
    address: Optional[str] = None


class SpotCreate(SpotBase):
    """Schema for creating a spot"""
    raw_data: Optional[Dict[str, Any]] = None


class SpotUpdate(BaseModel):
    """Schema for updating a spot"""
    name: Optional[str] = None
    address: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class SpotResponse(SpotBase):
    """Schema for spot response"""
    id: str
    created_at: str
    updated_at: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True
