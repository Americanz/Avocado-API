"""
Warehouse model for organization management.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class Warehouse(BaseModel):
    """Warehouse model for organization."""

    __tablename__ = "warehouses"

    name = Column(String, nullable=False)
    code = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Foreign keys
    company_id = Column(
        PgUUID(as_uuid=True), ForeignKey("companies.id"), nullable=False
    )



    def __repr__(self) -> str:
        return f"<Warehouse {self.name}>"
