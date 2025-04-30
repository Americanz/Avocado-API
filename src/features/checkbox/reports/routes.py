from fastapi import Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.core.loader_factory.api_factory.routes import create_api_router
from src.core.loader_factory.api_factory.controller import create_controller
from src.core.security.jwt import require_auth
from src.core.database.connection import get_db, get_sync_db
from src.features.checkbox.service.file_parser import parse_report_file
from src.features.checkbox.service.report_processor import (
    get_report_data_for_processing,
    parse_and_save_report_file,
    process_additional_report_data,
)
from .model import Report
from .schemas import ReportCreate, ReportUpdate, ReportResponse
from src.core.models.logging.providers import get_global_logger

# Отримуємо логер з резервним варіантом, якщо глобальний логер ще не ініціалізований
logger = get_global_logger()
# Якщо глобальний логер не ініціалізований, використовуємо стандартний logging
if logger is None:
    standard_logger = logging.getLogger("checkbox_routes")
    standard_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    standard_logger.addHandler(handler)

    # Створюємо об'єкт-замінник з тими ж методами, що й OptimizedLoguruService
    class FallbackLogger:
        def info(self, message, module=None, data=None):
            standard_logger.info(f"{module or ''}: {message} {data or ''}")

        def error(self, message, module=None, data=None, error=None):
            if error:
                standard_logger.exception(f"{module or ''}: {message} {data or ''}")
            else:
                standard_logger.error(f"{module or ''}: {message} {data or ''}")

        def warning(self, message, module=None, data=None):
            standard_logger.warning(f"{module or ''}: {message} {data or ''}")

        def debug(self, message, module=None, data=None):
            standard_logger.debug(f"{module or ''}: {message} {data or ''}")

    logger = FallbackLogger()

# Створюємо маршрутизатор з універсальними CRUD операціями
router = create_api_router(
    controller=create_controller(Report, ReportResponse),
    create_schema=ReportCreate,
    update_schema=ReportUpdate,
    response_schema=ReportResponse,
    prefix="/checkbox/reports",
    tags=["reports"],
    auth_dependency=require_auth,
    admin_dependency=require_auth,
    include_public_routes=True,  # Включити публічні маршрути (list, get)
    include_protected_routes=False,  # Вимкнути захищені маршрути (create, update, delete)
    include_admin_routes=False,  # Вимкнути адмін маршрути (bulk)
)

# # Тут можна додати додаткові спеціалізовані маршрути, наприклад:
# @router.get("/list/active",dependencies=[Depends(get_current_user)])
# async def get_active_companies(db: AsyncSession = Depends(get_db)):
#     """Отримати всі активні компанії."""
#     controller = CompanyController(Company, CompanyResponse)
#     companies = await controller.get_active_companies(db)
#     return Success(data=companies)


@router.post("/process-report-files")
async def process_report_files(
    goods_file: UploadFile = File(None),
    receipts_file: UploadFile = File(None),
    skip_if_processed: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Обробка файлів звітів - товарів та чеків.

    Args:
        goods_file: Файл звіту по товарах (Goods_*.xlsx)
        receipts_file: Файл звіту по чеках (receiptsReport_*.xlsx)
        skip_if_processed: Чи пропускати файли, які вже були оброблені
        db: Сесія бази даних
    """
    results = {"goods_file": None, "receipts_file": None, "success": False}

    try:
        # Отримуємо синхронну сесію для роботи з функціями, які вимагають синхронний API
        sync_db = get_sync_db()

        try:
            # Обробка звіту по товарах (основний файл)
            if goods_file:

                # Читаємо файл
                goods_data = await goods_file.read()

                # Обробляємо файл товарів як основний
                goods_result = parse_and_save_report_file(
                    goods_data, goods_file.filename, sync_db, "goods", skip_if_processed
                )

                results["goods_file"] = goods_result

                # Якщо обробка товарів успішна і є файл чеків, оновлюємо дані
                if goods_result["success"] and receipts_file:

                    # Читаємо файл чеків
                    receipts_data = await receipts_file.read()

                    # Парсимо файл чеків
                    report_data = parse_report_file(
                        receipts_data, receipts_file.filename
                    )

                    if "error" in report_data:
                        results["receipts_file"] = {
                            "success": False,
                            "error": report_data["error"],
                            "stage": "parsing",
                        }
                    else:
                        # Отримуємо дані з файлу
                        processed_data = get_report_data_for_processing(
                            report_data, receipts_file.filename
                        )

                        # Оновлюємо існуючі записи товарів даними з чеків
                        if "data" in processed_data and processed_data["data"]:
                            success = process_additional_report_data(
                                sync_db,
                                goods_result["report_id"],
                                processed_data["data"],
                            )

                            results["receipts_file"] = {
                                "success": success,
                                "message": (
                                    "Дані чеків успішно додані до товарів"
                                    if success
                                    else "Помилка при додаванні даних чеків"
                                ),
                                "rows_processed": len(processed_data["data"]),
                            }
                        else:
                            results["receipts_file"] = {
                                "success": False,
                                "error": "Файл чеків не містить даних",
                                "stage": "empty_data",
                            }

            # Якщо немає файлу товарів, але є файл чеків, обробляємо його окремо
            elif receipts_file:
                logger.info(
                    f"Обробка файлу чеків як окремого: {receipts_file.filename}",
                    module="report_processor",
                    data={"action": "process_receipts_file_standalone"},
                )

                # Читаємо файл
                receipts_data = await receipts_file.read()

                # Обробляємо файл чеків як окремий звіт
                receipts_result = parse_and_save_report_file(
                    receipts_data,
                    receipts_file.filename,
                    sync_db,
                    "payments",
                    skip_if_processed,
                )

                results["receipts_file"] = receipts_result

            # Визначаємо загальний результат
            if (not goods_file or results["goods_file"]["success"]) and (
                not receipts_file or results["receipts_file"]["success"]
            ):
                results["success"] = True

            return results
        finally:
            # Закриваємо синхронну сесію після використання
            sync_db.close()

    except Exception as e:
        # Додаємо перевірку на випадок, якщо логер не ініціалізований
        if logger:
            logger.error(
                f"Помилка при обробці файлів: {str(e)}",
                module="report_processor",
                data={"action": "process_files_error", "error": str(e)},
            )
        else:
            print(f"Logger not initialized. Error: {str(e)}")

        results["error"] = str(e)
        return results
