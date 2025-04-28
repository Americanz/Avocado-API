"""
Client schemas for request and response validation.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from src.core.schemas.base import BaseResponseSchema, BaseSchema
from src.features.clients.model import ClientStatus, ClientType


class ClientContactBase(BaseSchema):
    """Base schema for client contact data."""

    first_name: str
    last_name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ClientContactCreate(ClientContactBase):
    """Schema for creating a client contact."""

    pass


class ClientContactUpdate(BaseSchema):
    """Schema for updating a client contact."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class ClientContactResponse(ClientContactBase, BaseResponseSchema):
    """Schema for client contact response."""

    client_id: str


class ClientBase(BaseSchema):
    """Base schema for client data."""

    name: str
    type: ClientType = ClientType.INDIVIDUAL
    status: ClientStatus = ClientStatus.ACTIVE
    email: Optional[str] = None
    phone: Optional[str] = None
    code: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    balance: float = 0.0
    discount: Optional[float] = None
    metadata: Optional[Dict] = None
    organization_id: str


class ClientCreate(ClientBase):
    """Schema for creating a client."""

    contacts: Optional[List[ClientContactCreate]] = None


class ClientUpdate(BaseSchema):
    """Schema for updating a client."""

    name: Optional[str] = None
    type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    code: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    balance: Optional[float] = None
    discount: Optional[float] = None
    metadata: Optional[Dict] = None
    organization_id: Optional[str] = None


class ClientResponse(ClientBase, BaseResponseSchema):
    """Schema for client response."""

    contacts: Optional[List[ClientContactResponse]] = None


class ClientGroupBase(BaseSchema):
    """Base schema for client group data."""

    name: str
    description: Optional[str] = None
    discount: Optional[float] = None
    is_active: bool = True
    organization_id: str


class ClientGroupCreate(ClientGroupBase):
    """Schema for creating a client group."""

    client_ids: Optional[List[str]] = None


class ClientGroupUpdate(BaseSchema):
    """Schema for updating a client group."""

    name: Optional[str] = None
    description: Optional[str] = None
    discount: Optional[float] = None
    is_active: Optional[bool] = None
    organization_id: Optional[str] = None
    client_ids: Optional[List[str]] = None


class ClientGroupResponse(ClientGroupBase, BaseResponseSchema):
    """Schema for client group response."""

    clients: Optional[List[ClientResponse]] = None


class ClientListResponse(BaseSchema):
    """Schema for client list response."""

    items: List[ClientResponse]
    total: int
