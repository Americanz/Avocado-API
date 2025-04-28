# Оновлення для app/models/reports.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Float,
    Boolean,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.core.models.base_model import BaseModel


class Report(BaseModel):
    __tablename__ = "reports"

    # Налаштування для generic_routes
    use_generic_routes = True
    search_fields = ["processing_status", "report_type", "filename"]
    default_order_by = [
        "-date_created"
    ]  # Сортування за датою створення (спочатку нові)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now())
    from_date = Column(DateTime(timezone=True))
    to_date = Column(DateTime(timezone=True))

    # Нові зв'язки
    # checkbox_account_id = Column(Integer, ForeignKey("checkbox_accounts.id"), nullable=True)
    # schedule_id = Column(Integer, ForeignKey("report_schedules.id"), nullable=True)

    cash_register_id = Column(String)
    emails = Column(Text)  # Зберігаємо як JSON
    processing_status = Column(
        String, default="pending"
    )  # pending, processing, completed, failed
    report_data = Column(Text, nullable=True)  # JSON дані звіту або метадані
    error_message = Column(Text, nullable=True)  # Повідомлення про помилку, якщо є
    is_processed = Column(Boolean, default=False)  # Чи оброблено звіт
    report_type = Column(String, nullable=True)  # Тип звіту: "goods" або "payments"

    filename = Column(String, nullable=True)  # Назва файлу
    file_hash = Column(String, nullable=True)  # MD5 або інший хеш вмісту файлу
    rows_count = Column(Integer, default=0)  # Кількість рядків у файлі
    processing_time = Column(Float, nullable=True)  # Час обробки в секундах

    # Зв'язки
    # checkbox_account = relationship("CheckboxAccount", back_populates="reports")
    # schedule = relationship("ReportSchedule", back_populates="reports")
    # product_sales = relationship("ProductSale", back_populates="report", cascade="all, delete-orphan")


# Виправлення: імена класів як рядки
__all__ = ["Report"]
