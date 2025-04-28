"""
API routes for category management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.connection import get_db
from src.core.models.logging.providers import get_global_logger
from src.core.models.logging.loguru_service import OptimizedLoguruService
from src.core.security.jwt import require_auth, get_current_admin_user, get_current_user

from src.features.catalog.category.controller import CategoryController
from src.features.catalog.category.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithChildren,
    CategoryWithParent,
    CategoryWithProducts,
    CategoryTree,
    CategoryPaginationResponse,
)

# Отримуємо логер з гарантованим fallback на випадок, якщо глобальний логер не ініціалізовано
logger = get_global_logger()
if logger is None:
    # Створюємо локальний екземпляр логера, якщо глобальний недоступний
    logger = OptimizedLoguruService(db_service=None)

# Створюємо роутери для різних рівнів доступу
protected_router = APIRouter(tags=["categories"], dependencies=[Depends(require_auth)])
admin_router = APIRouter(tags=["categories"], dependencies=[Depends(get_current_admin_user)])

# Об'єднуємо всі роутери в один для експорту
router = APIRouter(tags=["categories"])

# Функція для створення контролера категорій
def get_category_controller(db: AsyncSession = Depends(get_db)) -> CategoryController:
    """Dependency for getting CategoryController instance."""
    return CategoryController(db)

# Функція для логування дій
async def log_action(action_type: str, detail: str, current_user=None):
    """Log user action."""
    by_user_id = current_user.get("sub", "0") if current_user else "0"
    logger.info(
        f"Category action: {detail}",
        module="catalog.categories",
        data={"action_type": action_type, "by_user_id": by_user_id},
    )

# =========================================================
# ЗАХИЩЕНІ ЕНДПОІНТИ (доступні для авторизованих користувачів)
# =========================================================

@protected_router.get("/", response_model=CategoryPaginationResponse)
async def list_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Filter by category name"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category ID"),
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get list of all categories with filtering and pagination.
    """
    # Get categories
    total, categories = await controller.get_all(
        skip=skip,
        limit=limit,
        name=name,
        parent_id=parent_id,
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"List categories (skip={skip}, limit={limit})",
        current_user=current_user,
    )

    return {
        "total": total,
        "items": categories
    }


@protected_router.get("/tree", response_model=CategoryTree)
async def get_category_tree(
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get hierarchical tree of all categories.
    """
    # Get root categories with their subcategories
    categories = await controller.get_root_categories_with_children()

    # Log action
    await log_action(
        action_type="READ",
        detail="Get category tree",
        current_user=current_user,
    )

    return {"categories": categories}


@protected_router.get("/root", response_model=List[CategoryResponse])
async def get_root_categories(
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get root categories (top-level categories without parent).
    """
    # Get root categories
    categories = await controller.get_root_categories()

    # Log action
    await log_action(
        action_type="READ",
        detail="Get root categories",
        current_user=current_user,
    )

    return categories


@protected_router.get("/{category_id}", response_model=CategoryWithParent)
async def get_category(
    category_id: UUID = Path(..., description="The ID of the category to get"),
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get a specific category by ID.
    """
    category = await controller.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get category: {category_id}",
        current_user=current_user,
    )

    return category


@protected_router.get("/{category_id}/children", response_model=List[CategoryResponse])
async def get_subcategories(
    category_id: UUID = Path(..., description="The ID of the category to get children for"),
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get subcategories of a specific category.
    """
    # Check if category exists
    category = await controller.get_by_id_with_subcategories(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get subcategories for category: {category_id}",
        current_user=current_user,
    )

    return category.subcategories


@protected_router.get("/{category_id}/path", response_model=List[CategoryResponse])
async def get_category_path(
    category_id: UUID = Path(..., description="The ID of the category to get path for"),
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get the path from root to the specified category.
    """
    # Check if category exists and get path
    categories = await controller.get_category_path(category_id)
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get path for category: {category_id}",
        current_user=current_user,
    )

    return categories


@protected_router.get("/{category_id}/with_products", response_model=CategoryWithProducts)
async def get_category_with_products_count(
    category_id: UUID = Path(..., description="The ID of the category"),
    current_user: dict = Depends(get_current_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Get category with count of products in this category.
    """
    # Check if category exists
    category = await controller.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Get products count
    products_count = await controller.get_category_products_count(category_id)

    # Prepare response
    result = CategoryWithProducts(
        id=category.id,
        name=category.name,
        description=category.description,
        parent_id=category.parent_id,
        products_count=products_count,
    )

    # Log action
    await log_action(
        action_type="READ",
        detail=f"Get category with products count: {category_id}",
        current_user=current_user,
    )

    return result


# =========================================================
# АДМІНІСТРАТИВНІ ЕНДПОІНТИ (доступні тільки для адміністраторів)
# =========================================================

@admin_router.post(
    "/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(get_current_admin_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Create a new category.
    Admin access required.
    """
    # Check if parent category exists if provided
    if category_data.parent_id:
        parent = await controller.get_by_id(category_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

    # Create category
    category = await controller.create(category_data)

    # Log action
    await log_action(
        action_type="CREATE",
        detail=f"Create category: {category.name}",
        current_user=current_user,
    )

    return category


@admin_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_data: CategoryUpdate,
    category_id: UUID = Path(..., description="The ID of the category to update"),
    current_user: dict = Depends(get_current_admin_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Update a category.
    Admin access required.
    """
    # Check if category exists
    category = await controller.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Check if parent category exists if provided
    if category_data.parent_id:
        parent = await controller.get_by_id(category_data.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

        # Prevent circular reference
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )

    # Update category
    updated_category = await controller.update(category_id, category_data)

    # Log action
    await log_action(
        action_type="UPDATE",
        detail=f"Update category: {category_id}",
        current_user=current_user,
    )

    return updated_category


@admin_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID = Path(..., description="The ID of the category to delete"),
    current_user: dict = Depends(get_current_admin_user),
    controller: CategoryController = Depends(get_category_controller),
):
    """
    Delete a category.
    Admin access required.

    Note: Category cannot be deleted if it has subcategories.
    """
    # Check if category exists and delete it
    success = await controller.delete(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or has subcategories"
        )

    # Log action
    await log_action(
        action_type="DELETE",
        detail=f"Delete category: {category_id}",
        current_user=current_user,
    )

    return None

# Об'єднання всіх роутерів
router.include_router(protected_router)
router.include_router(admin_router)
