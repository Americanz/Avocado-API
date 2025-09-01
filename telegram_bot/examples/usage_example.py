"""
Example of how to use the new adapter schemas in telegram bot handlers
"""

from sqlalchemy.orm import Session
from telegram_bot.services.telegram_service import get_telegram_services
from telegram_bot.schemas import TelegramBotUser, TelegramReceipt


# Example usage in a telegram handler
async def example_handler(message, session: Session):
    """Example of using adapter services"""

    # Get services
    services = get_telegram_services(session)
    user_service = services["user"]
    bonus_service = services["bonus"]
    receipt_service = services["receipt"]

    user_id = message.from_user.id

    # Get user using adapter - returns TelegramBotUserAdapter but we can use it as TelegramBotUser
    user = user_service.get_user_by_id(user_id)
    if not user:
        # Create user
        user = user_service.upsert_user(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

    # Work with user data using familiar field names
    print(f"User: {user.first_name} {user.last_name} (@{user.username})")
    print(f"Phone: {user.phone}")
    print(f"Active: {user.is_active}")

    # Get user receipts using adapter - returns TelegramReceiptAdapter but we can use as TelegramReceipt
    receipts = receipt_service.get_user_receipts(user_id, limit=5)
    for receipt in receipts:
        print(
            f"Receipt {receipt.receipt_number}: {receipt.total_amount} UAH at {receipt.store_name}"
        )

    # Get bonus balance
    balance = bonus_service.get_user_balance(user_id)
    print(f"Bonus balance: {balance}")

    # Add bonuses
    bonus_service.add_bonus(user_id, 100, "Test bonus")

    # Get bonus history
    history = bonus_service.get_user_history(user_id)
    for transaction in history:
        print(
            f"Bonus transaction: {transaction['amount']} - {transaction['description']}"
        )


# Alternative approach - direct usage of schemas with session
async def alternative_example(session: Session, telegram_user_id: int):
    """Example using schemas directly"""

    from telegram_bot.schemas import get_telegram_user, get_user_receipts

    # Get user
    user = get_telegram_user(session, telegram_user_id)
    if user:
        # Now user is TelegramBotUserAdapter with all expected fields
        print(
            f"User ID: {user.user_id}"
        )  # This is actually telegram_user_id from Client
        print(f"Username: {user.username}")  # This is telegram_username from Client
        print(
            f"Name: {user.first_name} {user.last_name}"
        )  # These are telegram_first_name, telegram_last_name

    # Get receipts
    receipts = get_user_receipts(session, telegram_user_id)
    for receipt in receipts:
        print(f"Receipt: {receipt.receipt_number} - {receipt.total_amount}")
