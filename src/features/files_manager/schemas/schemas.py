from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Базова модель для схем Supabase
class SupabaseModel(BaseModel):
    """Base model for Supabase tables"""

    id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Моделі, що відповідають схемам таблиць у Supabase
class FilesManagerBase(SupabaseModel):
    """Base schema for files in Supabase"""

    name: str
    description: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    user_id: Optional[str] = None
    folder: Optional[str] = None
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = None


class FilesManagerCreate(BaseModel):
    """Schema for creating a file record"""

    name: str
    description: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    folder: Optional[str] = None
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = None


class FilesManagerResponse(FilesManagerBase):
    """Schema for file response with all fields"""

    url: Optional[str] = None

    class Config:
        from_attributes = True


class FilesManagerUpdate(BaseModel):
    """Schema for updating a file record"""

    name: Optional[str] = None
    description: Optional[str] = None
    folder: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
