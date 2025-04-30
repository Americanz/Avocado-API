"""
Utility functions for connecting CRUD operations with base response schemas.
"""
from typing import Any, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crud.crud_base import CRUDBase

from src.core.models.base_model import BaseModel as DBBaseModel
from src.core.schemas.base import BaseResponseSchema, PaginatedResponse, PaginationParams

ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseResponseSchema)


class CRUDHelper(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """
    Helper class that connects CRUD operations with response schemas.
    """

    def __init__(
        self,
        crud: CRUDBase[ModelType, CreateSchemaType, UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
    ):
        self.crud = crud
        self.response_schema = response_schema

    async def get_item(
        self,
        db: AsyncSession,
        item_id: Union[int, str, UUID],
        select_related: Optional[List[str]] = None,
    ) -> Optional[ResponseSchemaType]:
        """Get item by ID and convert to response schema."""
        db_item = await self.crud.get(db, item_id, select_related=select_related)
        if db_item is None:
            return None
        return self.response_schema.model_validate(db_item)

    async def get_item_by_attribute(
        self,
        db: AsyncSession,
        attr_name: str,
        attr_value: Any,
        select_related: Optional[List[str]] = None,
    ) -> Optional[ResponseSchemaType]:
        """Get item by attribute and convert to response schema."""
        db_item = await self.crud.get_by_attribute(
            db, attr_name, attr_value, select_related=select_related
        )
        if db_item is None:
            return None
        return self.response_schema.model_validate(db_item)

    async def get_paginated_items(
        self,
        db: AsyncSession,
        pagination: PaginationParams,
        search_filter=None,
        order_by: Optional[List[str]] = None,
        select_related: Optional[List[str]] = None,
        search_fields: Optional[List[str]] = None,
        search_term: Optional[str] = None,
    ) -> PaginatedResponse:
        """Get paginated items and convert to response schema."""
        total, items = await self.crud.list(
            db,
            page=pagination.page,
            page_size=pagination.limit,
            search_filter=search_filter,
            order_by=order_by,
            select_related=select_related,
            search_fields=search_fields,
            search_term=search_term,
        )

        response_items = [self.response_schema.model_validate(item) for item in items]

        return PaginatedResponse(
            items=response_items,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=0,  # Will be calculated by the validator
        )

    async def create_item(
        self,
        db: AsyncSession,
        item_in: CreateSchemaType,
        exclude: Optional[set] = None,
    ) -> ResponseSchemaType:
        """Create item and convert to response schema."""
        db_item = await self.crud.create(db, item_in, exclude=exclude)
        return self.response_schema.model_validate(db_item)

    async def update_item(
        self,
        db: AsyncSession,
        item_id: Union[int, str, UUID],
        item_in: UpdateSchemaType,
        exclude: Optional[set] = None,
    ) -> Optional[ResponseSchemaType]:
        """Update item and convert to response schema."""
        db_item = await self.crud.update(
            db, id=item_id, obj_in=item_in, exclude=exclude
        )
        if db_item is None:
            return None
        return self.response_schema.model_validate(db_item)

    async def delete_item(
        self,
        db: AsyncSession,
        item_id: Union[int, str, UUID],
    ) -> Optional[ResponseSchemaType]:
        """Delete item and convert to response schema."""
        db_item = await self.crud.remove(db, id=item_id)
        if db_item is None:
            return None
        return self.response_schema.model_validate(db_item)


# Factory function to create CRUD helpers
def create_crud_helper(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
) -> CRUDHelper[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]:
    """
    Create a CRUD helper for a specific model and schemas.

    Args:
        model: SQLAlchemy model
        create_schema: Schema for creating items
        update_schema: Schema for updating items
        response_schema: Schema for responses (must be a subclass of BaseResponseSchema)

    Returns:
        CRUDHelper instance
    """
    crud = CRUDBase(model)
    return CRUDHelper(crud, response_schema)
