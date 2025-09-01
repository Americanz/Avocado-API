"""
Telegram Bot Internal API Routes

These routes are for internal management and admin purposes only.
Not exposed to public API.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.connection import get_db

# from src.core.security.jwt import require_admin_access  # TODO: Implement admin access check
from .controller import (
    telegram_bot_user,
    telegram_bonus_account,
    telegram_bonus_transaction,
)
from .schemas import (
    Client,
    ClientCreate,
    ClientUpdate,
    TelegramBonusAccount,
    TelegramBonusAccountCreate,
    TelegramBonusAccountUpdate,
    TelegramBonusTransaction,
    TelegramBonusTransactionCreate,
    # Legacy imports for backward compatibility
    TelegramBotUser,
    TelegramBotUserCreate,
    TelegramBotUserUpdate,
)

# Internal admin router - not exposed publicly
router = APIRouter(
    prefix="/internal/telegram-bot",
    tags=["Telegram Bot Internal"],
    # dependencies=[Depends(require_admin_access)]  # TODO: Add admin access only
)


# User management routes
@router.get("/users/", response_model=List[Client])
async def list_telegram_users(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List telegram bot users (Admin only)"""
    users = telegram_bot_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/users/with-phone/", response_model=List[Client])
async def list_users_with_phone(limit: int = 100, db: Session = Depends(get_db)):
    """List users who shared their phone number (Admin only)"""
    users = telegram_bot_user.get_users_with_phone(db, limit=limit)
    return users


@router.get("/users/blocked/", response_model=List[Client])
async def list_blocked_users(limit: int = 100, db: Session = Depends(get_db)):
    """List blocked users (Admin only)"""
    users = telegram_bot_user.get_blocked_users(db, limit=limit)
    return users


@router.get("/users/telegram/{telegram_user_id}", response_model=Client)
async def get_user_by_telegram_id(telegram_user_id: int, db: Session = Depends(get_db)):
    """Get user by telegram user ID (Admin only)"""
    user = telegram_bot_user.get_by_telegram_id(db, telegram_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Telegram user not found"
        )
    return user


# Bonus account management routes
@router.get("/bonus-accounts/", response_model=List[TelegramBonusAccount])
async def list_bonus_accounts(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """List telegram bonus accounts (Admin only)"""
    accounts = telegram_bonus_account.get_multi(db, skip=skip, limit=limit)
    return accounts


@router.get("/bonus-accounts/with-balance/", response_model=List[TelegramBonusAccount])
async def list_accounts_with_balance(
    min_balance: int = 1, limit: int = 100, db: Session = Depends(get_db)
):
    """List accounts with balance (Admin only)"""
    accounts = telegram_bonus_account.get_accounts_with_balance(db, min_balance, limit)
    return accounts


@router.post(
    "/bonus-accounts/{client_id}/add-bonus/", response_model=TelegramBonusAccount
)
async def add_bonus_to_account(
    client_id: int,
    amount: int,
    reason: str = None,
    admin_id: int = None,
    db: Session = Depends(get_db),
):
    """Add bonus to account (Admin only)"""
    account = telegram_bonus_account.add_bonus(db, client_id, amount, reason, admin_id)
    return account


# Transaction management routes
@router.get("/transactions/", response_model=List[TelegramBonusTransaction])
async def list_recent_transactions(limit: int = 100, db: Session = Depends(get_db)):
    """List recent bonus transactions (Admin only)"""
    transactions = telegram_bonus_transaction.get_recent_transactions(db, limit)
    return transactions


@router.get(
    "/transactions/client/{client_id}", response_model=List[TelegramBonusTransaction]
)
async def list_client_transactions(
    client_id: int, limit: int = 50, db: Session = Depends(get_db)
):
    """List transactions for specific client (Admin only)"""
    transactions = telegram_bonus_transaction.get_by_client_id(db, client_id, limit)
    return transactions


# Statistics routes
@router.get("/stats/summary")
async def get_telegram_bot_stats(db: Session = Depends(get_db)):
    """Get telegram bot statistics (Admin only)"""
    total_users = telegram_bot_user.count(db)
    users_with_phone = len(telegram_bot_user.get_users_with_phone(db))
    blocked_users = len(telegram_bot_user.get_blocked_users(db))
    accounts_with_balance = len(telegram_bonus_account.get_accounts_with_balance(db))

    # Calculate total balance
    all_accounts = telegram_bonus_account.get_multi(db, limit=10000)
    total_balance = sum(account.balance for account in all_accounts)

    return {
        "users": {
            "total": total_users,
            "with_phone": users_with_phone,
            "blocked": blocked_users,
            "phone_percentage": (
                round((users_with_phone / total_users * 100), 2)
                if total_users > 0
                else 0
            ),
        },
        "bonuses": {
            "total_balance": total_balance,
            "accounts_with_balance": accounts_with_balance,
        },
    }


__all__ = ["router"]
