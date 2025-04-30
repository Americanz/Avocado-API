"""
Контролер для управління товарними позиціями (ProductSale).
"""

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from src.core.loader_factory.api_factory.controller import APIController

from .model import ProductSale
from .schemas import ProductSaleResponse


class ProductSaleController(APIController):
    """Контролер для спеціалізованих операцій з товарними позиціями."""

    async def get_sales_by_date(
        self,
        sale_date: date,
        page: int = 1,
        page_size: int = 10,
        product_name: Optional[str] = None,
        product_code: Optional[str] = None,
        receipt_numbers: Optional[str] = None,
        fiscal_number: Optional[str] = None,
    ) -> Tuple[int, List[ProductSale]]:
        """
        Отримати товари за вказану дату.

        Args:
            sale_date: Дата продажу
            page: Номер сторінки
            page_size: Кількість елементів на сторінці
            product_name: Фільтр за назвою товару (частковий пошук)
            product_code: Фільтр за кодом товару (точний пошук)
            receipt_numbers: Фільтр за номером чеку (точний пошук)
            fiscal_number: Фільтр за фіскальним номером каси (точний пошук)

        Returns:
            Кортеж із загальною кількістю записів та списком об'єктів товарних позицій
        """
        db = await self.get_db_session()

        # Створюємо фільтр для початку і кінця дня
        start_of_day = datetime.combine(sale_date, datetime.min.time())
        end_of_day = datetime.combine(sale_date, datetime.max.time())

        # Базовий фільтр за датою
        date_filter = or_(
            ProductSale.sale_date == sale_date,
            (ProductSale.sale_datetime >= start_of_day) & (ProductSale.sale_datetime <= end_of_day)
        )

        # Додаткові фільтри
        filters = [date_filter]

        if product_code:
            filters.append(ProductSale.product_code == product_code)

        if receipt_numbers:
            filters.append(ProductSale.receipt_numbers == receipt_numbers)

        if fiscal_number:
            filters.append(ProductSale.fiscal_number == fiscal_number)

        # Поля пошуку для текстового фільтру
        search_fields = ["product_name"] if product_name else None

        # Використовуємо базовий метод list з CRUDBase
        return await self.list(
            page=page,
            page_size=page_size,
            search_filter=and_(*filters) if len(filters) > 1 else filters[0],
            order_by=["-sale_datetime"],
            search_fields=search_fields,
            search_term=product_name
        )

    async def get_sales_by_receipt(
        self,
        receipt_numbers: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[int, List[ProductSale]]:
        """
        Отримати всі товари за номером чеку.

        Args:
            receipt_numbers: Номер чеку
            page: Номер сторінки
            page_size: Кількість елементів на сторінці

        Returns:
            Кортеж із загальною кількістю записів та списком об'єктів товарних позицій
        """
        db = await self.get_db_session()

        # Фільтр за номером чеку
        receipt_filter = ProductSale.receipt_numbers == receipt_numbers

        # Використовуємо базовий метод list з CRUDBase
        return await self.list(
            page=page,
            page_size=page_size,
            search_filter=receipt_filter,
            order_by=["-sale_datetime"]
        )


# Створюємо екземпляр контролера для використання в маршрутах
def get_product_sale_controller():
    """
    Отримати екземпляр контролера товарних позицій.

    Returns:
        Екземпляр ProductSaleController
    """
    return ProductSaleController(
        model=ProductSale,
        response_schema=ProductSaleResponse,
        search_fields=["product_name", "product_code", "barcode", "receipt_numbers"],
        default_order_by=["-date_created"]
    )
