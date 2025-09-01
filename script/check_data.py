#!/usr/bin/env python3
"""
Check loaded data in database
"""
from sqlalchemy import create_engine, text
from src.config.settings import get_settings


def check_data():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        print("=== Data Check Results ===")

        # Check stores
        stores = conn.execute(text("SELECT COUNT(*) FROM telegram_stores")).scalar()
        print(f"✅ Stores loaded: {stores}")

        if stores > 0:
            store_names = conn.execute(
                text("SELECT name FROM telegram_stores LIMIT 3")
            ).fetchall()
            print(f"   Sample stores: {[s[0] for s in store_names]}")

        # Check receipts
        receipts = conn.execute(text("SELECT COUNT(*) FROM telegram_receipts")).scalar()
        print(f"✅ Receipts loaded: {receipts}")

        # Check receipt items
        items = conn.execute(
            text("SELECT COUNT(*) FROM telegram_receipt_items")
        ).scalar()
        print(f"✅ Receipt items loaded: {items}")

        # Check transactions
        transactions = conn.execute(
            text("SELECT COUNT(*) FROM telegram_bonus_transactions")
        ).scalar()
        print(f"✅ Bonus transactions: {transactions}")

        print("\n=== System Ready for Testing ===")


if __name__ == "__main__":
    check_data()
