"""
Controller for product management.
"""

from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.crud.crud_base import CRUDBase
from src.features.catalog.product.model import Product
from src.features.catalog.product.schemas import ProductCreate, ProductUpdate
from src.features.catalog.category.model import Category


class ProductController(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """Controller for handling product-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize product controller with database session.

        Args:
            db: Database session
        """
        super().__init__(Product)
        self.db = db

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product object or None if not found
        """
        return await self.get(self.db, product_id, select_related=["category"])

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product object or None if not found
        """
        return await self.get_by_attribute(
            self.db, "sku", sku, select_related=["category"]
        )

    async def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """
        Get product by barcode.

        Args:
            barcode: Product barcode

        Returns:
            Product object or None if not found
        """
        return await self.get_by_attribute(
            self.db, "barcode", barcode, select_related=["category"]
        )

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filter_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, List[Product]]:
        """
        Get all products with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_params: Optional filter parameters

        Returns:
            Tuple of (total count, list of products)
        """
        # Перетворюємо filter_params у формат, зрозумілий для базового CRUD
        filters = {}
        search_term = None
        order_by = "name"

        if filter_params:
            # Базовi фільтри, які підтримуються CRUD.list
            if filter_params.get("name"):
                search_term = filter_params["name"]

            if filter_params.get("category_id"):
                filters["category_id"] = filter_params["category_id"]

            if "is_active" in filter_params:
                filters["is_active"] = filter_params["is_active"]

            # Складні фільтри, які потребують додаткових умов
            custom_filters = []

            if filter_params.get("sku"):
                custom_filters.append(Product.sku.ilike(f"%{filter_params['sku']}%"))

            if filter_params.get("barcode"):
                custom_filters.append(
                    Product.barcode.ilike(f"%{filter_params['barcode']}%")
                )

            if filter_params.get("min_price") is not None:
                custom_filters.append(Product.price >= filter_params["min_price"])

            if filter_params.get("max_price") is not None:
                custom_filters.append(Product.price <= filter_params["max_price"])

            if filter_params.get("in_stock") is True:
                custom_filters.append(Product.stock_quantity > 0)

            # Додаємо складні фільтри до параметрів
            filters["_custom_filters"] = custom_filters

        # Підготовка параметрів для базового CRUD
        page = (skip // limit) + 1 if limit else 1
        page_size = limit
        # Підтримка складних фільтрів
        search_filter = None
        if filters.get("_custom_filters"):
            from sqlalchemy import and_

            search_filter = and_(*filters["_custom_filters"])
        # Використовуємо базовий CRUD.list
        return await self.list(
            self.db,
            page=page,
            page_size=page_size,
            search_filter=search_filter,
            order_by=[order_by] if order_by else None,
            search_fields=["name", "sku", "barcode", "description"],
            search_term=search_term,
            select_related=["category"],
        )

    async def get_by_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[int, List[Product]]:
        """
        Get products by category.

        Args:
            category_id: Category ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive products

        Returns:
            Tuple of (total count, list of products)
        """
        filters = {"category_id": category_id}

        if not include_inactive:
            filters["is_active"] = True

        return await self.list(
            self.db,
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="name",
            select_related=["category"],
        )

    async def search(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[int, List[Product]]:
        """
        Search products by name, SKU, or barcode.

        Args:
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive products

        Returns:
            Tuple of (total count, list of products)
        """
        filters = {}

        if not include_inactive:
            filters["is_active"] = True

        return await self.list(
            self.db,
            skip=skip,
            limit=limit,
            search_term=search_term,
            filters=filters,
            search_fields=["name", "sku", "barcode", "description"],
            order_by="name",
            select_related=["category"],
        )

    async def create(self, product_data: ProductCreate) -> Product:
        """
        Create a new product.

        Args:
            product_data: Product data for creation

        Returns:
            Created Product object
        """
        return await super().create(self.db, product_data)

    async def update(
        self, product_id: UUID, product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Update a product.

        Args:
            product_id: Product ID
            product_data: Product data for update

        Returns:
            Updated Product object or None if not found
        """
        return await super().update(self.db, product_id, product_data)

    async def delete(self, product_id: UUID) -> bool:
        """
        Delete a product.

        Args:
            product_id: Product ID

        Returns:
            True if deleted, False if not found
        """
        return await self.remove(self.db, product_id)

    async def update_stock(
        self, product_id: UUID, quantity_change: int
    ) -> Optional[Product]:
        """
        Update product stock quantity.

        Args:
            product_id: Product ID
            quantity_change: Amount to add (positive) or subtract (negative) from stock

        Returns:
            Updated Product object or None if not found
        """
        # Get product
        product = await self.get_by_id(product_id)
        if not product:
            return None

        # Update stock quantity
        product.stock_quantity += quantity_change

        # Ensure stock quantity is not negative
        if product.stock_quantity < 0:
            product.stock_quantity = 0

        # Save changes
        await self.db.commit()
        await self.db.refresh(product)

        return product

    async def prepare_product_with_category(
        self, product: Product
    ) -> "ProductWithCategory":
        """
        Prepare product response with category name using Pydantic schema.

        Args:
            product: Product object

        Returns:
            ProductWithCategory Pydantic schema
        """
        from src.features.catalog.product.schemas import ProductWithCategory

        return ProductWithCategory(
            id=product.id,
            name=product.name,
            description=product.description,
            sku=product.sku,
            barcode=product.barcode,
            price=product.price,
            cost_price=product.cost_price,
            tax_rate=product.tax_rate,
            is_active=product.is_active,
            stock_quantity=product.stock_quantity,
            min_stock_quantity=product.min_stock_quantity,
            category_id=product.category_id,
            created_at=product.created_at,
            updated_at=product.updated_at,
            category_name=product.category.name if product.category else None,
        )
