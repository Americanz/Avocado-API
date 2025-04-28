"""
Product repository using the CRUD helper.
"""
from typing import Optional, List, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.crud.crud_helper import create_crud_helper
from src.features.catalog.product.model import Product
from src.features.catalog.product.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

# Create a CRUD helper for the Product model
product_crud_helper = create_crud_helper(
    model=Product,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    response_schema=ProductResponse
)


class ProductRepository:
    """Repository for product operations."""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.crud_helper = product_crud_helper

    async def get_product(self, product_id: str, select_related: Optional[List[str]] = None):
        """Get a product by ID."""
        return await self.crud_helper.get_item(
            db=self.db,
            item_id=product_id,
            select_related=select_related
        )

    async def get_products(
        self,
        page: int = 1,
        limit: int = 10,
        search_term: Optional[str] = None,
        category_id: Optional[str] = None,
        order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None
    ):
        """Get paginated products with filtering options."""
        from src.core.schemas.base import PaginationParams

        search_filter = {}
        if category_id:
            search_filter["category_id"] = category_id

        return await self.crud_helper.get_paginated_items(
            db=self.db,
            pagination=PaginationParams(page=page, limit=limit),
            search_filter=search_filter,
            search_fields=["name", "description", "sku"],
            search_term=search_term,
            order_by=order_by or ["-created_at"],
            select_related=select_related
        )

    async def create_product(self, product_data: ProductCreate):
        """Create a new product."""
        return await self.crud_helper.create_item(
            db=self.db,
            item_in=product_data
        )

    async def update_product(self, product_id: str, product_data: ProductUpdate):
        """Update an existing product."""
        return await self.crud_helper.update_item(
            db=self.db,
            item_id=product_id,
            item_in=product_data
        )

    async def delete_product(self, product_id: str):
        """Delete a product."""
        return await self.crud_helper.delete_item(
            db=self.db,
            item_id=product_id
        )
