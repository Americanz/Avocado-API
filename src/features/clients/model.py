"""
Client models for customer-related entities.
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


# Enum for client type
class ClientType(str, enum.Enum):
    """Client type enum."""

    INDIVIDUAL = "individual"
    COMPANY = "company"


# Enum for client status
class ClientStatus(str, enum.Enum):
    """Client status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class Client(BaseModel):
    """Client model."""

    __tablename__ = "clients"

    # Налаштування для generic_routes
    use_generic_routes = True
    search_fields = ["name", "email", "phone", "code", "tax_id"]
    default_order_by = ["name"]

    name = Column(String, nullable=False, index=True)
    type = Column(Enum(ClientType), nullable=False, default=ClientType.INDIVIDUAL)
    status = Column(Enum(ClientStatus), nullable=False, default=ClientStatus.ACTIVE)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    code = Column(String, nullable=True, index=True)
    tax_id = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    balance = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=True)
    client_metadata = Column(
        JSON, nullable=True
    )  # Changed from JSONB to JSON for SQLite compatibility
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)

    # Додаємо зв'язок з контактами
    contacts = relationship(
        "ClientContact", backref="client", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Client {self.name}>"


class ClientContact(BaseModel):
    """Client contact model."""

    __tablename__ = "client_contacts"

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    position = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<ClientContact {self.first_name} {self.last_name}>"


class ClientGroup(BaseModel):
    """Client group model."""

    __tablename__ = "client_groups"

    # Налаштування для generic_routes
    use_generic_routes = True
    search_fields = ["name", "description"]
    default_order_by = ["name"]

    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    discount = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Додаємо зв'язок з клієнтами через групи
    clients = relationship("Client", secondary="client_group_members", backref="groups")

    def __repr__(self) -> str:
        return f"<ClientGroup {self.name}>"


# Association table for client groups
class ClientGroupMember(BaseModel):
    """Client group member model."""

    __tablename__ = "client_group_members"

    group_id = Column(
        UUID(as_uuid=True), ForeignKey("client_groups.id"), primary_key=True
    )
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), primary_key=True)

    def __repr__(self) -> str:
        return f"<ClientGroupMember {self.group_id} - {self.client_id}>"


__all__ = [
    "Client",
    "ClientContact",
    "ClientGroup",
    "ClientGroupMember",
    "ClientType",
    "ClientStatus",
]
