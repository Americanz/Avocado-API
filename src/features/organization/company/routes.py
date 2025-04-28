from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models.loader.generic_routes import create_api_router
from src.core.models.loader.generic_controller import create_controller
from src.core.database.connection import get_db
from src.core.security.jwt import get_current_user, require_auth
from .model import Company
from .schemas import CompanyCreate, CompanyUpdate, CompanyResponse
from src.core.schemas.responses import Success
from .controller import CompanyController

# Створюємо маршрутизатор з універсальними CRUD операціями
router = create_api_router(
    controller=create_controller(Company, CompanyResponse),
    create_schema=CompanyCreate,
    update_schema=CompanyUpdate,
    response_schema=CompanyResponse,
    prefix="/organizations/companies",
    tags=["companies"],
    auth_dependency=require_auth,
    admin_dependency=require_auth,
)

# Тут можна додати додаткові спеціалізовані маршрути, наприклад:
@router.get("/list/active",dependencies=[Depends(get_current_user)])
async def get_active_companies(db: AsyncSession = Depends(get_db)):
    """Отримати всі активні компанії."""
    controller = CompanyController(Company, CompanyResponse)
    companies = await controller.get_active_companies(db)
    return Success(data=companies)
