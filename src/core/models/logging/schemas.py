"""
Pydantic schemas for logging
"""

from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from .constants import LogLevel, LogType, LogDetailType


class ApplicationLogBase(BaseModel):
    """Base schema for application logs"""

    message: str
    level: str
    log_type: str
    timestamp: datetime
    module: Optional[str] = None
    detail_type: Optional[str] = None
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    exception_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True,
    }


class ApplicationLogCreate(ApplicationLogBase):
    """Schema for creating log"""

    pass


class ApplicationLogRead(ApplicationLogBase):
    """Schema for reading log"""

    id: str
    stack_trace: Optional[str] = None
    http_log_id: Optional[str] = None

    @field_validator("id", "http_log_id", mode="before")
    def validate_uuid(cls, v: Any) -> str:
        """Validate and convert UUID to string."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, UUID):
            return str(v)
        return str(v)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class HttpLogBase(BaseModel):
    """Base schema for HTTP logs"""

    timestamp: datetime
    is_request: bool
    method: Optional[str] = None
    path: Optional[str] = None
    client_ip: Optional[str] = None
    user_id: Optional[str] = None
    status_code: Optional[int] = None
    processing_time_ms: Optional[float] = None


class HttpLogCreate(HttpLogBase):
    """Schema for creating HTTP log"""

    request_headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    request_body: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None


class HttpLogRead(HttpLogBase):
    """Schema for reading HTTP log"""

    id: str
    request_headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    request_body: Optional[Any] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    related_log_id: Optional[str] = None

    @field_validator("id", "related_log_id", mode="before")
    def validate_uuid(cls, v: Any) -> str:
        """Validate and convert UUID to string."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, UUID):
            return str(v)
        return str(v)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PaginatedBase(BaseModel):
    """Base schema for paginated responses"""

    total: int
    limit: int
    offset: int


class ApplicationLogListResponse(PaginatedBase):
    """Response schema for application logs list"""

    items: List[ApplicationLogRead]


class HttpLogListResponse(PaginatedBase):
    """Response schema for HTTP logs list"""

    items: List[HttpLogRead]


class RequestDetail(BaseModel):
    """Detail of HTTP request"""

    id: str
    timestamp: datetime
    method: str
    path: str
    client_ip: str
    user_id: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, str]] = None
    body: Optional[Any] = None


class ResponseDetail(BaseModel):
    """Detail of HTTP response"""

    id: str
    timestamp: datetime
    status_code: int
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    processing_time_ms: Optional[float] = None


class RequestResponseDetail(BaseModel):
    """Complete request-response pair"""

    request: RequestDetail
    response: Optional[ResponseDetail] = None
