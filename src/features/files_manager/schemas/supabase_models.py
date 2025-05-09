"""
Generated Pydantic models for Supabase tables.
This file was auto-generated by SupabaseIntrospector.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class Files(BaseModel):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    name: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    user_id: Optional[str]
    folder: Optional[str]
    is_public: bool
    metadata: Optional[Dict[str, Any]]


class FilesCreate(BaseModel):
    name: str
    description: Optional[str]
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    user_id: Optional[str]
    folder: Optional[str]
    is_public: bool
    metadata: Optional[Dict[str, Any]]


class FilesUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    user_id: Optional[str]
    folder: Optional[str]
    is_public: Optional[bool]
    metadata: Optional[Dict[str, Any]]


class Users(BaseModel):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str


class UsersCreate(BaseModel):
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    role: str


class UsersUpdate(BaseModel):
    email: Optional[str]
    name: Optional[str]
    avatar_url: Optional[str]
    role: Optional[str]


class Categories(BaseModel):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    name: str
    slug: str
    parent_id: Optional[str]


class CategoriesCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[str]


class CategoriesUpdate(BaseModel):
    name: Optional[str]
    slug: Optional[str]
    parent_id: Optional[str]

