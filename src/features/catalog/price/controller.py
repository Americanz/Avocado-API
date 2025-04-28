"""
Controller for price management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.features.catalog.price.model import Price
from src.features.catalog.price.schemas import PriceCreate, PriceUpdate
from src.features.catalog.product.model import Product


class PriceController:
    """Controller for handling price-related business logic."""

    def __init__(self, db: AsyncSession):
        """
        Initialize price controller with database session.

        Args:
            db: Database session
        """
        self.db = db

    async def get_by_id(self, price_id: UUID) -> Optional[Price]:
        """
        Get price by ID.

        Args:
            price_id: Price ID

        Returns:
            Price object or None if not found
        """
        result = await self.db.execute(
            select(Price)
            .where(Price.id == price_id)
            .options(joinedload(Price.product))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filter_params: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, List[Price]]:
        """
        Get all prices with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filter_params: Optional filter parameters

        Returns:
            Tuple of (total count, list of prices)
        """
        # Base query with product join for filtering
        query = select(Price).options(joinedload(Price.product))
        
        # Apply filters if provided
        if filter_params:
            conditions = []
            
            if filter_params.get("name"):
                conditions.append(Price.name.ilike(f"%{filter_params['name']}%"))
                
            if filter_params.get("price_type"):
                conditions.append(Price.price_type == filter_params["price_type"])
                
            if filter_params.get("product_id"):
                conditions.append(Price.product_id == filter_params["product_id"])
                
            if "is_active" in filter_params:
                conditions.append(Price.is_active == filter_params["is_active"])
                
            if filter_params.get("min_value") is not None:
                conditions.append(Price.price_value >= filter_params["min_value"])
                
            if filter_params.get("max_value") is not None:
                conditions.append(Price.price_value <= filter_params["max_value"])
                
            if filter_params.get("valid_at") is not None:
                valid_at = filter_params["valid_at"]
                # Price is valid if:
                # 1. valid_from <= valid_at AND
                # 2. (valid_to IS NULL OR valid_to >= valid_at)
                valid_date_conditions = [
                    Price.valid_from <= valid_at,
                    or_(
                        Price.valid_to.is_(None),
                        Price.valid_to >= valid_at
                    )
                ]
                conditions.append(and_(*valid_date_conditions))
            
            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Price.valid_from.desc())
        
        # Execute query
        result = await self.db.execute(query)
        prices = result.scalars().all()
        
        return total_count, list(prices)

    async def get_by_product(
        self, 
        product_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        price_type: Optional[str] = None,
        include_inactive: bool = False,
        valid_at: Optional[datetime] = None
    ) -> Tuple[int, List[Price]]:
        """
        Get prices by product.

        Args:
            product_id: Product ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            price_type: Filter by price type (optional)
            include_inactive: Whether to include inactive prices
            valid_at: Get prices valid at this date (optional)

        Returns:
            Tuple of (total count, list of prices)
        """
        # Base query
        query = (
            select(Price)
            .where(Price.product_id == product_id)
            .options(joinedload(Price.product))
        )
        
        # Apply additional filters
        conditions = []
        
        if price_type:
            conditions.append(Price.price_type == price_type)
            
        if not include_inactive:
            conditions.append(Price.is_active == True)
            
        if valid_at:
            valid_date_conditions = [
                Price.valid_from <= valid_at,
                or_(
                    Price.valid_to.is_(None),
                    Price.valid_to >= valid_at
                )
            ]
            conditions.append(and_(*valid_date_conditions))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Price.valid_from.desc())
        
        # Execute query
        result = await self.db.execute(query)
        prices = result.scalars().all()
        
        return total_count, list(prices)

    async def get_current_price(
        self,
        product_id: UUID,
        price_type: str = "regular"
    ) -> Optional[Price]:
        """
        Get the current price for a product.

        Args:
            product_id: Product ID
            price_type: Price type to retrieve

        Returns:
            Current Price object or None if not found
        """
        now = datetime.utcnow()
        
        # Query for current valid price
        query = (
            select(Price)
            .where(
                and_(
                    Price.product_id == product_id,
                    Price.price_type == price_type,
                    Price.is_active == True,
                    Price.valid_from <= now,
                    or_(
                        Price.valid_to.is_(None),
                        Price.valid_to >= now
                    )
                )
            )
            .options(joinedload(Price.product))
            .order_by(Price.valid_from.desc())
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, price_data: PriceCreate) -> Price:
        """
        Create a new price.

        Args:
            price_data: Price data for creation

        Returns:
            Created Price object
        """
        # Create new price
        price = Price(**price_data.model_dump())
        
        # Add price to database
        self.db.add(price)
        await self.db.commit()
        await self.db.refresh(price)
        
        return price

    async def update(self, price_id: UUID, price_data: PriceUpdate) -> Optional[Price]:
        """
        Update a price.

        Args:
            price_id: Price ID
            price_data: Price data for update

        Returns:
            Updated Price object or None if not found
        """
        # Get price
        price = await self.get_by_id(price_id)
        if not price:
            return None
        
        # Update price fields
        update_data = price_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(price, field, value)
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(price)
        
        return price

    async def delete(self, price_id: UUID) -> bool:
        """
        Delete a price.

        Args:
            price_id: Price ID

        Returns:
            True if deleted, False if not found
        """
        # Get price
        price = await self.get_by_id(price_id)
        if not price:
            return False
        
        # Delete price
        await self.db.delete(price)
        await self.db.commit()
        
        return True

    async def deactivate(self, price_id: UUID) -> Optional[Price]:
        """
        Deactivate a price.

        Args:
            price_id: Price ID

        Returns:
            Updated Price object or None if not found
        """
        # Get price
        price = await self.get_by_id(price_id)
        if not price:
            return None
        
        # Set end date to now if not already set
        if not price.valid_to:
            price.valid_to = datetime.utcnow()
        
        # Deactivate
        price.is_active = False
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(price)
        
        return price

    async def prepare_price_with_product(self, price: Price) -> Dict[str, Any]:
        """
        Prepare price response with product name.

        Args:
            price: Price object

        Returns:
            Price dict with product name
        """
        price_dict = {
            "id": price.id,
            "name": price.name,
            "price_value": price.price_value,
            "price_type": price.price_type,
            "is_active": price.is_active,
            "valid_from": price.valid_from,
            "valid_to": price.valid_to,
            "product_id": price.product_id,
            "created_at": price.created_at,
            "updated_at": price.updated_at,
            "product_name": price.product.name if price.product else None
        }
        
        return price_dict
