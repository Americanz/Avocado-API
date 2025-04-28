"""
Database initialization module.
"""

from sqlalchemy.ext.asyncio import AsyncConnection

from src.core.database.connection import Base, async_engine

from src.core.models.logging.providers import get_global_logger

logger = get_global_logger()
if logger is None:
    import logging
    logger = logging.getLogger(__name__)

async def create_tables(drop_all: bool = False):
    """
    Create database tables.

    Args:
        drop_all (bool): Whether to drop all tables before creating them
    """
    async with async_engine.begin() as conn:
        conn: AsyncConnection
        if drop_all:
            logger.warning("Dropping all tables!")
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully")
