"""
Telegram Bot Service Functions

Service functions for telegram bot to work with unified models.
These functions return dictionaries instead of creating duplicate model classes.
"""

# User functions
from .user import (
    get_telegram_user,
    create_or_update_telegram_user,
    search_telegram_users,
)

# Receipt functions
from .receipt import get_user_receipts, get_receipt_details, get_monthly_receipts_stats

# Product functions
from .product import (
    get_product_categories,
    search_products,
    get_user_purchase_history,
    get_user_favorite_products,
)

# Bonus functions
from .bonus import (
    get_user_bonus_balance,
    create_or_get_bonus_account,
    add_bonus_to_user,
    remove_bonus_from_user,
    get_user_bonus_history,
    get_users_with_bonuses,
    get_bonus_statistics,
)

# Transaction Product schemas
from .transaction_product import (
    TransactionProductBase,
    TransactionProductCreate,
    TransactionProductUpdate,
    TransactionProductResponse,
    TransactionProductFromPosterAPI,
)

# Transaction schemas
from .transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionFromPosterAPI,
)

# Store functions removed - use Transaction.spot_name directly

__all__ = [
    # User functions
    "get_telegram_user",
    "create_or_update_telegram_user",
    "search_telegram_users",
    # Receipt functions
    "get_user_receipts",
    "get_receipt_details",
    "get_monthly_receipts_stats",
    # Product functions
    "get_product_categories",
    "search_products",
    "get_user_purchase_history",
    "get_user_favorite_products",
    # Bonus functions
    "get_user_bonus_balance",
    "create_or_get_bonus_account",
    "add_bonus_to_user",
    "remove_bonus_from_user",
    "get_user_bonus_history",
    "get_users_with_bonuses",
    "get_bonus_statistics",
    # Transaction Product schemas
    "TransactionProductBase",
    "TransactionProductCreate", 
    "TransactionProductUpdate",
    "TransactionProductResponse",
    "TransactionProductFromPosterAPI",
    # Transaction schemas
    "TransactionBase",
    "TransactionCreate",
    "TransactionUpdate", 
    "TransactionResponse",
    "TransactionFromPosterAPI",
]
