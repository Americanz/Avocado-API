"""
Alembic environment module for database migrations.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Додаємо кореневу директорію проекту до sys.path для коректних імпортів
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)  # Використовуємо insert замість append для пріоритетності

# Імпортуємо необхідні модулі для доступу до моделей та бази даних
from src.config import settings
from src.core.database.connection import Base
from src.core.models.loader.registry import register_all_models




# Register all models to ensure they are included in migrations
register_all_models()
# У env.py після register_all_models()
print("Tables detected in metadata:")
target_metadata = Base.metadata
for table_name in target_metadata.tables.keys():
    print(f"- {table_name}")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Переконфігуруємо URL бази даних з налаштувань застосунку
# Це дозволяє не зберігати пароль бази даних у файлі alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Додаткові опції
        compare_type=True,  # Порівнювати типи колонок під час autogenerate
        compare_server_default=True,  # Порівнювати значення за замовчуванням
        include_schemas=True,  # Включати схеми (якщо використовуються)
        render_as_batch=True,  # Використовувати batch режим для SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Додаткові опції
            compare_type=True,  # Порівнювати типи колонок під час autogenerate
            compare_server_default=True,  # Порівнювати значення за замовчуванням
            include_schemas=True,  # Включати схеми (якщо використовуються)
            render_as_batch=True,  # Використовувати batch режим для SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
