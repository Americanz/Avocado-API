"""
Маршрути для системи логування
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Path, HTTPException, Security
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

from src.core.database.connection import get_sync_db
from src.core.security.jwt import get_current_user  # Виправлений імпорт
from .constants import LogLevel, LogType, LogDetailType
from .schemas import (
    ApplicationLogListResponse,
    HttpLogListResponse,
    ApplicationLogRead,
    HttpLogRead,
    RequestResponseDetail,
)
from .controller import get_logging_controller, LoggingController

router = APIRouter(
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/application", response_model=ApplicationLogListResponse)
async def get_application_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    log_type: Optional[str] = Query(
        None, description="Filter by log type (SYSTEM, USER, DATABASE, ERROR)"
    ),
    level: Optional[str] = Query(
        None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    module: Optional[str] = Query(None, description="Filter by module name"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    detail_type: Optional[str] = Query(
        None, description="Filter by detail type (CREATE, UPDATE, DELETE, etc.)"
    ),
    entity_type: Optional[str] = Query(
        None, description="Filter by entity type (for database logs)"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати список логів додатку з фільтрацією.
    Потрібні права адміністратора.
    """
    # Отримуємо контролер
    controller = get_logging_controller(db)

    # Отримуємо загальну кількість логів з цими фільтрами
    total = controller.count_application_logs(
        log_type=log_type,
        level=level,
        module=module,
        user_id=user_id,
        detail_type=detail_type,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
    )

    # Отримуємо самі логи
    logs = controller.get_application_logs(
        limit=limit,
        offset=offset,
        log_type=log_type,
        level=level,
        module=module,
        user_id=user_id,
        detail_type=detail_type,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
    )

    return ApplicationLogListResponse(
        items=logs,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/application/{log_id}", response_model=ApplicationLogRead)
async def get_application_log_by_id(
    log_id: str = Path(..., description="Application log ID"),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати лог додатку за ID.
    Потрібні права адміністратора.
    """
    controller = get_logging_controller(db)
    log = controller.get_application_log_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    return log


@router.get("/errors", response_model=ApplicationLogListResponse)
async def get_error_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    module: Optional[str] = Query(None, description="Filter by module name"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    exception_type: Optional[str] = Query(None, description="Filter by exception type"),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати список логів помилок з фільтрацією.
    Потрібні права адміністратора.
    """
    controller = get_logging_controller(db)

    # Помилки - це логи з рівнем ERROR
    total = controller.count_application_logs(
        level=LogLevel.ERROR.value,  # Змінено з LogType.ERROR.value на LogLevel.ERROR.value
        module=module,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    logs = controller.get_error_logs(
        limit=limit,
        offset=offset,
        module=module,
        user_id=user_id,
        exception_type=exception_type,
        start_date=start_date,
        end_date=end_date,
    )

    return ApplicationLogListResponse(
        items=logs,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/http", response_model=HttpLogListResponse)
async def get_http_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    is_request: Optional[bool] = Query(
        None, description="Filter by type (True - requests, False - responses)"
    ),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    path: Optional[str] = Query(None, description="Filter by path"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    min_processing_time: Optional[float] = Query(
        None, description="Filter by minimum processing time (ms)"
    ),
    max_processing_time: Optional[float] = Query(
        None, description="Filter by maximum processing time (ms)"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати список HTTP логів з фільтрацією.
    Потрібні права адміністратора.
    """
    controller = get_logging_controller(db)

    total = controller.count_http_logs(
        is_request=is_request,
        method=method,
        path=path,
        client_ip=client_ip,
        user_id=user_id,
        status_code=status_code,
        start_date=start_date,
        end_date=end_date,
    )

    logs = controller.get_http_logs(
        limit=limit,
        offset=offset,
        is_request=is_request,
        method=method,
        path=path,
        client_ip=client_ip,
        user_id=user_id,
        status_code=status_code,
        min_processing_time=min_processing_time,
        max_processing_time=max_processing_time,
        start_date=start_date,
        end_date=end_date,
    )

    return HttpLogListResponse(
        items=logs,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/http/{log_id}", response_model=HttpLogRead)
async def get_http_log_by_id(
    log_id: str = Path(..., description="HTTP log ID"),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати HTTP лог за ID.
    Потрібні права адміністратора.
    """
    controller = get_logging_controller(db)
    log = controller.get_http_log_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    return log


@router.get(
    "/http/request/{request_id}/with-response", response_model=RequestResponseDetail
)
async def get_request_with_response(
    request_id: str = Path(..., description="Request log ID"),
    current_user=Security(
        get_current_user, scopes=["admin"]
    ),  # Додано обмеження доступу
    db: Session = Depends(get_sync_db),  # Змінено на синхронну сесію
):
    """
    Отримати HTTP запит разом з відповіддю.
    Потрібні права адміністратора.
    """
    controller = get_logging_controller(db)
    data = controller.get_request_with_response(request_id)

    if not data:
        raise HTTPException(status_code=404, detail="Request log not found")

    return data
