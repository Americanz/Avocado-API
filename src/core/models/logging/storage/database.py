import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .base import LogStorage


class DatabaseLogStorage(LogStorage):
    """Сховище логів, що зберігає їх у базі даних."""

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує сховище логів в базі даних.

        Args:
            db_session: Асинхронна сесія SQLAlchemy
        """
        self.db_session = db_session

    async def store_api_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає API лог у базі даних.

        Args:
            log_data: Дані логу

        Returns:
            ID запису або None у випадку помилки
        """
        try:
            # Імпортуємо тут, щоб уникнути циклічних імпортів
            from src.core.models.logging.models import ApiLog
            
            # Створюємо ID для логу
            log_id = str(uuid.uuid4())
            
            # Підготовка даних для зберігання
            user_id = log_data.get("user_id")
            ip_address = log_data.get("ip_address")
            request_method = log_data.get("request_method")
            request_url = log_data.get("request_url")
            request_params = json.dumps(log_data.get("request_params", {}))
            request_data = json.dumps(log_data.get("request_data", {}))
            response_code = log_data.get("response_code")
            response_data = json.dumps(log_data.get("response_data", {}))
            process_time = log_data.get("process_time")
            error = log_data.get("error")
            level = log_data.get("level")
            
            # Виконуємо запит на вставку
            query = insert(ApiLog).values(
                id=log_id,
                user_id=user_id,
                ip_address=ip_address,
                request_method=request_method,
                request_url=request_url,
                request_params=request_params,
                request_data=request_data,
                response_code=response_code,
                response_data=response_data,
                process_time=process_time,
                error=error,
                level=level,
                created_at=datetime.utcnow()
            )
            
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            return log_id
        except Exception as e:
            print(f"Error storing API log in database: {e}")
            # Пробуємо відкатити транзакцію
            try:
                await self.db_session.rollback()
            except Exception:
                pass
            return None

    async def store_user_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає лог дій користувача у базі даних.

        Args:
            log_data: Дані логу

        Returns:
            ID запису або None у випадку помилки
        """
        try:
            # Імпортуємо тут, щоб уникнути циклічних імпортів
            from src.core.models.logging.models import UserLog
            
            # Створюємо ID для логу
            log_id = str(uuid.uuid4())
            
            # Підготовка даних для зберігання
            user_id = log_data.get("user_id")
            api_log_id = log_data.get("api_log_id")
            detail_type = log_data.get("detail_type")
            detail = log_data.get("detail")
            level = log_data.get("level")
            additional_data = json.dumps(log_data.get("additional_data", {}))
            
            # Виконуємо запит на вставку
            query = insert(UserLog).values(
                id=log_id,
                user_id=user_id,
                api_log_id=api_log_id,
                detail_type=detail_type,
                detail=detail,
                level=level,
                additional_data=additional_data,
                created_at=datetime.utcnow()
            )
            
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            return log_id
        except Exception as e:
            print(f"Error storing user log in database: {e}")
            # Пробуємо відкатити транзакцію
            try:
                await self.db_session.rollback()
            except Exception:
                pass
            return None

    async def store_system_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """
        Зберігає системний лог у базі даних.

        Args:
            log_data: Дані логу

        Returns:
            ID запису або None у випадку помилки
        """
        try:
            # Імпортуємо тут, щоб уникнути циклічних імпортів
            from src.core.models.logging.models import SystemLog
            
            # Створюємо ID для логу
            log_id = str(uuid.uuid4())
            
            # Визначаємо тип логу - звичайний системний чи операція з базою даних
            if log_data.get("operation_type"):
                # Це лог операції з базою даних
                detail_type = f"database_{log_data.get('operation_type', '').lower()}"
                entity_type = log_data.get("entity_type")
                entity_id = log_data.get("entity_id")
                user_id = log_data.get("user_id")
                duration = log_data.get("duration")
                detail = f"Database operation: {log_data.get('operation_type')} on {entity_type} {entity_id or ''}"
                if duration:
                    detail += f" (duration: {duration:.3f}s)"
            else:
                # Звичайний системний лог
                detail_type = log_data.get("detail_type")
                detail = log_data.get("detail")
                entity_type = None
                entity_id = None
                user_id = None
                duration = None
            
            level = log_data.get("level")
            error = log_data.get("error")
            additional_data = json.dumps(log_data.get("additional_data", {}))
            
            # Виконуємо запит на вставку
            query = insert(SystemLog).values(
                id=log_id,
                detail_type=detail_type,
                detail=detail,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                duration=duration,
                error=error,
                level=level,
                additional_data=additional_data,
                created_at=datetime.utcnow()
            )
            
            await self.db_session.execute(query)
            await self.db_session.commit()
            
            return log_id
        except Exception as e:
            print(f"Error storing system log in database: {e}")
            # Пробуємо відкатити транзакцію
            try:
                await self.db_session.rollback()
            except Exception:
                pass
            return None