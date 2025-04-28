"""
Database migrations module.
"""


from typing import AsyncGenerator, Optional

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from src.core.database.connection import engine, async_engine

from src.config import settings  # Додаємо імпорт settings для reset_database
from src.core.models.logging.providers import get_global_logger

logger = get_global_logger()
if logger is None:
    import logging
    logger = logging.getLogger(__name__)


async def get_current_revision(connection: AsyncConnection) -> Optional[str]:
    """
    Get current database revision.

    Args:
        connection: Database connection

    Returns:
        Optional[str]: Current revision or None if no revision
    """
    try:
        # Для асинхронного з'єднання потрібно використовувати run_sync
        def _get_revision(sync_conn):
            context = MigrationContext.configure(sync_conn)
            return context.get_current_revision()

        current_rev = await connection.run_sync(_get_revision)
        return current_rev
    except Exception as e:
        logger.error(f"Error getting current revision: {e}")
        return None


async def get_database_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Get database connection.

    Yields:
        AsyncConnection: Database connection
    """
    async with async_engine.connect() as connection:
        yield connection


async def check_migrations() -> None:
    """
    Check if migrations are up to date.
    """
    # Get alembic configuration
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)

    # Get latest revision
    head_revision = script.get_current_head()

    # Get current revision
    async with async_engine.connect() as connection:
        current_revision = await get_current_revision(connection)

    # Log migration status
    if current_revision is None:
        logger.warning("No migrations have been run yet!")
    elif current_revision != head_revision:
        logger.warning(
            f"Database is not up to date! Current revision: {current_revision}, latest revision: {head_revision}"
        )
    else:
        logger.info("Database migrations are up to date.")


async def check_pending_migrations() -> dict:
    """
    Check if there are pending migrations that need to be applied.

    Returns:
        dict: Dictionary with information about pending migrations
            {
                "current_revision": str,  # Current database revision
                "latest_revision": str,   # Latest available revision
                "is_up_to_date": bool,    # Whether database is up to date
                "pending_migrations": list, # List of pending migration objects
                "pending_count": int      # Number of pending migrations
            }
    """
    # Get alembic configuration
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)

    # Get latest revision
    head_revision = script.get_current_head()

    # Get current revision
    async with async_engine.connect() as connection:
        current_revision = await get_current_revision(connection)

    # Check if there are pending migrations
    is_up_to_date = current_revision == head_revision

    # Get list of pending migration revisions
    pending_migrations = []
    pending_count = 0

    if current_revision is not None and not is_up_to_date:
        # Get all revisions between current and head
        revs = list(script.iterate_revisions(current_revision, head_revision))
        pending_count = len(revs)

        # Extract info about each pending migration
        for rev in revs:
            pending_migrations.append({
                "revision": rev.revision,
                "down_revision": rev.down_revision,
                "doc": rev.doc,  # Migration message/description
                "path": rev.path
            })

    result = {
        "current_revision": current_revision,
        "latest_revision": head_revision,
        "is_up_to_date": is_up_to_date,
        "pending_migrations": pending_migrations,
        "pending_count": pending_count
    }

    if not is_up_to_date:
        logger.warning(f"Database is not up to date! {pending_count} migrations pending.")
        for mig in pending_migrations:
            logger.info(f"Pending migration: {mig['revision']} - {mig['doc']}")
    else:
        logger.info("Database migrations are up to date.")

    return result


def has_pending_migrations() -> bool:
    """
    Check if there are pending migrations without printing detailed logs.
    This is a synchronous wrapper for check_pending_migrations.

    Returns:
        bool: True if there are pending migrations, False otherwise
    """
    try:
        # Використовуємо синхронний спосіб перевірки міграцій замість
        # запуску асинхронної функції в синхронному контексті
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)

        # Отримуємо останню ревізію
        head_revision = script.get_current_head()

        # Отримуємо поточну ревізію з бази даних через синхронне з'єднання
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_revision = context.get_current_revision()

        # Перевіряємо чи потрібні міграції
        is_up_to_date = current_revision == head_revision

        if not is_up_to_date:
            logger.warning(f"Database is not up to date! Current: {current_revision}, latest: {head_revision}")

        return not is_up_to_date
    except Exception as e:
        logger.error(f"Error checking pending migrations: {e}")
        # Якщо не можемо перевірити, припускаємо, що можуть бути необхідні міграції
        return True


async def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            logger.info("Database connection is working.")
            return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False


def run_migrations() -> None:
    """
    Run migrations to latest revision.
    """
    from alembic import command

    # Get alembic configuration
    alembic_cfg = Config("alembic.ini")

    # Run migrations
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error applying migrations: {e}")
        raise


def create_migration(message: str) -> None:
    """
    Create new migration with autogenerate.

    Args:
        message: Migration message/description
    """
    from alembic import command

    # Get alembic configuration
    alembic_cfg = Config("alembic.ini")

    # Create migration
    try:
        command.revision(alembic_cfg, message=message, autogenerate=True)
        logger.info(f"Created new migration: {message}")
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        raise


def reset_database() -> None:
    """
    Reset database by dropping all tables and reapplying migrations.
    Only for development!
    """
    from src.core.database.connection import Base, engine

    if not settings.DEBUG:
        logger.error("Cannot reset database in production mode!")
        return

    try:
        # Видаляємо всі таблиці
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")

        # Застосовуємо всі міграції
        run_migrations()
        logger.info("Database reset completed successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise
