from sqlalchemy import (
    Boolean,
    Column,
    String,
    Float,
    Date,
    ForeignKey,
    DateTime,
    Integer,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.models.base_model import BaseModel


class ProductSale(BaseModel):
    __tablename__ = "product_sales"

    # Налаштування для generic_routes
    use_generic_routes = True
    search_fields = ["product_name", "product_code", "barcode", "receipt_numbers"]
    default_order_by = ["-date_created"]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"))

    # Дані про товар
    product_code = Column(String, index=True)  # Код товару
    product_name = Column(String, nullable=True)  # Найменування
    ukt_zed_code = Column(String, nullable=True)  # УКТ ЗЕД
    barcode = Column(String, nullable=True)  # Штрих-код

    # Дані про чек і продаж
    receipt_numbers = Column(
        String, index=True
    )  # Фіскальні номери чеків (ключ для зв'язування)
    operation_type = Column(String)  # Вид операції
    price = Column(Float, nullable=True)  # Вартість
    quantity = Column(Float)  # Кількість
    amount = Column(Float, nullable=True)  # Сума
    receipts_count = Column(Integer, nullable=True)  # Чеків з товаром

    # Податкова інформація
    tax_name = Column(String, nullable=True)  # Назва податку
    tax_rate = Column(String, nullable=True)  # Податок
    additional_fee = Column(Float, default=0)  # Дод. збір

    # Знижки та націнки
    discount_amount = Column(Float, default=0)  # Сума знижок
    markup_amount = Column(Float, default=0)  # Сума націнок

    # Загальна сума та дата
    total_amount = Column(Float)  # Загальна сума
    sale_date = Column(Date, nullable=True)  # Дата продажу
    sale_datetime = Column(DateTime, nullable=True)  # Дата та час закриття зміни

    # Інформація про касу і оплату
    fiscal_number = Column(String, nullable=True)  # Фіскальний номер ПРРО
    register_address = Column(String, nullable=True)  # Адреса каси
    excise_stamp = Column(String, nullable=True)  # Акцизна марка
    shift_number = Column(Integer, nullable=True)  # Номер зміни
    payment_type = Column(String, nullable=True)  # Тип оплати
    is_return = Column(Boolean, default=False)  # Повернення

    # Інші дані
    check_link = Column(String, nullable=True)  # Посилання на чек

    # Технічні поля
    date_created = Column(DateTime(timezone=True), server_default=func.now())

    # Зв'язок з таблицею звітів
    # report = relationship("Report", back_populates="product_sales")


__all__ = ["ProductSale"]
