"""
Database connection module.
"""

import time
from typing import AsyncGenerator, Dict, Optional

from sqlalchemy import create_engine, MetaData, text, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncConnection,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

# Тимчасово імпортуємо стандартний логгер
import logging

_logger = logging.getLogger(__name__)

from src.config import settings

# Імпорти логування перенесені нижче, після ініціалізації підключення до БД
# щоб уникнути циклічної залежності

# Налаштування метаданих
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)

# Створення базової моделі
Base = declarative_base(metadata=metadata)


# Налаштування підтримки UUID для SQLite
def _sqlite_uuid_converter(uuid_obj):
    """Convert UUID objects to strings for SQLite"""
    if uuid_obj is None:
        return None
    return str(uuid_obj)


def _sqlite_load_uuid(uuid_str):
    """Load UUID from SQLite string representation"""
    import uuid

    if uuid_str is None:
        return None
    return uuid.UUID(uuid_str)


# Логування SQL запитів, якщо DEBUG=True
if settings.DEBUG:
    # Використаємо рівень логування INFO для SQL запитів при включеному DEBUG
    # Примітка: loguru не має getLogger, тому управляємо рівнем логування іншим чином
    pass  # Конфігурація для loguru здійснюється через інтерцептори подій нижче


# SQLAlchemy event listener для логування запитів
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if not hasattr(conn, "info"):
        conn.info = {}
    conn.info.setdefault("query_start_time", []).append(time.time())
    if settings.DEBUG:
        _logger.debug("SQL Query: %s", statement)
        _logger.debug("Parameters: %s", parameters)


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if (
        hasattr(conn, "info")
        and "query_start_time" in conn.info
        and conn.info["query_start_time"]
    ):
        total = time.time() - conn.info["query_start_time"].pop(-1)
        if settings.DEBUG:
            _logger.debug("SQL Query Execution Time: %.3f s", total)


# Створення async engine
if settings.USE_SQLITE:
    # SQLite оптимізації
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,  # Змінено з settings.DEBUG на False, щоб відключити автоматичне логування
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    # Синхронний engine для міграцій та утиліт
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,  # Змінено з settings.DEBUG на False, щоб відключити автоматичне логування
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    # Register UUID type adapter for SQLite
    import sqlite3
    import uuid

    sqlite3.register_converter("UUID", _sqlite_load_uuid)
    sqlite3.register_adapter(uuid.UUID, _sqlite_uuid_converter)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas on connect"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL конфігурація
    async_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,  # Змінено з settings.DEBUG на False, щоб відключити автоматичне логування
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
    )
    # Синхронний engine для міграцій та утиліт
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,  # Змінено з settings.DEBUG на False, щоб відключити автоматичне логування
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True,
    )

# Створення асинхронної session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine, expire_on_commit=False, autocommit=False, autoflush=False
)

# Створення синхронної session factory для утиліт
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            _logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """
    Get synchronous database session.

    Returns:
        Session: Synchronous database session
    """
    db = SessionLocal()
    return db


async def init_db() -> AsyncSession:
    """
    Initialize database.

    Returns:
        AsyncSession: Database session
    """
    try:
        # Використовуємо метадані з Base
        async with async_engine.begin() as conn:
            # Для SQLite потрібно вручну включити foreign keys
            if settings.USE_SQLITE:
                await conn.execute(text("PRAGMA foreign_keys=ON"))

            # Перевірка підключення
            await conn.execute(text("SELECT 1"))
            _logger.info("Database connection established successfully")

            # Ми більше не створюємо таблиці автоматично, а використовуємо міграції
            # Це призводило до постійного виводу SQL-запитів при кожному запуску
            # await create_tables(drop_all=settings.DEBUG and settings.RESET_DB)

        # Перевіряємо статус міграцій
        from src.core.database.migrations import check_migrations

        await check_migrations()

        # Створюємо сесію для операцій з базою даних
        session = AsyncSessionLocal()
        return session
    except Exception as e:
        _logger.error(f"Error initializing database: {e}")
        raise


# Додавання event listeners для асинхронних запитів
# Це складніше, оскільки з AsyncEngine потрібен інший підхід
# Використаємо проміжний об'єкт для логування асинхронних запитів


class AsyncQueryTracker:
    """Tracker for async database queries."""

    _query_data: Dict[str, Dict] = {}

    @classmethod
    def start_query(cls, query_id: str, query: str, params: Optional[Dict] = None):
        """Start tracking a query."""
        cls._query_data[query_id] = {
            "query": query,
            "params": params,
            "start_time": time.time(),
        }
        if settings.DEBUG:
            _logger.debug(f"Async SQL Query ({query_id}): {query}")
            _logger.debug(f"Parameters: {params}")

    @classmethod
    def end_query(cls, query_id: str):
        """End tracking a query and log its execution time."""
        if query_id in cls._query_data:
            query_info = cls._query_data[query_id]
            total_time = time.time() - query_info["start_time"]
            if settings.DEBUG:
                _logger.debug(
                    f"Async SQL Query ({query_id}) Execution Time: {total_time:.3f} s"
                )
            del cls._query_data[query_id]


"""
Database initialization module.
"""


async def create_tables(drop_all: bool = False):
    """
    Create database tables.

    Args:
        drop_all (bool): Whether to drop all tables before creating them
    """
    from src.core.database.connection import async_engine

    async with async_engine.begin() as conn:
        conn: AsyncConnection
        if drop_all:
            _logger.warning("Dropping all tables!")
            await conn.run_sync(Base.metadata.drop_all)

        _logger.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        _logger.info("Tables created successfully")
