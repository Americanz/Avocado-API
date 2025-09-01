#!/usr/bin/env python3
"""
Utility script for managing PostgreSQL bonus calculation triggers
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
    """Enable bonus calculation triggers"""
    with SessionLocal() as db:
        result = db.execute(text("SELECT manage_bonus_triggers(true)"))
        message = result.fetchone()[0]
        print(f"✅ {message}")


def disable_triggers():
    """Disable bonus calculation triggers"""
    with SessionLocal() as db:
        result = db.execute(text("SELECT manage_bonus_triggers(false)"))
        message = result.fetchone()[0]
        print(f"⚠️ {message}")


def recalculate_all():
    """Recalculate all bonuses using PostgreSQL"""
    print("🔄 Recalculating all bonuses...")
    with SessionLocal() as db:
        result = db.execute(
            text("SELECT * FROM recalculate_all_bonuses_with_trigger()")
        )
        row = result.fetchone()
        total, updated, earned_total, spent_total = row
        print(f"📊 Results:")
        print(f"   Total transactions: {total}")
        print(f"   Updated: {updated}")
        print(f"   Total bonuses earned: {earned_total}")
        print(f"   Total bonuses spent: {spent_total}")


def check_triggers():
    """Check if bonus triggers are enabled"""
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
            WHERE trigger_name LIKE '%bonus%'
            ORDER BY event_object_table, trigger_name
            """
            )
        )

        triggers = result.fetchall()
        if triggers:
            print("🔍 Bonus calculation triggers:")
            for trigger in triggers:
                name, table, timing, event = trigger
                print(f"   ✓ {name} on {table} ({timing} {event})")
        else:
            print("❌ No bonus triggers found")


def check_settings():
    """Check bonus system settings"""
    print("⚙️ Bonus system settings:")
    with SessionLocal() as db:
        result = db.execute(
            text(
                "SELECT key, value, description FROM system_settings WHERE key LIKE 'bonus%' ORDER BY key"
            )
        )
        settings = result.fetchall()

        if settings:
            for key, value, description in settings:
                print(f"   📝 {key}: {value}")
                if description:
                    print(f"      └─ {description}")
        else:
            print("❌ No bonus settings found")


def set_setting():
    """Set bonus system setting interactively"""
    print("⚙️ Available bonus settings:")
    print("1. bonus_system_enabled (true/false)")
    print("2. bonus_system_start_date (YYYY-MM-DD)")
    print("3. default_bonus_percent (number)")

    key = input("Enter setting key: ").strip()
    value = input("Enter setting value: ").strip()
    description = input("Enter description (optional): ").strip() or None

    with SessionLocal() as db:
        db.execute(
            text("SELECT set_setting(:key, :value, :desc)"),
            {"key": key, "value": value, "desc": description},
        )
        db.commit()
        print(f"✅ Setting '{key}' updated to '{value}'")


def test_trigger():
    """Test trigger functionality"""
    print("🧪 Testing bonus trigger functionality...")

    with SessionLocal() as db:
        # Find a closed transaction with client and bonus data
        result = db.execute(
            text(
                """
            SELECT t.transaction_id, t.client_id, t.sum, t.bonus, t.payed_bonus, c.bonus as client_bonus
            FROM transactions t
            JOIN clients c ON t.client_id = c.client_id
            WHERE t.date_close IS NOT NULL
                AND t.client_id IS NOT NULL
                AND (t.bonus > 0 OR t.payed_bonus > 0)
            LIMIT 1
            """
            )
        )

        row = result.fetchone()
        if not row:
            print(
                "❌ No test data found (need closed transaction with client and bonus data)"
            )
            return

        trans_id, client_id, trans_sum, bonus_percent, paid_bonus, client_bonus = row
        print(f"📋 Testing with transaction {trans_id}")
        print(f"   Client: {client_id}, current bonus: {client_bonus}")
        print(
            f"   Transaction sum: {trans_sum}, bonus %: {bonus_percent}, paid with bonus: {paid_bonus}"
        )

        # Count current bonus operations for this transaction
        result = db.execute(
            text(
                "SELECT COUNT(*) FROM transaction_bonus WHERE transaction_id = :trans_id"
            ),
            {"trans_id": trans_id},
        )
        old_operations_count = result.fetchone()[0]
        print(f"   Current bonus operations: {old_operations_count}")

        # Trigger recalculation by updating transaction
        print("🔄 Triggering bonus recalculation...")
        db.execute(
            text(
                "UPDATE transactions SET updated_at = NOW() WHERE transaction_id = :trans_id"
            ),
            {"trans_id": trans_id},
        )
        db.commit()

        # Check new operations count
        result = db.execute(
            text(
                "SELECT COUNT(*) FROM transaction_bonus WHERE transaction_id = :trans_id"
            ),
            {"trans_id": trans_id},
        )
        new_operations_count = result.fetchone()[0]

        # Check client's new bonus balance
        result = db.execute(
            text("SELECT bonus FROM clients WHERE client_id = :client_id"),
            {"client_id": client_id},
        )
        new_client_bonus = result.fetchone()[0]

        print(f"🎯 After trigger:")
        print(f"   Bonus operations: {new_operations_count}")
        print(f"   Client bonus: {new_client_bonus}")

        if new_operations_count > old_operations_count:
            print("✅ Trigger is working correctly!")
        else:
            print("⚠️ Trigger may not be working as expected")


def view_bonus_history():
    """View recent bonus history"""
    print("📜 Recent bonus operations:")

    with SessionLocal() as db:
        result = db.execute(
            text(
                """
            SELECT
                tb.created_at,
                tb.client_id,
                tb.operation_type,
                tb.amount,
                tb.balance_after,
                tb.description,
                c.firstname,
                c.lastname,
                c.phone
            FROM transaction_bonus tb
            JOIN clients c ON tb.client_id = c.client_id
            ORDER BY tb.created_at DESC
            LIMIT 10
            """
            )
        )

        operations = result.fetchall()
        if operations:
            for op in operations:
                (
                    created,
                    client_id,
                    op_type,
                    amount,
                    balance,
                    desc,
                    fname,
                    lname,
                    phone,
                ) = op
                name = f"{fname or ''} {lname or ''}".strip() or f"ID:{client_id}"
                print(
                    f"   {created} | {op_type:5} | {amount:8.2f} | Bal: {balance:8.2f} | {name} ({phone}) | {desc}"
                )
        else:
            print("   No bonus operations found")


def main():
    parser = argparse.ArgumentParser(
        description="Manage PostgreSQL bonus calculation triggers"
    )
    parser.add_argument(
        "action",
        choices=[
            "enable",
            "disable",
            "check",
            "settings",
            "set",
            "recalculate",
            "test",
            "history",
        ],
        help="Action to perform",
    )

    args = parser.parse_args()

    print(f"🔧 PostgreSQL Bonus Triggers Manager")
    print(f"Action: {args.action}")
    print("-" * 50)

    try:
        if args.action == "enable":
            enable_triggers()
        elif args.action == "disable":
            disable_triggers()
        elif args.action == "check":
            check_triggers()
        elif args.action == "settings":
            check_settings()
        elif args.action == "set":
            set_setting()
        elif args.action == "recalculate":
            recalculate_all()
        elif args.action == "test":
            test_trigger()
        elif args.action == "history":
            view_bonus_history()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())
