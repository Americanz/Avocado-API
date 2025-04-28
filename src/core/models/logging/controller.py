from src.core.crud.crud_base import CRUDBase
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import uuid

from .model import ApplicationLog, HttpLog
from .schemas import HttpLogRead, ApplicationLogRead
from .constants import LogLevel, LogType, LogDetailType


def convert_uuid_to_str(obj: Any) -> Any:
    """
    Converts UUID objects to strings in model objects

    Args:
        obj: Object that might contain UUID fields

    Returns:
        Object with UUID fields converted to strings
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return obj


class LoggingController:
    """Контролер для роботи з логами у ендпоінтах"""

    def __init__(self, db: Session):
        """Ініціалізує контролер з сесією бази даних"""
        self.db = db

    # Методи для роботи з ApplicationLog

    def get_application_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        log_type: Optional[Union[LogType, str]] = None,
        level: Optional[Union[LogLevel, str]] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        detail_type: Optional[Union[LogDetailType, str]] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ApplicationLog]:
        """
        Отримує системні логи з фільтрацією.

        Args:
            limit: Максимальна кількість записів
            offset: Кількість записів, які потрібно пропустити
            log_type: Тип логу (SYSTEM, USER, DATABASE, ERROR)
            level: Рівень логу
            module: Фільтр за назвою модуля
            user_id: Фільтр за ID користувача
            detail_type: Фільтр за типом деталей
            entity_type: Фільтр за типом сутності (для логів БД)
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Список записів ApplicationLog
        """
        query = self.db.query(ApplicationLog)

        # Застосовуємо фільтри
        if log_type is not None:
            log_type_val = log_type.value if hasattr(log_type, "value") else log_type
            query = query.filter(ApplicationLog.log_type == log_type_val)

        if level is not None:
            level_val = level.value if hasattr(level, "value") else level
            query = query.filter(ApplicationLog.level == level_val)

        if module is not None:
            query = query.filter(ApplicationLog.module == module)

        if user_id is not None:
            query = query.filter(ApplicationLog.user_id == user_id)

        if detail_type is not None:
            detail_type_val = (
                detail_type.value if hasattr(detail_type, "value") else detail_type
            )
            query = query.filter(ApplicationLog.detail_type == detail_type_val)

        if entity_type is not None:
            query = query.filter(ApplicationLog.entity_type == entity_type)

        if start_date is not None:
            query = query.filter(ApplicationLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(ApplicationLog.timestamp <= end_date)

        # Сортування за часом у спадному порядку (найновіші спочатку)
        query = query.order_by(desc(ApplicationLog.timestamp))

        # Пагінація
        query = query.limit(limit).offset(offset)

        logs = query.all()

        # Convert UUID fields to strings before returning
        for log in logs:
            log.id = convert_uuid_to_str(log.id)
            log.http_log_id = (
                convert_uuid_to_str(log.http_log_id) if log.http_log_id else None
            )

        return logs

    def get_application_log_by_id(self, log_id: str) -> Optional[ApplicationLog]:
        """
        Отримує лог додатку за ідентифікатором.

        Args:
            log_id: Ідентифікатор логу

        Returns:
            Об'єкт ApplicationLog або None
        """
        log = self.db.query(ApplicationLog).filter(ApplicationLog.id == log_id).first()
        if log:
            log.id = convert_uuid_to_str(log.id)
            log.http_log_id = (
                convert_uuid_to_str(log.http_log_id) if log.http_log_id else None
            )
        return log

    def get_error_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        exception_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ApplicationLog]:
        """
        Отримує логи помилок з фільтрацією.

        Args:
            limit: Максимальна кількість записів
            offset: Кількість записів, які потрібно пропустити
            module: Фільтр за назвою модуля
            user_id: Фільтр за ID користувача
            exception_type: Фільтр за типом виключення
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Список записів ApplicationLog з рівнем ERROR
        """
        # Використовуємо рівень LogLevel.ERROR замість LogType.ERROR
        query = self.db.query(ApplicationLog).filter(
            ApplicationLog.level == LogLevel.ERROR.value
        )

        if module is not None:
            query = query.filter(ApplicationLog.module == module)

        if user_id is not None:
            query = query.filter(ApplicationLog.user_id == user_id)

        if exception_type is not None:
            query = query.filter(ApplicationLog.exception_type == exception_type)

        if start_date is not None:
            query = query.filter(ApplicationLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(ApplicationLog.timestamp <= end_date)

        # Сортування за часом у спадному порядку (найновіші спочатку)
        query = query.order_by(desc(ApplicationLog.timestamp))

        # Пагінація
        query = query.limit(limit).offset(offset)

        logs = query.all()

        # Convert UUID fields to strings before returning
        for log in logs:
            log.id = convert_uuid_to_str(log.id)
            log.http_log_id = (
                convert_uuid_to_str(log.http_log_id) if log.http_log_id else None
            )

        return logs

    # Методи для роботи з HttpLog

    def get_http_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        is_request: Optional[bool] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
        min_processing_time: Optional[float] = None,
        max_processing_time: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[HttpLog]:
        """
        Отримує HTTP логи з фільтрацією.

        Args:
            limit: Максимальна кількість записів
            offset: Кількість записів, які потрібно пропустити
            is_request: Фільтр за типом (True - запити, False - відповіді)
            method: Фільтр за HTTP методом
            path: Фільтр за шляхом
            client_ip: Фільтр за IP клієнта
            user_id: Фільтр за ID користувача
            status_code: Фільтр за HTTP статус кодом
            min_processing_time: Мінімальний час обробки
            max_processing_time: Максимальний час обробки
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Список записів HttpLog
        """
        query = self.db.query(HttpLog)

        # Застосовуємо фільтри
        if is_request is not None:
            query = query.filter(HttpLog.is_request == is_request)

        if method is not None:
            query = query.filter(HttpLog.method == method)

        if path is not None:
            query = query.filter(HttpLog.path.like(f"%{path}%"))

        if client_ip is not None:
            query = query.filter(HttpLog.client_ip == client_ip)

        if user_id is not None:
            query = query.filter(HttpLog.user_id == user_id)

        if status_code is not None:
            query = query.filter(HttpLog.status_code == status_code)

        if min_processing_time is not None:
            query = query.filter(HttpLog.processing_time_ms >= min_processing_time)

        if max_processing_time is not None:
            query = query.filter(HttpLog.processing_time_ms <= max_processing_time)

        if start_date is not None:
            query = query.filter(HttpLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(HttpLog.timestamp <= end_date)

        # Сортування за часом у спадному порядку (найновіші спочатку)
        query = query.order_by(desc(HttpLog.timestamp))

        # Пагінація
        query = query.limit(limit).offset(offset)

        logs = query.all()

        # Convert UUID fields to strings before returning
        for log in logs:
            log.id = convert_uuid_to_str(log.id)
            log.related_log_id = (
                convert_uuid_to_str(log.related_log_id) if log.related_log_id else None
            )

        return logs

    def get_http_log_by_id(self, log_id: str) -> Optional[HttpLog]:
        """
        Отримує HTTP лог за ідентифікатором.

        Args:
            log_id: Ідентифікатор логу

        Returns:
            Об'єкт HttpLog або None
        """
        log = self.db.query(HttpLog).filter(HttpLog.id == log_id).first()
        if log:
            log.id = convert_uuid_to_str(log.id)
            log.related_log_id = (
                convert_uuid_to_str(log.related_log_id) if log.related_log_id else None
            )
        return log

    def get_request_with_response(self, request_id: str) -> Dict[str, Any]:
        """
        Отримує запит та пов'язану з ним відповідь.

        Args:
            request_id: ID запису запиту

        Returns:
            Словник з даними запиту та відповіді
        """
        request_log = self.db.query(HttpLog).filter(HttpLog.id == request_id).first()
        if not request_log:
            return None

        # Знаходимо відповідь, якщо вона є
        response_log = (
            self.db.query(HttpLog)
            .filter(HttpLog.related_log_id == request_id, HttpLog.is_request == False)
            .first()
        )

        result = {
            "request": {
                "id": convert_uuid_to_str(request_log.id),
                "timestamp": request_log.timestamp,
                "method": request_log.method,
                "path": request_log.path,
                "client_ip": request_log.client_ip,
                "user_id": request_log.user_id,
                "headers": request_log.request_headers,
                "query_params": request_log.query_params,
                "body": request_log.request_body,
            },
            "response": None,
        }

        if response_log:
            result["response"] = {
                "id": convert_uuid_to_str(response_log.id),
                "timestamp": response_log.timestamp,
                "status_code": response_log.status_code,
                "headers": response_log.response_headers,
                "body": response_log.response_body,
                "processing_time_ms": response_log.processing_time_ms,
            }

        return result

    def count_application_logs(
        self,
        log_type: Optional[Union[LogType, str]] = None,
        level: Optional[Union[LogLevel, str]] = None,
        module: Optional[str] = None,
        user_id: Optional[str] = None,
        detail_type: Optional[Union[LogDetailType, str]] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Підраховує кількість логів додатку з фільтрацією.

        Args:
            log_type: Тип логу (SYSTEM, USER, DATABASE, ERROR)
            level: Рівень логу
            module: Фільтр за назвою модуля
            user_id: Фільтр за ID користувача
            detail_type: Фільтр за типом деталей
            entity_type: Фільтр за типом сутності (для логів БД)
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Кількість логів
        """
        query = self.db.query(ApplicationLog)

        # Застосовуємо фільтри
        if log_type is not None:
            log_type_val = log_type.value if hasattr(log_type, "value") else log_type
            query = query.filter(ApplicationLog.log_type == log_type_val)

        if level is not None:
            level_val = level.value if hasattr(level, "value") else level
            query = query.filter(ApplicationLog.level == level_val)

        if module is not None:
            query = query.filter(ApplicationLog.module == module)

        if user_id is not None:
            query = query.filter(ApplicationLog.user_id == user_id)

        if detail_type is not None:
            detail_type_val = (
                detail_type.value if hasattr(detail_type, "value") else detail_type
            )
            query = query.filter(ApplicationLog.detail_type == detail_type_val)

        if entity_type is not None:
            query = query.filter(ApplicationLog.entity_type == entity_type)

        if start_date is not None:
            query = query.filter(ApplicationLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(ApplicationLog.timestamp <= end_date)

        return query.count()

    def count_http_logs(
        self,
        is_request: Optional[bool] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        status_code: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Підраховує кількість HTTP логів з фільтрацією.

        Args:
            is_request: Фільтр за типом (True - запити, False - відповіді)
            method: Фільтр за HTTP методом
            path: Фільтр за шляхом
            client_ip: Фільтр за IP клієнта
            user_id: Фільтр за ID користувача
            status_code: Фільтр за HTTP статус кодом
            start_date: Фільтр за датою (від)
            end_date: Фільтр за датою (до)

        Returns:
            Кількість логів
        """
        query = self.db.query(HttpLog)

        # Застосовуємо фільтри
        if is_request is not None:
            query = query.filter(HttpLog.is_request == is_request)

        if method is not None:
            query = query.filter(HttpLog.method == method)

        if path is not None:
            query = query.filter(HttpLog.path.like(f"%{path}%"))

        if client_ip is not None:
            query = query.filter(HttpLog.client_ip == client_ip)

        if user_id is not None:
            query = query.filter(HttpLog.user_id == user_id)

        if status_code is not None:
            query = query.filter(HttpLog.status_code == status_code)

        if start_date is not None:
            query = query.filter(HttpLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(HttpLog.timestamp <= end_date)

        return query.count()


# Фабрична функція для створення контролера
def get_logging_controller(db: Session) -> LoggingController:
    """
    Фабрична функція для створення контролера логування

    Args:
        db: Сесія бази даних

    Returns:
        Контролер логування
    """
    return LoggingController(db)
