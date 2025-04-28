"""
Schemas for category operations.
"""

from typing import List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CategoryBase(BaseModel):
    """Base schema for category data."""

    name: str
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID

    class Config:
        """Pydantic config."""

        from_attributes = True


class CategoryWithChildren(CategoryResponse):
    """Schema for category with subcategories."""

    subcategories: List["CategoryWithChildren"] = []

    class Config:
        """Pydantic config."""

        from_attributes = True


# Forward reference resolution for recursive model
CategoryWithChildren.model_rebuild()


class CategoryWithParent(CategoryResponse):
    """Schema for category with parent data."""

    parent: Optional[CategoryResponse] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class CategoryWithProducts(CategoryResponse):
    """Schema for category with products count."""

    products_count: int = 0

    class Config:
        """Pydantic config."""

        from_attributes = True


class CategoryTree(BaseModel):
    """Schema for category tree response."""

    categories: List[CategoryWithChildren]


class CategoryPaginationResponse(BaseModel):
    """Schema for paginated category list response."""

    total: int
    items: List[CategoryResponse]
