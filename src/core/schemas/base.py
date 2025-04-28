"""
Base models for the application.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field, field_validator
from pydantic.functional_validators import BeforeValidator

PyObjectId = TypeVar("PyObjectId", bound=str)


class BaseSchema(PydanticBaseModel):
    """Base schema for all schemas."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            uuid.UUID: lambda id: str(id),
        },
    )


class BaseResponseSchema(BaseSchema):
    """Base schema for all response schemas."""
    
    id: PyObjectId = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    @field_validator("id", mode="before")
    def validate_id(cls, v: Any) -> str:
        """Validate and convert id to string."""
        if isinstance(v, str):
            return v
        if isinstance(v, uuid.UUID):
            return str(v)
        raise ValueError("Invalid id format")


class PaginationParams(BaseSchema):
    """Pagination parameters schema."""
    
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """Calculate skip value for pagination."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseSchema):
    """Base schema for paginated responses."""
    
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int
    
    @field_validator("pages", mode="before")
    def calculate_pages(cls, v: Any, values: Dict[str, Any]) -> int:
        """Calculate total pages."""
        if "total" in values.data and "limit" in values.data:
            total = values.data["total"]
            limit = values.data["limit"]
            return (total + limit - 1) // limit if limit else 0
        return v or 0


class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
