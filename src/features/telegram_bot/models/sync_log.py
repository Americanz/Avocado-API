"""
Poster sync log model
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    JSON,
)
from src.core.models.base_model import BaseModel


class SyncLog(BaseModel):
    """
    Log for Poster API synchronization
    """

    __tablename__ = "sync_logs"

    use_generic_routes = False
    search_fields = ["sync_type", "status"]
    default_order_by = ["-created_at"]

    # Sync information
    sync_type = Column(
        String(50), nullable=False, comment="Type: transactions, clients, products"
    )
    status = Column(
        String(20), nullable=False, comment="Status: success, error, partial"
    )

    # Timing
    start_time = Column(DateTime, nullable=False, comment="Sync start time")
    end_time = Column(DateTime, nullable=True, comment="Sync end time")

    # Results
    records_processed = Column(
        Integer, nullable=False, default=0, comment="Records processed"
    )
    records_success = Column(
        Integer, nullable=False, default=0, comment="Successful records"
    )
    records_failed = Column(
        Integer, nullable=False, default=0, comment="Failed records"
    )

    # Error details
    error_message = Column(Text, nullable=True, comment="Error message if failed")
    error_details = Column(JSON, nullable=True, comment="Detailed error information")

    # API call details
    api_endpoint = Column(String(255), nullable=True, comment="API endpoint called")
    api_response_time = Column(
        Integer, nullable=True, comment="API response time in ms"
    )

    def __repr__(self):
        return f"<SyncLog type={self.sync_type} status={self.status}>"
