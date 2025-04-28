"""
System settings model for application configuration.
"""

from enum import Enum
from typing import List, Optional, Any

from sqlalchemy import Boolean, Column, Enum as SQLAlchemyEnum, String, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PgUUID


from src.core.models.base_model import BaseModel


class SettingType(str, Enum):
    """Setting type enum."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    DATE = "date"
    DATETIME = "datetime"


class SettingScope(str, Enum):
    """Setting scope enum."""

    SYSTEM = "system"
    USER = "user"
    ORGANIZATION = "organization"
    COMPANY = "company"


class SystemSetting(BaseModel):
    """SystemSetting model for application configuration."""

    __tablename__ = "system_settings"

    key = Column(String, nullable=False, index=True, unique=True)
    value = Column(JSON, nullable=True)
    default_value = Column(JSON, nullable=True)
    data_type = Column(
        SQLAlchemyEnum(SettingType), nullable=False, default=SettingType.STRING
    )
    scope = Column(
        SQLAlchemyEnum(SettingScope), nullable=False, default=SettingScope.SYSTEM
    )
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)

    # Foreign keys
    user_id = Column(PgUUID(as_uuid=True), nullable=True, index=True)

    company_id = Column(
        PgUUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True
    )



    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}>"

    def get_typed_value(self) -> Any:
        """Get value converted to the appropriate type."""
        if self.value is None:
            return None

        try:
            if self.data_type == SettingType.INTEGER:
                return int(self.value)
            elif self.data_type == SettingType.FLOAT:
                return float(self.value)
            elif self.data_type == SettingType.BOOLEAN:
                return bool(self.value)
            elif self.data_type == SettingType.JSON:
                return self.value  # Already parsed as JSON
            else:
                return self.value  # String or other types
        except (ValueError, TypeError):
            return self.value  # Return as is if conversion fails
