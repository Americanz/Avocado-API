"""
Schemas for device operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.features.devices.model import DeviceStatus, DeviceType


class DeviceBase(BaseModel):
    """Base schema for device data."""
    
    name: str
    device_id: str
    device_type: DeviceType = DeviceType.MOBILE
    status: DeviceStatus = DeviceStatus.ACTIVE
    platform: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    push_token: Optional[str] = None
    notes: Optional[str] = None
    user_id: Optional[UUID] = None


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    
    name: Optional[str] = None
    device_type: Optional[DeviceType] = None
    status: Optional[DeviceStatus] = None
    platform: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    push_token: Optional[str] = None
    notes: Optional[str] = None
    user_id: Optional[UUID] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        
        from_attributes = True


class DevicePaginationResponse(BaseModel):
    """Schema for paginated device list response."""
    
    total: int
    items: List[DeviceResponse]


class DeviceFilter(BaseModel):
    """Schema for device filtering."""
    
    name: Optional[str] = None
    device_type: Optional[DeviceType] = None
    status: Optional[DeviceStatus] = None
    platform: Optional[str] = None
    user_id: Optional[UUID] = None
