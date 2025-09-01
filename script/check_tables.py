#!/usr/bin/env python3
"""
Script to check database tables after migration
"""
import sys
import os
from sqlalchemy import create_engine, text
from src.config.settings import get_settings


# Додаємо кореневу папку проекту до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def check_tables():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
            )
        )

        tables = [row[0] for row in result]
        print("Tables in database:")
        for table in tables:
            print(f"  - {table}")

        # Check if new tables exist
        required_tables = [
            "telegram_stores",
            "telegram_receipts",
            "telegram_receipt_items",
        ]
        for table in required_tables:
            if table in tables:
                print(f"✅ {table} - EXISTS")
            else:
                print(f"❌ {table} - MISSING")


if __name__ == "__main__":
    check_tables()
