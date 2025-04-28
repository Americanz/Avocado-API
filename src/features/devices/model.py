"""
Device model for device management.
"""

from enum import Enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID


from src.core.models.base_model import BaseModel


class DeviceType(str, Enum):
    """Device type enum."""

    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    POS = "pos"
    OTHER = "other"


class DeviceStatus(str, Enum):
    """Device status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOST = "lost"
    STOLEN = "stolen"


class Device(BaseModel):
    """Device model for device management."""

    __tablename__ = "devices"

    name = Column(String, nullable=False)
    device_id = Column(String, nullable=False, index=True, unique=True)
    device_type = Column(
        SQLAlchemyEnum(DeviceType), nullable=False, default=DeviceType.MOBILE
    )
    status = Column(
        SQLAlchemyEnum(DeviceStatus), nullable=False, default=DeviceStatus.ACTIVE
    )
    platform = Column(String, nullable=True)
    model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    app_version = Column(String, nullable=True)
    push_token = Column(String, nullable=True)
    last_active = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


    # Foreign keys
    user_id = Column(PgUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Device {self.name} ({self.device_id})>"
