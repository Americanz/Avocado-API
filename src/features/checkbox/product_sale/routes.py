from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from src.core.loader_factory.api_factory.routes import create_api_router
from src.core.loader_factory.api_factory.controller import create_controller
from src.core.database.connection import get_db
from src.core.security.jwt import get_current_user, require_auth
from src.core.schemas.responses import SuccessExtra

from .model import ProductSale
from .schemas import ProductSaleCreate, ProductSaleUpdate, ProductSaleResponse
from .controller import get_product_sale_controller

# Створюємо маршрутизатор з універсальними CRUD операціями
router = create_api_router(
    controller=create_controller(ProductSale, ProductSaleResponse),
    create_schema=ProductSaleCreate,
    update_schema=ProductSaleUpdate,
    response_schema=ProductSaleResponse,
    prefix="/checkbox/productsales",
    tags=["product sales"],
    auth_dependency=require_auth,
    include_endpoints=["list"],  # Включаємо тільки endpoint "list"
)

# Видаляємо дублювання маршруту GET "/" - використовуємо той, що вже створений через create_api_router

# Створюємо окремий роутер для спеціалізованих ендпоінтів
special_router = APIRouter(
    tags=["product sales"],
)


@special_router.get("/by-date", dependencies=[Depends(get_current_user)])
async def get_sales_by_date(
    sale_date: date = Query(..., description="Дата продажу (формат: YYYY-MM-DD)"),
    product_name: Optional[str] = Query(None, description="Фільтр за назвою товару"),
    product_code: Optional[str] = Query(None, description="Фільтр за кодом товару"),
    receipt_numbers: Optional[str] = Query(None, description="Фільтр за номером чеку"),
    fiscal_number: Optional[str] = Query(
        None, description="Фільтр за фіскальним номером каси"
    ),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    page_size: int = Query(
        10, ge=1, le=100, description="Кількість елементів на сторінці"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Отримати всі товарні позиції за вказану дату (з початку дня по кінець).

    Можна додатково фільтрувати за назвою або кодом товару, номером чеку або фіскальним номером каси.
    Підтримується пагінація через параметри page та page_size.
    """
    # Використовуємо контролер із окремого файлу
    controller = get_product_sale_controller().with_db(db)

    # Отримуємо дані через контролер
    total_count, items = await controller.get_sales_by_date(
        sale_date=sale_date,
        page=page,
        page_size=page_size,
        product_name=product_name,
        product_code=product_code,
        receipt_numbers=receipt_numbers,
        fiscal_number=fiscal_number,
    )

    # Перетворюємо результати в модель відповіді
    response_items = controller.prepare_responses(items)

    # Знаходимо унікальні чеки в результатах
    receipt_numbers_set = set()
    receipts_summary = []

    for item in items:
        if item.receipt_numbers not in receipt_numbers_set and item.receipt_numbers:
            receipt_numbers_set.add(item.receipt_numbers)
            receipts_summary.append(
                {
                    "receipt_numbers": item.receipt_numbers,
                    "sale_date": item.sale_date.isoformat() if item.sale_date else None,
                    "sale_datetime": (
                        item.sale_datetime.isoformat() if item.sale_datetime else None
                    ),
                    "items_count": len(
                        [i for i in items if i.receipt_numbers == item.receipt_numbers]
                    ),
                }
            )

    # Готуємо дані відповіді
    result_data = {"items": response_items, "receipts_summary": receipts_summary}

    # Використовуємо клас SuccessExtra для відповіді з інформацією про пагінацію
    return SuccessExtra(
        data=result_data,
        total=total_count,
        current=page,
        size=page_size,
        msg=f"Знайдено {total_count} товарних позицій за {sale_date.isoformat()}",
    )


@special_router.get("/by-receipt", dependencies=[Depends(get_current_user)])
async def get_sales_by_receipt(
    receipt_numbers: str = Query(..., description="Номер чеку"),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    page_size: int = Query(
        10, ge=1, le=100, description="Кількість елементів на сторінці"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Отримати всі товарні позиції за номером чеку.

    Підтримується пагінація через параметри page та page_size.
    """
    # Використовуємо контролер із окремого файлу
    controller = get_product_sale_controller().with_db(db)

    # Отримуємо дані через контролер
    total_count, items = await controller.get_sales_by_receipt(
        receipt_numbers=receipt_numbers, page=page, page_size=page_size
    )

    # Перетворюємо результати в модель відповіді
    response_items = controller.prepare_responses(items)

    # Готуємо інформацію про чек
    receipt_info = {}
    if items:
        first_item = items[0]
        receipt_info = {
            "receipt_numbers": first_item.receipt_numbers,
            "sale_date": (
                first_item.sale_date.isoformat() if first_item.sale_date else None
            ),
            "sale_datetime": (
                first_item.sale_datetime.isoformat()
                if first_item.sale_datetime
                else None
            ),
            "fiscal_number": first_item.fiscal_number,
            "register_address": first_item.register_address,
            "items_count": total_count,
        }

    # Використовуємо клас SuccessExtra для відповіді з інформацією про пагінацію
    return SuccessExtra(
        data={"items": response_items, "receipt_info": receipt_info},
        total=total_count,
        current=page,
        size=page_size,
        msg=f"Знайдено {total_count} товарних позицій у чеку {receipt_numbers}",
    )


# Включаємо спеціалізовані маршрути в основний роутер
router.include_router(special_router)
