from fastapi import APIRouter, Depends, Request
from src.core.security.jwt import require_auth
from src.features.bonuses.model import BonusAccount, Transaction
from src.features.bonuses.schemas import (
    BonusAccountCreate,
    BonusAccountUpdate,
    BonusAccountResponse,
    BonusTransactionCreate,
    BonusTransactionResponse,
)
from src.features.bonuses.schemas_check import CheckRequest, CheckResponse
from src.features.bonuses.controller import (
    BonusAccountController,
    BonusTransactionController,
)
from src.core.loader_factory.api_factory.routes import create_api_router
from src.core.database.connection import get_sync_db

router = APIRouter()

# CRUD для бонусних рахунків
accounts_router = create_api_router(
    controller=BonusAccountController,
    create_schema=BonusAccountCreate,
    update_schema=BonusAccountUpdate,
    response_schema=BonusAccountResponse,
    prefix="/bonus-accounts",
    tags=["bonuses"],
    auth_dependency=require_auth,
    include_endpoints=["list"],
)

# CRUD для транзакцій
transactions_router = create_api_router(
    controller=BonusTransactionController,
    create_schema=BonusTransactionCreate,
    update_schema=None,
    response_schema=BonusTransactionResponse,
    prefix="/bonus-transactions",
    tags=["bonuses"],
    auth_dependency=require_auth,
    include_endpoints=["list"],
)

router.include_router(accounts_router)
router.include_router(transactions_router)


@router.post(
    "/check",
    response_model=CheckResponse,
    tags=["bonuses"],
    dependencies=[Depends(require_auth)],
)
async def accrue_bonuses_for_check(data: CheckRequest, db=Depends(get_sync_db)):
    """
    Приймає чек з вже розрахованими бонусами, зберігає чек і транзакцію в базу через контролер.
    """
    from src.features.bonuses.controller import accrue_bonuses_for_check as accrue_check

    transaction = accrue_check(db, data)
    if not transaction:
        return CheckResponse(client_id=data.client_id, bonuses_accrued=0, details=[])
    return CheckResponse(
        client_id=data.client_id,
        bonuses_accrued=transaction.amount,
        details=[
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in data.items
        ],
    )
