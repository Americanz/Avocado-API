from src.features.bonuses.model import BonusAccount, Transaction
from src.features.bonuses.schemas import (
    BonusAccountCreate,
    BonusAccountUpdate,
    BonusAccountResponse,
    BonusTransactionCreate,
    BonusTransactionResponse,
)
from src.core.loader_factory.api_factory.controller import create_controller

# Контролери для generic CRUD
BonusAccountController = create_controller(BonusAccount, BonusAccountResponse)
BonusTransactionController = create_controller(Transaction, BonusTransactionResponse)


def accrue_bonuses_for_check(db, data):
    """
    Приймає чек з вже розрахованими бонусами, зберігає чек і транзакцію в базу.
    """
    account = db.query(BonusAccount).filter_by(client_id=data.client_id).first()
    if not account:
        account = BonusAccount(client_id=data.client_id, balance=0)
        db.add(account)
        db.commit()
        db.refresh(account)
    bonuses = (
        getattr(data, "bonuses_accrued", 0) if hasattr(data, "bonuses_accrued") else 0
    )
    if not bonuses:
        return None
    transaction = Transaction(
        client_id=data.client_id,
        account_id=account.id,
        amount=bonuses,
        type="accrual",
        description=f"Нарахування бонусів за чек на {data.total_amount} грн",
    )
    db.add(transaction)
    account.balance += bonuses
    db.commit()
    return transaction


__all__ = [
    "BonusAccountController",
    "BonusTransactionController",
]
