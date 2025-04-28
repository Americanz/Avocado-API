"""
Route models for route management.
"""

from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class RouteStatus(str, Enum):
    """Route status enum."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Route(BaseModel):
    """Route model for delivery/visit routes."""

    __tablename__ = "routes"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLAlchemyEnum(RouteStatus), nullable=False, default=RouteStatus.PLANNED
    )
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    user_id = Column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    def __repr__(self) -> str:
        return f"<Route {self.name}>"


class RoutePoint(BaseModel):
    """Route point model for stops on a route."""

    __tablename__ = "route_points"

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    sequence = Column(Integer, nullable=False, default=0)
    planned_arrival = Column(DateTime, nullable=True)
    planned_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    actual_departure = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    route_id = Column(PgUUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    client_id = Column(PgUUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<RoutePoint {self.name} ({self.sequence})>"
