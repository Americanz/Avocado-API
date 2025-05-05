#!/usr/bin/env python
"""
Script to initialize database, run migrations, and load initial data.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from alembic import command
from alembic.config import Config
from src.config import settings
from src.core.database.connection import init_db, AsyncSessionLocal
from src.core.services.demo_data import load_demo_data


async def ensure_database_exists():
    """Ensure database file exists and initialize it"""
    # Extract directory path from DATABASE_URL
    if settings.USE_SQLITE:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "").strip("./")
        db_dir = os.path.dirname(db_path)
        
        # Create directory if it doesn't exist
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        
        # Initialize database
        db_session = await init_db()
        await db_session.close()
        print(f"Database initialized at: {db_path}")


def run_migrations():
    """Run database migrations using Alembic"""
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise


async def load_initial_data():
    """Load initial/demo data if configured"""
    if settings.LOAD_DEMO_DATA:
        print("Loading demo data...")
        try:
            async with AsyncSessionLocal() as session:
                await load_demo_data(session)
            print("Demo data loaded successfully")
        except Exception as e:
            print(f"Error loading demo data: {e}")
            raise
    else:
        print("Demo data loading skipped (LOAD_DEMO_DATA=False)")


async def main():
    """Main function to initialize database, run migrations, and load initial data"""
    print(f"Initializing {settings.APP_NAME} database...")
    
    # Ensure database exists
    await ensure_database_exists()
    
    # Run migrations
    run_migrations()
    
    # Load initial data
    await load_initial_data()
    
    print("Database initialization completed successfully")


if __name__ == "__main__":
    asyncio.run(main())