"""
API routes for product management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.logging.providers import get_global_logger
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.security.jwt import require_auth, get_current_admin_user, get_current_user

from src.features.catalog.product.controller import ProductController
from src.features.catalog.category.controller import CategoryController
from src.features.catalog.product.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductWithCategory,
    ProductPaginationResponse,
)

# Отримуємо логер з гарантованим fallback на випадок, якщо глобальний логер не ініціалізовано
logger = get_global_logger()
if logger is None:
    # Створюємо локальний екземпляр логера, якщо глобальний недоступний
    logger = OptimizedLoguruService(db_service=None)

# Створюємо роутери для різних рівнів доступу
protected_router = APIRouter(tags=["products"], dependencies=[Depends(require_auth)])
admin_router = APIRouter(tags=["products"], dependencies=[Depends(get_current_admin_user)])

# Об'єднуємо всі роутери в один для експорту
router = APIRouter(tags=["products"])

# Функція для створення контролера продуктів
def get_product_controller(db: AsyncSession = Depends(get_db)) -> ProductController:
    """Dependency for getting ProductController instance."""
    return ProductController(db)

# Функція для створення контролера категорій
def get_category_controller(db: AsyncSession = Depends(get_db)) -> CategoryController:
    """Dependency for getting CategoryController instance."""
    return CategoryController(db)

# Функція для логування дій
async def log_action(action_type: str, detail: str, current_user=None):
    """Log user action."""
    by_user_id = current_user.get("sub", "0") if current_user else "0"
    logger.info(
        f"Product action: {detail}",
        module="catalog.products",
        data={"action_type": action_type, "by_user_id": by_user_id},
    )

# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні для авторизованих користувачів)
# =========================================================

@protected_router.get("/", response_model=ProductPaginationResponse)
async def list_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by product name"),
    sku: Optional[str] = Query(None, description="Filter by product SKU"),
    barcode: Optional[str] = Query(None, description="Filter by product barcode"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_price: Optional[float] = Query(None, ge=0, description="Filter by minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Filter by maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter products in stock"),
    current_user: dict = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Get list of all products with filtering and pagination.
    """
    filter_params = {}
    if name:
        filter_params["name"] = name
    if sku:
        filter_params["sku"] = sku
    if barcode:
        filter_params["barcode"] = barcode
    if category_id:
        filter_params["category_id"] = category_id
    if is_active is not None:
        filter_params["is_active"] = is_active
    if min_price is not None:
        filter_params["min_price"] = min_price
    if max_price is not None:
        filter_params["max_price"] = max_price
    if in_stock is not None:
        filter_params["in_stock"] = in_stock

    # Get products
    total, products = await controller.get_all(
        skip=skip,
        limit=limit,
        filter_params=filter_params
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"List products (skip={skip}, limit={limit})",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": products
    }


@protected_router.get("/search", response_model=ProductPaginationResponse)
async def search_products(
    query: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_inactive: bool = Query(False, description="Include inactive products in search results"),
    current_user: dict = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Search products by name, SKU, barcode, or description.
    """
    # Search products
    total, products = await controller.search(
        search_term=query,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Search products: '{query}'",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": products
    }


@protected_router.get("/category/{category_id}", response_model=ProductPaginationResponse)
async def get_products_by_category(
    category_id: UUID = Path(..., description="The ID of the category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    include_inactive: bool = Query(False, description="Include inactive products"),
    current_user: dict = Depends(get_current_user),
    product_controller: ProductController = Depends(get_product_controller),
    category_controller: CategoryController = Depends(get_category_controller),
):
    """
    Get products by category.
    """
    # Check if category exists
    category = await category_controller.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Get products for this category
    total, products = await product_controller.get_by_category(
        category_id=category_id,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get products by category: {category_id}",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": products
    }


@protected_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID = Path(..., description="The ID of the product to get"),
    current_user: dict = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Get a specific product by ID.
    """
    product = await controller.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get product: {product_id}",
        current_user=current_user,
    )

    return product


@protected_router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str = Path(..., description="The SKU of the product"),
    current_user: dict = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Get a specific product by SKU.
    """
    product = await controller.get_by_sku(sku)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get product by SKU: {sku}",
        current_user=current_user,
    )

    return product


@protected_router.get("/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str = Path(..., description="The barcode of the product"),
    current_user: dict = Depends(get_current_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Get a specific product by barcode.
    """
    product = await controller.get_by_barcode(barcode)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get product by barcode: {barcode}",
        current_user=current_user,
    )

    return product


# =========================================================
# АДМІНІСТРАТИВНІ ЕНДПОІНТИ (доступні тільки для адміністраторів)
# =========================================================

@admin_router.post(
    "/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED
)
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(get_current_admin_user),
    product_controller: ProductController = Depends(get_product_controller),
    category_controller: CategoryController = Depends(get_category_controller),
):
    """
    Create a new product.
    Admin access required.
    """
    # Check if SKU is already in use
    if product_data.sku:
        existing_product = await product_controller.get_by_sku(product_data.sku)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )

    # Check if barcode is already in use
    if product_data.barcode:
        existing_product = await product_controller.get_by_barcode(product_data.barcode)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with barcode '{product_data.barcode}' already exists"
            )

    # Check if category exists if specified
    if product_data.category_id:
        category = await category_controller.get_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Create product
    product = await product_controller.create(product_data)

    # Log action
    await log_action(
        action_type="CREATE",
        detail=f"Create product: {product.name}",
        current_user=current_user,
    )

    return product


@admin_router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_data: ProductUpdate,
    product_id: UUID = Path(..., description="The ID of the product to update"),
    current_user: dict = Depends(get_current_admin_user),
    product_controller: ProductController = Depends(get_product_controller),
    category_controller: CategoryController = Depends(get_category_controller),
):
    """
    Update a product.
    Admin access required.
    """
    # Check if product exists
    product = await product_controller.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Check if SKU is already in use by another product
    if product_data.sku and product_data.sku != product.sku:
        existing_product = await product_controller.get_by_sku(product_data.sku)
        if existing_product and existing_product.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{product_data.sku}' already exists"
            )

    # Check if barcode is already in use by another product
    if product_data.barcode and product_data.barcode != product.barcode:
        existing_product = await product_controller.get_by_barcode(product_data.barcode)
        if existing_product and existing_product.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with barcode '{product_data.barcode}' already exists"
            )

    # Check if category exists if specified
    if product_data.category_id:
        category = await category_controller.get_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Update product
    updated_product = await product_controller.update(product_id, product_data)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update product: {product_id}",
        current_user=current_user,
    )

    return updated_product


@admin_router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_product_stock(
    quantity_change: int,
    product_id: UUID = Path(..., description="The ID of the product to update"),
    current_user: dict = Depends(get_current_admin_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Update product stock quantity.
    Admin access required.
    """
    # Check if product exists
    product = await controller.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Update stock
    updated_product = await controller.update_stock(product_id, quantity_change)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update product stock: {product_id} ({quantity_change})",
        current_user=current_user,
    )

    return updated_product


@admin_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID = Path(..., description="The ID of the product to delete"),
    current_user: dict = Depends(get_current_admin_user),
    controller: ProductController = Depends(get_product_controller),
):
    """
    Delete a product.
    Admin access required.
    """
    # Check if product exists and delete it
    success = await controller.delete(product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Log action
    await log_action(
        action_type="DELETE",
        detail=f"Delete product: {product_id}",
        current_user=current_user,
    )

    return None

# Об'єднання всіх роутерів
router.include_router(protected_router)
router.include_router(admin_router)
