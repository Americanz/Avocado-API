"""
API routes for price management.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.logging.providers import get_global_logger
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.security.jwt import require_auth, get_current_admin_user, get_current_user

from src.features.catalog.price.controller import PriceController
from src.features.catalog.product.controller import ProductController
from src.features.catalog.price.schemas import (
    PriceCreate,
    PriceUpdate,
    PriceResponse,
    PriceWithProduct,
    PricePaginationResponse,
)

# Отримуємо логер з гарантованим fallback на випадок, якщо глобальний логер не ініціалізовано
logger = get_global_logger()
if logger is None:
    # Створюємо локальний екземпляр логера, якщо глобальний недоступний
    logger = OptimizedLoguruService(db_service=None)

# Створюємо роутери для різних рівнів доступу
protected_router = APIRouter(tags=["prices"], dependencies=[Depends(require_auth)])
admin_router = APIRouter(tags=["prices"], dependencies=[Depends(get_current_admin_user)])

# Об'єднуємо всі роутери в один для експорту
router = APIRouter(tags=["prices"])

# Функція для створення контролера цін
def get_price_controller(db: AsyncSession = Depends(get_db)) -> PriceController:
    """Dependency for getting PriceController instance."""
    return PriceController(db)

# Функція для створення контролера товарів
def get_product_controller(db: AsyncSession = Depends(get_db)) -> ProductController:
    """Dependency for getting ProductController instance."""
    return ProductController(db)

# Функція для логування дій
async def log_action(action_type: str, detail: str, current_user=None):
    """Log user action."""
    by_user_id = current_user.get("sub", "0") if current_user else "0"
    logger.info(
        f"Price action: {detail}",
        module="catalog.prices",
        data={"action_type": action_type, "by_user_id": by_user_id},
    )

# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні для авторизованих користувачів)
# =========================================================

@protected_router.get("/", response_model=PricePaginationResponse)
async def list_prices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by price name"),
    price_type: Optional[str] = Query(None, description="Filter by price type"),
    product_id: Optional[UUID] = Query(None, description="Filter by product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    min_value: Optional[float] = Query(None, ge=0, description="Filter by minimum price value"),
    max_value: Optional[float] = Query(None, ge=0, description="Filter by maximum price value"),
    valid_at: Optional[datetime] = Query(None, description="Filter prices valid at this date"),
    current_user: dict = Depends(get_current_user),
    controller: PriceController = Depends(get_price_controller),
):
    """
    Get list of all prices with filtering and pagination.
    """
    filter_params = {}
    if name:
        filter_params["name"] = name
    if price_type:
        filter_params["price_type"] = price_type
    if product_id:
        filter_params["product_id"] = product_id
    if is_active is not None:
        filter_params["is_active"] = is_active
    if min_value is not None:
        filter_params["min_value"] = min_value
    if max_value is not None:
        filter_params["max_value"] = max_value
    if valid_at:
        filter_params["valid_at"] = valid_at

    # Get prices
    total, prices = await controller.get_all(
        skip=skip,
        limit=limit,
        filter_params=filter_params
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"List prices (skip={skip}, limit={limit})",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": prices
    }


@protected_router.get("/product/{product_id}", response_model=PricePaginationResponse)
async def get_prices_by_product(
    product_id: UUID = Path(..., description="The ID of the product"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    price_type: Optional[str] = Query(None, description="Filter by price type"),
    include_inactive: bool = Query(False, description="Include inactive prices"),
    valid_at: Optional[datetime] = Query(None, description="Filter prices valid at this date"),
    current_user: dict = Depends(get_current_user),
    price_controller: PriceController = Depends(get_price_controller),
    product_controller: ProductController = Depends(get_product_controller),
):
    """
    Get prices by product.
    """
    # Check if product exists
    product = await product_controller.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Get prices for this product
    total, prices = await price_controller.get_by_product(
        product_id=product_id,
        skip=skip,
        limit=limit,
        price_type=price_type,
        include_inactive=include_inactive,
        valid_at=valid_at
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get prices by product: {product_id}",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": prices
    }


@protected_router.get("/product/{product_id}/current", response_model=PriceResponse)
async def get_current_price(
    product_id: UUID = Path(..., description="The ID of the product"),
    price_type: str = Query("regular", description="Price type"),
    current_user: dict = Depends(get_current_user),
    price_controller: PriceController = Depends(get_price_controller),
    product_controller: ProductController = Depends(get_product_controller),
):
    """
    Get current price for a product.
    """
    # Check if product exists
    product = await product_controller.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Get current price
    price = await price_controller.get_current_price(product_id, price_type)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active {price_type} price found for this product"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get current price for product: {product_id}",
        current_user=current_user,
    )

    return price


@protected_router.get("/{price_id}", response_model=PriceResponse)
async def get_price(
    price_id: UUID = Path(..., description="The ID of the price to get"),
    current_user: dict = Depends(get_current_user),
    controller: PriceController = Depends(get_price_controller),
):
    """
    Get a specific price by ID.
    """
    price = await controller.get_by_id(price_id)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get price: {price_id}",
        current_user=current_user,
    )

    return price


# =========================================================
# АДМІНІСТРАТИВНІ ЕНДПОІНТИ (доступні тільки для адміністраторів)
# =========================================================

@admin_router.post(
    "/", response_model=PriceResponse, status_code=status.HTTP_201_CREATED
)
async def create_price(
    price_data: PriceCreate,
    current_user: dict = Depends(get_current_admin_user),
    price_controller: PriceController = Depends(get_price_controller),
    product_controller: ProductController = Depends(get_product_controller),
):
    """
    Create a new price.
    Admin access required.
    """
    # Check if product exists
    product = await product_controller.get_by_id(price_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Validate date range
    if price_data.valid_to and price_data.valid_from > price_data.valid_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid from date must be before valid to date"
        )

    # Create price
    price = await price_controller.create(price_data)

    # Log action
    await log_action(
        action_type="CREATE",
        detail=f"Create price: {price.name} for product {price_data.product_id}",
        current_user=current_user,
    )

    return price


@admin_router.patch("/{price_id}", response_model=PriceResponse)
async def update_price(
    price_data: PriceUpdate,
    price_id: UUID = Path(..., description="The ID of the price to update"),
    current_user: dict = Depends(get_current_admin_user),
    controller: PriceController = Depends(get_price_controller),
):
    """
    Update a price.
    Admin access required.
    """
    # Check if price exists
    price = await controller.get_by_id(price_id)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price not found"
        )

    # Validate date range
    valid_from = price_data.valid_from or price.valid_from
    valid_to = price_data.valid_to or price.valid_to

    if valid_to and valid_from > valid_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid from date must be before valid to date"
        )

    # Update price
    updated_price = await controller.update(price_id, price_data)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update price: {price_id}",
        current_user=current_user,
    )

    return updated_price


@admin_router.patch("/{price_id}/deactivate", response_model=PriceResponse)
async def deactivate_price(
    price_id: UUID = Path(..., description="The ID of the price to deactivate"),
    current_user: dict = Depends(get_current_admin_user),
    controller: PriceController = Depends(get_price_controller),
):
    """
    Deactivate a price.
    Admin access required.
    """
    # Check if price exists
    price = await controller.get_by_id(price_id)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price not found"
        )

    # Deactivate price
    updated_price = await controller.deactivate(price_id)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Deactivate price: {price_id}",
        current_user=current_user,
    )

    return updated_price


@admin_router.delete("/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price(
    price_id: UUID = Path(..., description="The ID of the price to delete"),
    current_user: dict = Depends(get_current_admin_user),
    controller: PriceController = Depends(get_price_controller),
):
    """
    Delete a price.
    Admin access required.
    """
    # Check if price exists and delete it
    success = await controller.delete(price_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Price not found"
        )

    # Log action
    await log_action(
        action_type="DELETE",
        detail=f"Delete price: {price_id}",
        current_user=current_user,
    )

    return None

# Об'єднання всіх роутерів
router.include_router(protected_router)
router.include_router(admin_router)
