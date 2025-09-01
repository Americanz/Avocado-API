#!/usr/bin/env python3
"""
Utility script for managing PostgreSQL discount calculation triggers
"""

import logging
import sys
import argparse
from src.core.database.connection import SessionLocal
from sqlalchemy import text
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def enable_triggers():
    """Enable discount calculation triggers"""
    with SessionLocal() as db:
        result = db.execute(text("SELECT manage_discount_triggers(true)"))
        message = result.fetchone()[0]
        print(f"✅ {message}")


def disable_triggers():
    """Disable discount calculation triggers"""
    with SessionLocal() as db:
        result = db.execute(text("SELECT manage_discount_triggers(false)"))
        message = result.fetchone()[0]
        print(f"⚠️ {message}")


def recalculate_all():
    """Recalculate all discounts using PostgreSQL"""
    print("🔄 Recalculating all discounts...")
    with SessionLocal() as db:
        result = db.execute(
            text("SELECT * FROM recalculate_all_discounts_with_trigger()")
        )
        row = result.fetchone()
        total, updated, total_discount = row
        print(f"📊 Results:")
        print(f"   Total transactions: {total}")
        print(f"   Updated: {updated}")
        print(f"   Total discount amount: {total_discount}")


def check_triggers():
    """Check if triggers are enabled"""
    with SessionLocal() as db:
        # Check if triggers exist and are enabled
        result = db.execute(
            text(
                """
            SELECT
                trigger_name,
                event_object_table,
                action_timing,
                event_manipulation
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%discount%'
            ORDER BY event_object_table, trigger_name
            """
            )
        )

        triggers = result.fetchall()
        if triggers:
            print("🔍 Discount calculation triggers:")
            for trigger in triggers:
                name, table, timing, event = trigger
                print(f"   ✓ {name} on {table} ({timing} {event})")
        else:
            print("❌ No discount triggers found")


def test_trigger():
    """Test trigger functionality"""
    print("🧪 Testing trigger functionality...")

    with SessionLocal() as db:
        # Find a transaction with products
        result = db.execute(
            text(
                """
            SELECT tp.transaction_id, t.discount
            FROM transaction_products tp
            JOIN transactions t ON tp.transaction_id = t.transaction_id
            LIMIT 1
            """
            )
        )

        row = result.fetchone()
        if not row:
            print("❌ No test data found")
            return

        trans_id, old_discount = row
        print(
            f"📋 Testing with transaction {trans_id}, current discount: {old_discount}"
        )

        # Update a product to trigger discount recalculation
        db.execute(
            text(
                "UPDATE transaction_products SET sum = sum + 0.001 WHERE transaction_id = :trans_id"
            ),
            {"trans_id": trans_id},
        )
        db.commit()

        # Check new discount
        result = db.execute(
            text("SELECT discount FROM transactions WHERE transaction_id = :trans_id"),
            {"trans_id": trans_id},
        )
        new_discount = result.fetchone()[0]

        print(f"🎯 After trigger: discount = {new_discount}")

        if abs(float(new_discount) - float(old_discount)) > 0.0005:
            print("✅ Trigger is working correctly!")
        else:
            print("⚠️ Trigger may not be working as expected")


def main():
    parser = argparse.ArgumentParser(
        description="Manage PostgreSQL discount calculation triggers"
    )
    parser.add_argument(
        "action",
        choices=["enable", "disable", "check", "recalculate", "test"],
        help="Action to perform",
    )

    args = parser.parse_args()

    print(f"🔧 PostgreSQL Discount Triggers Manager")
    print(f"Action: {args.action}")
    print("-" * 40)

    try:
        if args.action == "enable":
            enable_triggers()
        elif args.action == "disable":
            disable_triggers()
        elif args.action == "check":
            check_triggers()
        elif args.action == "recalculate":
            recalculate_all()
        elif args.action == "test":
            test_trigger()

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
