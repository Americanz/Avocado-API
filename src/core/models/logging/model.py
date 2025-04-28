from sqlalchemy import (
    Column,
    String,
    Integer,
    JSON,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from src.core.models.logging.constants import LogLevel, LogDetailType, LogType
from src.core.models.base_model import BaseModel


class ApplicationLog(BaseModel):
    """Модель для зберігання всіх системних логів, помилок та дій користувачів."""

    __tablename__ = "application_logs"

    # Вказуємо, що ця модель не успадковує автоматично всі поля від BaseModel
    __mapper_args__ = {
        "exclude_properties": ["created_at", "updated_at", "is_active"],
    }

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String, nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_type = Column(String, nullable=False)  # Тип логу: SYSTEM, USER, DATABASE, ERROR
    detail_type = Column(String, nullable=True)  # Подія: CREATE, UPDATE, LOGIN, STARTUP
    message = Column(Text, nullable=False)  # Повідомлення логу
    module = Column(String, nullable=True)  # Модуль/компонент, що викликав лог

    # Дані користувача
    user_id = Column(String, nullable=True)  # ID користувача, якщо доступний

    # Дані сутності (для логів бази даних)
    entity_type = Column(String, nullable=True)  # Тип сутності (User, Order, Product)
    entity_id = Column(String, nullable=True)  # ID сутності

    # Дані помилки
    exception_type = Column(String, nullable=True)  # Тип виключення
    stack_trace = Column(Text, nullable=True)  # Стек виклику помилки

    # Опціональний зв'язок з HTTP логом (якщо помилка пов'язана з запитом)
    http_log_id = Column(String, ForeignKey("http_logs.id"), nullable=True)
    http_log = relationship("HttpLog", back_populates="application_logs")

    # Додаткові дані в форматі JSON
    data = Column(JSON, nullable=True)  # Будь-які додаткові дані

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_system_log(
        cls, message, level=LogLevel.INFO, detail_type=None, module=None, data=None
    ):
        """Створює системний лог."""
        return cls(
            message=message,
            level=level.value if isinstance(level, LogLevel) else level,
            log_type=LogType.SYSTEM.value,
            detail_type=(
                detail_type.value
                if isinstance(detail_type, LogDetailType)
                else detail_type
            ),
            module=module,
            data=data,
        )

    @classmethod
    def create_user_log(
        cls,
        message,
        user_id,
        level=LogLevel.INFO,
        detail_type=None,
        module=None,
        data=None,
    ):
        """Створює лог дій користувача."""
        return cls(
            message=message,
            level=level.value if isinstance(level, LogLevel) else level,
            log_type=LogType.USER.value,
            detail_type=(
                detail_type.value
                if isinstance(detail_type, LogDetailType)
                else detail_type
            ),
            user_id=user_id,
            module=module,
            data=data,
        )

    @classmethod
    def create_error_log(
        cls,
        message,
        exception=None,
        level=LogLevel.ERROR,
        module=None,
        user_id=None,
        http_log_id=None,
        data=None,
    ):
        """Створює лог помилки."""
        stack_trace = None
        exception_type = None

        if exception:
            import traceback

            stack_trace = "".join(
                traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            )
            exception_type = type(exception).__name__

        return cls(
            message=message,
            level=level.value if isinstance(level, LogLevel) else level,
            log_type="ERROR",
            module=module,
            user_id=user_id,
            exception_type=exception_type,
            stack_trace=stack_trace,
            http_log_id=http_log_id,
            data=data,
        )

    @classmethod
    def create_db_log(
        cls,
        message,
        entity_type,
        entity_id=None,
        user_id=None,
        level=LogLevel.INFO,
        detail_type=None,
        data=None,
    ):
        """Створює лог операції з базою даних."""
        return cls(
            message=message,
            level=level.value if isinstance(level, LogLevel) else level,
            log_type=LogType.DATABASE.value,
            detail_type=(
                detail_type.value
                if isinstance(detail_type, LogDetailType)
                else detail_type
            ),
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            data=data,
        )


class HttpLog(BaseModel):
    """Модель для зберігання логів HTTP запитів та відповідей."""

    __tablename__ = "http_logs"



    # Вказуємо, що ця модель не успадковує автоматично всі поля від BaseModel
    __mapper_args__ = {
        "exclude_properties": ["created_at", "updated_at", "is_active"],
    }

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Тип запису (запит/відповідь)
    is_request = Column(
        Boolean, default=True, nullable=False
    )  # True для запиту, False для відповіді

    # Дані запиту
    method = Column(String, nullable=True)  # HTTP метод (GET, POST, тощо)
    path = Column(String, nullable=True)  # URL шлях
    client_ip = Column(String, nullable=True)  # IP клієнта
    user_id = Column(String, nullable=True)  # ID користувача, якщо авторизований
    request_headers = Column(JSON, nullable=True)  # Заголовки запиту
    query_params = Column(JSON, nullable=True)  # Параметри запиту
    request_body = Column(JSON, nullable=True)  # Тіло запиту

    # Дані відповіді
    status_code = Column(Integer, nullable=True)  # HTTP статус код
    response_headers = Column(JSON, nullable=True)  # Заголовки відповіді
    response_body = Column(JSON, nullable=True)  # Тіло відповіді

    # Дані продуктивності
    processing_time_ms = Column(Float, nullable=True)  # Час обробки в мілісекундах

    # Зв'язок з іншим логом (для пов'язування запитів і відповідей)
    related_log_id = Column(String, ForeignKey("http_logs.id"), nullable=True)
    related_log = relationship("HttpLog", remote_side=[id], backref="child_logs")

    # Зв'язок із системними/користувацькими логами
    application_logs = relationship("ApplicationLog", back_populates="http_log")

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create_request_log(
        cls,
        method,
        path,
        client_ip,
        headers=None,
        query_params=None,
        body=None,
        user_id=None,
    ):
        """Створює лог HTTP запиту."""
        return cls(
            is_request=True,
            method=method,
            path=path,
            client_ip=client_ip,
            request_headers=headers,
            query_params=query_params,
            request_body=body,
            user_id=user_id,
        )

    @classmethod
    def create_response_log(
        cls,
        request_log_id,
        status_code,
        headers=None,
        body=None,
        processing_time_ms=None,
    ):
        """Створює лог HTTP відповіді, пов'язаний із запитом."""
        return cls(
            is_request=False,
            status_code=status_code,
            response_headers=headers,
            response_body=body,
            processing_time_ms=processing_time_ms,
            related_log_id=request_log_id,
        )


__all__ = ["ApplicationLog", "HttpLog", "LogLevel", "LogType", "LogDetailType"]
