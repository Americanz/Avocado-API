"""
Controller for category management.
"""

from typing import  List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.features.catalog.category.model import Category
from src.features.catalog.category.schemas import CategoryCreate, CategoryUpdate


class CategoryController:
    """Controller for handling category-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize category controller with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """
        Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category object or None if not found
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(joinedload(Category.parent))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_subcategories(self, category_id: UUID) -> Optional[Category]:
        """
        Get category by ID including its subcategories hierarchy.

        Args:
            category_id: Category ID

        Returns:
            Category object with subcategories loaded or None if not found
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.subcategories))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        name: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> Tuple[int, List[Category]]:
        """
        Get all categories with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            name: Filter by category name
            parent_id: Filter by parent ID

        Returns:
            Tuple of (total count, list of categories)
        """
        # Base query
        query = select(Category)

        # Apply filters
        conditions = []

        if name:
            conditions.append(Category.name.ilike(f"%{name}%"))

        if parent_id is not None:
            conditions.append(Category.parent_id == parent_id)

        if conditions:
            query = query.where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query
            .offset(skip)
            .limit(limit)
            .order_by(Category.name)
        )

        # Execute query
        result = await self.db.execute(query)
        categories = result.scalars().all()

        return total_count, list(categories)

    async def get_root_categories(self) -> List[Category]:
        """
        Get all root categories (categories without parent).

        Returns:
            List of root categories
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_root_categories_with_children(self) -> List[Category]:
        """
        Get all root categories with their hierarchical subcategories.

        Returns:
            List of root categories with subcategories loaded
        """
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .options(selectinload(Category.subcategories).selectinload(Category.subcategories))
            .order_by(Category.name)
        )
        return list(result.scalars().all())

    async def get_category_path(self, category_id: UUID) -> List[Category]:
        """
        Get the path from root to the specified category.

        Args:
            category_id: Category ID

        Returns:
            List of categories from root to the target category
        """
        path = []
        current_category = await self.get_by_id(category_id)

        while current_category:
            path.insert(0, current_category)

            if current_category.parent_id:
                current_category = await self.get_by_id(current_category.parent_id)
            else:
                break

        return path

    async def create(self, category_data: CategoryCreate) -> Category:
        """
        Create a new category.

        Args:
            category_data: Category data for creation

        Returns:
            Created Category object
        """
        # Create new category
        category = Category(**category_data.model_dump())

        # Add category to database
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def update(self, category_id: UUID, category_data: CategoryUpdate) -> Optional[Category]:
        """
        Update a category.

        Args:
            category_id: Category ID
            category_data: Category data for update

        Returns:
            Updated Category object or None if not found
        """
        # Get category
        category = await self.get_by_id(category_id)
        if not category:
            return None

        # Update category fields
        update_data = category_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(category, field, value)

        # Save changes
        await self.db.commit()
        await self.db.refresh(category)

        return category

    async def delete(self, category_id: UUID) -> bool:
        """
        Delete a category.

        Args:
            category_id: Category ID

        Returns:
            True if deleted, False if not found
        """
        # Get category with subcategories to check if it has children
        category = await self.get_by_id_with_subcategories(category_id)
        if not category:
            return False

        # Check if category has subcategories
        if category.subcategories:
            return False  # Cannot delete category with subcategories

        # Delete category
        await self.db.delete(category)
        await self.db.commit()

        return True

    async def get_category_products_count(self, category_id: UUID) -> int:
        """
        Get the number of products in a category.

        Args:
            category_id: Category ID

        Returns:
            Number of products in the category
        """
        from src.features.catalog.product.model import Product

        result = await self.db.execute(
            select(func.count())
            .select_from(Product)
            .where(Product.category_id == category_id)
        )
        return result.scalar() or 0
