"""
Base service class for Poster API integration
"""

import logging
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from src.core.database.connection import SessionLocal
from src.features.telegram_bot.models import SyncLog

logger = logging.getLogger(__name__)


class PosterBaseService:
    """Base class for Poster services"""

    def __init__(self, api_token: str, account_name: str):
        self.api_token = api_token
        self.account_name = account_name
        self.base_url = f"https://{account_name}.joinposter.com/api"
        self.SessionLocal = SessionLocal

    def log_sync_result(
        self,
        sync_type: str,
        status: str,
        details: Optional[dict] = None,
    ):
        """Log synchronization result to database"""
        try:
            with self.SessionLocal() as db:
                log_entry = SyncLog(
                    sync_type=sync_type,
                    status=status,
                    details=details or {},
                    synced_at=datetime.utcnow(),
                )
                db.add(log_entry)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to log sync result: {e}")

    def _parse_poster_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse Poster datetime format"""
        if not dt_str:
            return None

        # Convert to string if it's a number
        dt_str = str(dt_str)

        try:
            # First try to parse as timestamp (milliseconds)
            if dt_str.isdigit():
                timestamp_ms = int(dt_str)
                # Convert milliseconds to seconds
                timestamp_s = timestamp_ms / 1000
                return datetime.fromtimestamp(timestamp_s)

            # Try different datetime formats that Poster might use
            datetime_formats = [
                "%Y-%m-%d %H:%M:%S",  # "2024-08-30 14:30:00"
                "%Y-%m-%d",  # "2024-08-30"
                "%d.%m.%Y %H:%M:%S",  # "30.08.2024 14:30:00"
                "%d.%m.%Y",  # "30.08.2024"
            ]

            for fmt in datetime_formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue

            # If none of the formats worked, log warning and return None
            logger.warning(f"Could not parse datetime: {dt_str}")
            return None

        except Exception as e:
            logger.error(f"Error parsing datetime '{dt_str}': {e}")
            return None

    def _safe_decimal(self, value, default=None) -> Optional[Decimal]:
        """Safely convert value to Decimal"""
        if value is None or value == "":
            return default
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=None) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _safe_bool(self, value, default=False) -> bool:
        """Safely convert value to bool"""
        if value is None or value == "":
            return default
        try:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(int(value))
        except (ValueError, TypeError):
            return default
