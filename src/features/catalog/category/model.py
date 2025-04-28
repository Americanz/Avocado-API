"""
Category model for catalog management.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import relationship

from src.core.models.base_model import BaseModel


class Category(BaseModel):
    """Category model for product categorization."""

    __tablename__ = "categories"

    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    


    # Parent-child relationship (hierarchical structure)
    parent_id = Column(PgUUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Relationships
    parent = relationship(
        "Category", remote_side="Category.id", backref="subcategories"
    )
    products = relationship("Product", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"
