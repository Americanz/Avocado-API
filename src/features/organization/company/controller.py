from typing import List, Optional, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID, select, func
from src.core.models.loader.generic_controller import GenericController
from .model import Company
from .schemas import CompanyCreate, CompanyUpdate, CompanyResponse

# Визначення типів для типізації
T = TypeVar("T", bound=Company)
CreateSchemaType = TypeVar("CreateSchemaType", bound=CompanyCreate)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=CompanyUpdate)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=CompanyResponse)


class CompanyController(
    GenericController[Company, CompanyCreate, CompanyUpdate, CompanyResponse]
):
    """Розширений контролер для роботи з компаніями."""

    async def get_active_companies(self, db: AsyncSession) -> List[Company]:
        """Отримати тільки активні компанії."""
        query = select(self.model).where(self.model.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Company]:
        """Знайти компанію за назвою."""
        query = select(self.model).where(func.lower(self.model.name) == name.lower())
        result = await db.execute(query)
        return result.scalars().first()

    async def toggle_active_status(
        self, db: AsyncSession, company_id: UUID
    ) -> Optional[Company]:
        """Змінити статус активності компанії на протилежний."""
        company = await self.get_by_id(db, company_id)
        if not company:
            return None

        company.is_active = not company.is_active
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company

    async def search_by_address(
        self, db: AsyncSession, address_fragment: str
    ) -> List[Company]:
        """Пошук компаній за частиною адреси."""
        query = select(self.model).where(
            self.model.address.ilike(f"%{address_fragment}%")
        )
        result = await db.execute(query)
        return result.scalars().all()

    # Тут можна додати інші спеціалізовані методи


# Функція для створення інстансу контролера
def get_company_controller() -> CompanyController:
    """Створити та повернути інстанс контролера для компаній."""
    return CompanyController(Company, CompanyResponse)
