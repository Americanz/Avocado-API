"""
Example routes demonstrating the usage of LoguruService
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import time
import random

from src.core.models.logging import get_logger
from src.core.models.logging.providers import LoguruService

router = APIRouter(
    prefix="/log-demo",
    tags=["Демонстрація логування"],
    responses={404: {"description": "Not found"}},
)


@router.get("/info")
async def log_info(request: Request, message: str, logger: LoguruService = Depends(get_logger)) -> Dict[str, Any]:
    """
    Приклад логування інформаційного повідомлення
    
    Args:
        message: Повідомлення для логування
        
    Returns:
        Підтвердження логування
    """
    # Логуємо інформаційне повідомлення
    logger.info(
        message, 
        module="api.log_demo", 
        data={"client_ip": request.client.host, "user_agent": request.headers.get("user-agent")}
    )
    
    return {"status": "success", "message": f"Logged info message: {message}"}


@router.get("/levels")
async def log_all_levels(logger: LoguruService = Depends(get_logger)) -> Dict[str, Any]:
    """
    Демонстрація різних рівнів логування
    
    Returns:
        Підтвердження логування
    """
    logger.debug("Це DEBUG повідомлення", module="api.log_demo")
    logger.info("Це INFO повідомлення", module="api.log_demo")
    logger.warning("Це WARNING повідомлення", module="api.log_demo")
    logger.error("Це ERROR повідомлення", module="api.log_demo")
    logger.critical("Це CRITICAL повідомлення", module="api.log_demo")
    
    return {
        "status": "success",
        "message": "Logged messages with all severity levels"
    }


@router.get("/exception")
async def log_exception(logger: LoguruService = Depends(get_logger)) -> Dict[str, Any]:
    """
    Демонстрація логування виключення
    
    Returns:
        Ніколи не повертає результат, завжди викликає помилку
    """
    try:
        # Генеруємо помилку ділення на нуль
        result = 100 / 0
    except Exception as e:
        # Логуємо помилку з виключенням
        logger.error(
            "Сталася помилка при діленні на нуль", 
            exception=e, 
            module="api.log_demo",
            data={"operation": "division", "value": 100}
        )
        
        # Піднімаємо HTTP помилку для клієнта
        raise HTTPException(
            status_code=500,
            detail="Помилка при виконанні обчислень"
        )


@router.get("/performance")
async def log_performance(logger: LoguruService = Depends(get_logger)) -> Dict[str, Any]:
    """
    Демонстрація логування часу виконання операції
    
    Returns:
        Результат виконання операції та час виконання
    """
    # Початок вимірювання часу
    start_time = time.time()
    
    # Імітація тривалої операції
    time.sleep(random.uniform(0.1, 0.5))
    result = sum(i * i for i in range(1000000))
    
    # Закінчення вимірювання часу
    execution_time = (time.time() - start_time) * 1000  # в мілісекундах
    
    # Логуємо результат з часом виконання
    logger.info(
        f"Операція виконана за {execution_time:.2f} мс", 
        module="api.log_demo.performance", 
        data={"execution_time_ms": execution_time, "operation": "sum_of_squares"}
    )
    
    return {
        "status": "success",
        "execution_time_ms": execution_time,
        "result": result
    }


@router.get("/request-response")
async def log_request_response(request: Request, logger: LoguruService = Depends(get_logger)) -> Dict[str, Any]:
    """
    Демонстрація логування запиту та відповіді
    
    Returns:
        Дані запиту
    """
    # Логуємо запит
    request_log = logger.log_request(
        method=request.method,
        path=str(request.url),
        client_ip=request.client.host,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
        user_id=request.state.user.id if hasattr(request.state, "user") else None
    )
    
    # Готуємо відповідь
    response_data = {
        "status": "success",
        "message": "Запит та відповідь залоговано",
        "request_info": {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "headers": dict(request.headers)
        }
    }
    
    # Логуємо відповідь, якщо запит був успішно залогований
    if request_log:
        logger.log_response(
            request_id=request_log.id,
            status_code=200,
            body=response_data,
            processing_time_ms=random.uniform(10, 50)  # імітація часу обробки
        )
    
    return response_data