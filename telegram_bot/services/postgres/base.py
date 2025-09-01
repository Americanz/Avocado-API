"""
Base PostgreSQL service for Telegram bot
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

# Add main project to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.database.connection import SessionLocal
except ImportError:
    from telegram_bot.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Fallback: create our own session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger("telegram_bot.postgres")


class PostgresBaseService:
    """Base PostgreSQL service class"""

    def __init__(self):
        pass

    def get_session(self) -> Session:
        """Get database session"""
        return SessionLocal()

    def execute_query(self, query_func, *args, **kwargs):
        """Execute query with session management"""
        with self.get_session() as db:
            try:
                result = query_func(db, *args, **kwargs)
                db.commit()
                return result
            except Exception as e:
                db.rollback()
                logger.error(f"Database error: {e}")
                raise