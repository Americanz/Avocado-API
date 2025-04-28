"""
Sync models for data synchronization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,  # Added missing import
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class SyncStatus(str, Enum):
    """Sync status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncDirection(str, Enum):
    """Sync direction enum."""

    UPLOAD = "upload"
    DOWNLOAD = "download"
    BIDIRECTIONAL = "bidirectional"


class SyncLog(BaseModel):
    """SyncLog model for tracking data synchronization."""

    __tablename__ = "sync_logs"

    device_id = Column(String, nullable=True, index=True)
    direction = Column(
        SQLAlchemyEnum(SyncDirection),
        nullable=False,
        default=SyncDirection.BIDIRECTIONAL,
    )
    status = Column(
        SQLAlchemyEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING
    )
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    items_processed = Column(Integer, default=0, nullable=False)
    items_failed = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    sync_metadata = Column(JSON, nullable=True)  # Змінено 'metadata' на 'sync_metadata'

    # Foreign keys
    user_id = Column(PgUUID(as_uuid=True), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<SyncLog {self.id} ({self.status})>"


class SyncItem(BaseModel):
    """SyncItem model for individual items in a sync operation."""

    __tablename__ = "sync_items"

    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    operation = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    status = Column(
        SQLAlchemyEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING
    )
    error_message = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Foreign keys
    sync_log_id = Column(
        PgUUID(as_uuid=True), ForeignKey("sync_logs.id"), nullable=False
    )

    # Relationships
    sync_log = relationship("SyncLog")

    def __repr__(self) -> str:
        return f"<SyncItem {self.entity_type} {self.entity_id} ({self.operation})>"
