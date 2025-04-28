import json
import datetime
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.features.checkbox.reports.model import Report
from src.features.checkbox.product_sale import ProductSale

from src.features.checkbox.service.file_parser import (
    parse_report_file,
    CustomJSONEncoder,
)
from src.features.checkbox.utils.data_utils import (
    parse_item_data,
    parse_date,
    parse_datetime,
    count_processed_rows,
    calculate_file_hash,
)

from src.core.models.logging.providers import get_global_logger

# Отримуємо логер з резервним варіантом, якщо глобальний логер ще не ініціалізований
logger = get_global_logger()
# Якщо глобальний логер не ініціалізований, використовуємо стандартний logging
if logger is None:
    standard_logger = logging.getLogger("report_processor")
    standard_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
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


def get_product_sales(
    db: Session,
    report_id: Optional[int] = None,
    fiscal_number: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    product_code: Optional[str] = None,
    product_name: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> List[ProductSale]:
    """
    Отримує список товарних позицій з можливістю фільтрації.

    Args:
        db: Сесія бази даних.
        report_id: ID звіту для фільтрації.
        fiscal_number: Фіскальний номер для фільтрації.
        skip: Кількість записів для пропуску.
        limit: Максимальна кількість записів.
        product_code: Код товару для фільтрації.
        product_name: Назва товару для фільтрації.
        start_date: Початкова дата для фільтрації.
        end_date: Кінцева дата для фільтрації.

    Returns:
        List[ProductSale]: Список товарних позицій.
    """
    query = db.query(ProductSale)

    # Застосовуємо фільтри
    if report_id:
        query = query.filter(ProductSale.report_id == report_id)

    if fiscal_number:
        query = query.filter(ProductSale.fiscal_number == fiscal_number)

    if product_code:
        query = query.filter(ProductSale.product_code == product_code)

    if product_name:
        query = query.filter(ProductSale.product_name.ilike(f"%{product_name}%"))

    if start_date:
        query = query.filter(ProductSale.sale_date >= start_date)

    if end_date:
        query = query.filter(ProductSale.sale_date <= end_date)

    # Сортуємо за датою та ID
    query = query.order_by(ProductSale.sale_date.desc(), ProductSale.id.desc())

    # Застосовуємо пагінацію
    return query.offset(skip).limit(limit).all()


def detect_report_type(report_data: Dict[str, Any]) -> str:
    """
    Визначає тип звіту на основі наявних колонок.

    Args:
        report_data: Дані звіту після парсингу.

    Returns:
        str: Тип звіту ("goods", "payments" або "unknown").
    """
    # Перевіряємо наявність колонок
    if "columns" not in report_data:
        # Для Excel-файлів дані можуть бути в іншій структурі
        if "sheets" in report_data and report_data.get("sheet_names"):
            # Беремо колонки з першого аркуша
            sheet_name = report_data.get("sheet_names")[0]
            sheet_data = report_data.get("sheets", {}).get(sheet_name, {})
            columns = sheet_data.get("columns", [])
        else:
            # Якщо не можемо визначити колонки
            return "unknown"
    else:
        columns = report_data.get("columns", [])

    # Перелік колонок, характерних для різних типів звітів
    payment_indicators = [
        "Тип оплати",
        "Номер зміни",
        "Дата та час закриття зміни",
        "Повернення",
        "ID чека",
        "Дата/Час",
        "Фіскальний номер",
        "Сума (грн)",
    ]
    goods_indicators = ["УКТ ЗЕД", "Акцизна марка", "Штрих-код", "Найменування"]

    # Рахуємо кількість індикаторних колонок кожного типу
    payment_count = sum(1 for col in payment_indicators if col in columns)
    goods_count = sum(1 for col in goods_indicators if col in columns)

    # Логуємо знайдені індикатори
    logger.info(
        f"Виявлено індикатори типів звітів: товари - {goods_count}, оплати - {payment_count}",
        module="report_processor",
        data={
            "action": "detect_report_type",
            "goods_indicators": [col for col in goods_indicators if col in columns],
            "payment_indicators": [col for col in payment_indicators if col in columns],
        },
    )

    # Визначаємо тип на основі кількості індикаторів
    if payment_count > goods_count:
        return "payments"
    elif goods_count > payment_count:
        return "goods"
    else:
        # Якщо однакова кількість індикаторів або жодного не знайдено
        # Перевіряємо наявність критичних колонок
        if "Тип оплати" in columns:
            return "payments"
        elif "УКТ ЗЕД" in columns or "Найменування" in columns:
            return "goods"
        else:
            return "unknown"


def get_report_data_for_processing(
    report_data: Dict[str, Any], filename: str
) -> Dict[str, Any]:
    """
    Отримує дані звіту у форматі, придатному для обробки.

    Args:
        report_data: Дані звіту
        filename: Назва файлу для визначення формату

    Returns:
        Dict[str, Any]: Підготовлені дані для обробки
    """
    if filename.lower().endswith(".xlsx"):
        # Для Excel беремо дані з першого аркуша
        if "sheets" not in report_data or not report_data["sheets"]:
            return {"data": [], "columns": []}

        sheet_names = report_data.get("sheet_names", [])

        # Якщо аркушів немає або їх забагато, беремо перший
        if not sheet_names:
            sheet_name = next(iter(report_data["sheets"]))
        else:
            sheet_name = sheet_names[0]  # Використовуємо перший аркуш

        sheet_data = report_data["sheets"].get(sheet_name)
        if not sheet_data or not sheet_data.get("data"):
            return {"data": [], "columns": []}

        # Формуємо дані першого аркуша для обробки
        return {"data": sheet_data["data"], "columns": sheet_data.get("columns", [])}
    else:
        # Для CSV/JSON повертаємо дані напряму
        return report_data


def check_file_already_processed(
    db: Session, filename: str, rows_count: int, file_hash: Optional[str] = None
) -> Tuple[bool, Optional[int]]:
    """
    Перевіряє, чи вже оброблявся цей файл.

    Args:
        db: Сесія бази даних
        filename: Назва файлу
        rows_count: Кількість рядків у файлі
        file_hash: Хеш вмісту файлу (опціонально)

    Returns:
        Tuple[bool, Optional[int]]: (Чи був файл оброблений раніше, ID звіту якщо так)
    """
    # Шукаємо звіт з такою ж назвою файлу
    query = db.query(Report).filter(
        Report.filename == filename,
        Report.is_processed == True,
        Report.processing_status == "completed",
    )

    # Якщо є хеш файлу, використовуємо його для точнішого пошуку
    if file_hash:
        query = query.filter(Report.file_hash == file_hash)

    # Знаходимо останній успішно оброблений звіт
    existing_report = query.order_by(Report.id.desc()).first()

    if existing_report and existing_report.rows_count == rows_count:
        return True, existing_report.id

    return False, None


def parse_and_save_report_file(
    file_data: bytes,
    filename: str,
    db: Session,
    report_type: Optional[str] = None,
    skip_if_processed: bool = True,
) -> Dict[str, Any]:
    """
    Парсинг файлу звіту і збереження даних у БД з автовизначенням типу звіту
    та перевіркою на повторну обробку.
    """
    start_time = time.time()

    try:
        logger.info(
            f"Початок обробки файлу: {filename}",
            module="report_processor",
            data={
                "action": "parse_and_save",
                "filename": filename,
                "report_type": report_type,
            },
        )

        # Парсимо файл спочатку, щоб отримати кількість рядків
        report_data = parse_report_file(file_data, filename)

        # Перевіряємо наявність помилок при парсингу
        if "error" in report_data:
            logger.error(
                f"Помилка при парсингу файлу: {report_data['error']}",
                module="report_processor",
                data={
                    "action": "parse_error",
                    "filename": filename,
                    "error": report_data["error"],
                },
            )
            return {"success": False, "error": report_data["error"]}

        # Рахуємо кількість рядків
        rows_count = count_processed_rows(report_data, filename)

        # Обчислюємо хеш файлу для порівняння
        file_hash = calculate_file_hash(file_data)

        # Перевіряємо, чи вже був оброблений цей файл
        if skip_if_processed:
            already_processed, existing_report_id = check_file_already_processed(
                db, filename, rows_count, file_hash
            )

            if already_processed:
                logger.info(
                    f"Файл {filename} вже був оброблений раніше, пропускаємо",
                    module="report_processor",
                    data={
                        "action": "file_skipped",
                        "filename": filename,
                        "rows_count": rows_count,
                        "existing_report_id": existing_report_id,
                    },
                )

                return {
                    "success": True,
                    "report_id": existing_report_id,
                    "status": "skipped",
                    "rows_processed": rows_count,
                    "message": "Файл вже був оброблений раніше",
                }

        # Визначаємо тип звіту, якщо він не вказаний
        if report_type is None:
            report_type = detect_report_type(report_data)
            logger.info(
                f"Автоматично визначено тип звіту: {report_type}",
                module="report_processor",
                data={"action": "detected_report_type", "report_type": report_type},
            )

        # Створюємо запис звіту в БД
        now = datetime.datetime.now()

        # Замість повних даних зберігаємо тільки метадані у вигляді JSON
        metadata = {
            "filename": filename,
            "rows_count": rows_count,
            "file_hash": file_hash,
            "report_type": report_type,
            "processing_date": now.isoformat(),
            "columns": report_data.get("columns", []),
        }

        # Якщо це Excel, додаємо інформацію про аркуші
        if "sheet_names" in report_data:
            metadata["sheet_names"] = report_data.get("sheet_names", [])
            metadata["sheets_count"] = len(report_data.get("sheet_names", []))

        # Додаємо інформацію про підсумки, якщо вона є
        if "summary" in report_data:
            summary = report_data.get("summary", {})
            # Зберігаємо тільки загальні цифри, а не детальні дані
            if isinstance(summary, dict):
                metadata["summary"] = {
                    "rows": summary.get("rows", 0),
                    "columns": summary.get("columns", 0),
                    "totals": summary.get("totals", {}),
                }

        # Створюємо запис звіту без повних даних
        db_report = Report(
            from_date=now - datetime.timedelta(days=1),
            to_date=now,
            cash_register_id="test-cash-register",
            emails=json.dumps(["test@example.com"]),
            processing_status="processing",
            report_data=json.dumps(
                metadata, cls=CustomJSONEncoder
            ),  # Зберігаємо тільки метадані
            report_type=report_type,
            filename=filename,
            file_hash=file_hash,
            rows_count=rows_count,
        )

        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        logger.info(
            f"Створено запис звіту в БД, ID: {db_report.id}",
            module="report_processor",
            data={"action": "report_created", "report_id": db_report.id},
        )

        # Підготовка даних для обробки
        processed_data = get_report_data_for_processing(report_data, filename)

        # Зберігаємо дані в таблицю товарних позицій
        logger.info(
            f"Збереження даних звіту в БД",
            module="report_processor",
            data={
                "action": "saving_data",
                "report_id": db_report.id,
                "report_type": report_type,
            },
        )

        # Збереження даних
        success = save_report_data(db, db_report.id, processed_data, report_type)

        # Зберігаємо час виконання
        processing_time = time.time() - start_time
        db_report.processing_time = processing_time

        if success:
            db_report.processing_status = "completed"
            db_report.is_processed = True

            logger.info(
                f"Дані звіту успішно збережено за {processing_time:.2f} сек",
                module="report_processor",
                data={
                    "action": "data_saved",
                    "report_id": db_report.id,
                    "processing_time": processing_time,
                },
            )
        else:
            db_report.processing_status = "failed"
            db_report.error_message = "Помилка при збереженні даних"

            logger.error(
                f"Помилка при збереженні даних звіту",
                module="report_processor",
                data={"action": "save_failed", "report_id": db_report.id},
            )

        db.commit()

        return {
            "success": True,
            "report_id": db_report.id,
            "report_type": report_type,
            "status": db_report.processing_status,
            "rows_processed": rows_count,
            "processing_time": processing_time,
        }

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            f"Непередбачена помилка при обробці файлу: {str(e)}",
            module="report_processor",
            data={"action": "unexpected_error", "processing_time": processing_time},
            error=e,
        )

        # Якщо запис звіту вже створено, оновимо статус
        if "db_report" in locals() and db_report.id:
            db_report.processing_status = "failed"
            db_report.error_message = f"Непередбачена помилка: {str(e)}"
            db_report.processing_time = processing_time
            db.commit()
            return {"success": False, "error": str(e), "report_id": db_report.id}
        else:
            return {"success": False, "error": str(e)}


def process_additional_report_data(
    db: Session, report_id: int, data: List[Dict[str, Any]]
) -> bool:
    """
    Обробка додаткових даних для звіту.

    Args:
        db: Сесія бази даних
        report_id: ID звіту
        data: Додаткові дані

    Returns:
        bool: Успішність обробки
    """
    try:
        # Перевірка та підготовка даних
        cleaned_data = [{k.strip(): v for k, v in item.items()} for item in data]

        # Оновлення існуючих записів
        return update_product_sales_with_additional_info(db, report_id, cleaned_data)
    except Exception as e:
        logger.error(
            f"Помилка при обробці додаткових даних: {str(e)}",
            module="report_processor",
            data={"action": "process_additional_error"},
            error=e,
        )
        return False


def save_report_data(
    db: Session, report_id: int, report_data: Dict[str, Any], report_type: str = "goods"
) -> bool:
    """
    Зберігає дані звіту в таблицю товарних позицій, уникаючи дублікатів.
    Працює з обома типами звітів: Excel і CSV/JSON.

    Args:
        db: Сесія бази даних.
        report_id: ID звіту.
        report_data: Дані звіту в обробленому форматі.
        report_type: Тип звіту ("goods" для товарів, "payments" для оплат).

    Returns:
        bool: True, якщо збереження пройшло успішно, False - інакше.
    """
    try:
        # Перевіряємо чи є звіт
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return False

        # Перевіряємо чи є дані товарів
        if "data" not in report_data or not report_data["data"]:
            return False

        # Рахуємо статистику обробки
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        # Оновлюємо тип звіту в БД
        report.report_type = report_type

        # Опрацьовуємо кожен рядок даних
        for item in report_data["data"]:
            try:
                # Парсимо всі дані з запису в правильні типи
                parsed_item = parse_item_data(item, "goods")

                # Перевіряємо наявність ключових полів
                if (
                    not parsed_item["receipt_numbers"]
                    or not parsed_item["product_code"]
                ):
                    logger.warning(
                        f"Пропущено рядок через відсутність ключових полів",
                        module="report_processor",
                        data={
                            "action": "missing_key_fields",
                            "receipt": parsed_item["receipt_numbers"],
                            "product": parsed_item["product_code"],
                        },
                    )
                    stats["skipped"] += 1
                    continue

                # Шукаємо існуючий запис
                query = db.query(ProductSale).filter(
                    ProductSale.receipt_numbers == parsed_item["receipt_numbers"],
                    ProductSale.product_code == parsed_item["product_code"],
                )

                # Додаємо фільтр по даті продажу, якщо вона є
                if parsed_item["sale_date"]:
                    query = query.filter(
                        ProductSale.sale_date == parsed_item["sale_date"]
                    )

                # Додаємо фільтр по кількості та сумі для більшої точності
                if parsed_item["quantity"] > 0:
                    query = query.filter(
                        ProductSale.quantity == parsed_item["quantity"]
                    )
                if parsed_item["total_amount"] > 0:
                    query = query.filter(
                        ProductSale.total_amount == parsed_item["total_amount"]
                    )

                existing_sale = query.first()

                # Якщо запис існує, оновлюємо його
                if existing_sale:
                    # Логуємо оновлення
                    logger.info(
                        f"Оновлення існуючого запису: {existing_sale.id}",
                        module="report_processor",
                        data={
                            "action": "update_existing_sale",
                            "sale_id": existing_sale.id,
                            "receipt": parsed_item["receipt_numbers"],
                            "product": parsed_item["product_code"],
                        },
                    )

                    # Оновлюємо поля в залежності від типу звіту
                    if report_type == "goods":
                        # Оновлення полів з першого звіту (товари)
                        if (
                            parsed_item["product_name"]
                            and not existing_sale.product_name
                        ):
                            existing_sale.product_name = parsed_item["product_name"]

                        if (
                            parsed_item["ukt_zed_code"]
                            and not existing_sale.ukt_zed_code
                        ):
                            existing_sale.ukt_zed_code = parsed_item["ukt_zed_code"]

                        if parsed_item["barcode"] and not existing_sale.barcode:
                            existing_sale.barcode = parsed_item["barcode"]

                        if (
                            parsed_item["operation_type"]
                            and not existing_sale.operation_type
                        ):
                            existing_sale.operation_type = parsed_item["operation_type"]

                        # Оновлення числових значень, якщо вони ще не встановлені
                        if not existing_sale.price:
                            existing_sale.price = parsed_item["price"]

                        if not existing_sale.amount:
                            existing_sale.amount = parsed_item["amount"]

                        if not existing_sale.receipts_count:
                            existing_sale.receipts_count = parsed_item["receipts_count"]

                        # Податкова інформація
                        if parsed_item["tax_name"] and not existing_sale.tax_name:
                            existing_sale.tax_name = parsed_item["tax_name"]

                        if parsed_item["tax_rate"] and not existing_sale.tax_rate:
                            existing_sale.tax_rate = parsed_item["tax_rate"]

                        # Знижки та націнки
                        if not existing_sale.additional_fee:
                            existing_sale.additional_fee = parsed_item["additional_fee"]

                        if not existing_sale.discount_amount:
                            existing_sale.discount_amount = parsed_item[
                                "discount_amount"
                            ]

                        if not existing_sale.markup_amount:
                            existing_sale.markup_amount = parsed_item["markup_amount"]

                        # Інформація про касу
                        if (
                            parsed_item["fiscal_number"]
                            and not existing_sale.fiscal_number
                        ):
                            existing_sale.fiscal_number = parsed_item["fiscal_number"]

                        if (
                            parsed_item["register_address"]
                            and not existing_sale.register_address
                        ):
                            existing_sale.register_address = parsed_item[
                                "register_address"
                            ]

                        if (
                            parsed_item["excise_stamp"]
                            and not existing_sale.excise_stamp
                        ):
                            existing_sale.excise_stamp = parsed_item["excise_stamp"]

                    elif report_type == "payments":
                        # Оновлення полів з другого звіту (оплати)
                        if (
                            parsed_item["sale_datetime"]
                            and not existing_sale.sale_datetime
                        ):
                            existing_sale.sale_datetime = parsed_item["sale_datetime"]

                        if (
                            parsed_item["shift_number"]
                            and not existing_sale.shift_number
                        ):
                            existing_sale.shift_number = parsed_item["shift_number"]

                        if (
                            parsed_item["payment_type"]
                            and not existing_sale.payment_type
                        ):
                            existing_sale.payment_type = parsed_item["payment_type"]

                        if parsed_item["is_return"] != existing_sale.is_return:
                            existing_sale.is_return = parsed_item["is_return"]

                    stats["updated"] += 1

                else:
                    # Якщо запис не існує, створюємо новий з усіма наявними даними
                    product_sale = ProductSale(
                        report_id=report_id,
                        product_code=parsed_item["product_code"],
                        product_name=parsed_item["product_name"],
                        ukt_zed_code=parsed_item["ukt_zed_code"],
                        barcode=parsed_item["barcode"],
                        receipt_numbers=parsed_item["receipt_numbers"],
                        operation_type=parsed_item["operation_type"],
                        price=parsed_item["price"],
                        quantity=parsed_item["quantity"],
                        amount=parsed_item["amount"],
                        receipts_count=parsed_item["receipts_count"],
                        tax_name=parsed_item["tax_name"],
                        tax_rate=parsed_item["tax_rate"],
                        additional_fee=parsed_item["additional_fee"],
                        discount_amount=parsed_item["discount_amount"],
                        markup_amount=parsed_item["markup_amount"],
                        total_amount=parsed_item["total_amount"],
                        sale_date=parsed_item["sale_date"],
                        sale_datetime=parsed_item["sale_datetime"],
                        fiscal_number=parsed_item["fiscal_number"],
                        register_address=parsed_item["register_address"],
                        excise_stamp=parsed_item["excise_stamp"],
                        shift_number=parsed_item["shift_number"],
                        payment_type=parsed_item["payment_type"],
                        is_return=parsed_item["is_return"],
                    )

                    db.add(product_sale)
                    stats["created"] += 1

            except Exception as e:
                logger.error(
                    f"Помилка при обробці запису: {str(e)}",
                    module="report_processor",
                    data={
                        "action": "process_item_error",
                        "receipt": (
                            parsed_item["receipt_numbers"]
                            if "parsed_item" in locals()
                            else None
                        ),
                        "product": (
                            parsed_item["product_code"]
                            if "parsed_item" in locals()
                            else None
                        ),
                    },
                    error=e,
                )
                stats["errors"] += 1
                continue

        # Зберігаємо зміни
        db.commit()

        # Логуємо статистику
        logger.info(
            f"Статистика обробки звіту: створено - {stats['created']}, оновлено - {stats['updated']}, пропущено - {stats['skipped']}, помилок - {stats['errors']}",
            module="report_processor",
            data={"action": "save_report_stats", "stats": stats},
        )

        return True
    except Exception as e:
        db.rollback()
        logger.error(
            f"Помилка при збереженні даних звіту: {str(e)}",
            module="report_processor",
            data={"action": "save_data_error"},
            error=e,
        )
        return False


def update_product_sales_with_additional_info(
    db: Session,
    report_id: int,
    additional_data: List[Dict[str, Any]],
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> bool:
    """
    Оновлює додаткову інформацію для раніше збережених товарних позицій з фільтрацією за датами.

    Args:
        db: Сесія бази даних
        report_id: ID звіту
        additional_data: Додаткові дані для оновлення
        start_date: Початкова дата для фільтрації (включно)
        end_date: Кінцева дата для фільтрації (включно)

    Returns:
        bool: Успішність оновлення
    """
    try:
        # Визначаємо дати з додаткових даних, якщо не вказані
        if start_date is None or end_date is None:
            dates = []
            datetimes = []

            for item in additional_data:
                # Пропускаємо записи про повернення
                if item.get("Тип") == "SERVICE_OUT":
                    continue

                parsed = parse_item_data(item, "payments")

                if (
                    parsed["sale_datetime"]
                    and parsed["sale_datetime"] != datetime.datetime.now()
                ):
                    datetimes.append(parsed["sale_datetime"])
                    dates.append(parsed["sale_datetime"].date())

            # Визначаємо діапазон дат
            if dates:
                if not start_date:
                    start_date = min(dates)
                if not end_date:
                    end_date = max(dates)

        # Перетворюємо дати в початок і кінець дня для повного охоплення
        start_datetime = (
            datetime.datetime.combine(start_date, datetime.time.min)
            if start_date
            else None
        )
        end_datetime = (
            datetime.datetime.combine(end_date, datetime.time.max) if end_date else None
        )

        # Будуємо запит з фільтрацією за датами
        query = db.query(ProductSale)

        # Фільтруємо за датою продажу або датою і часом закриття зміни
        if start_date:
            # Використовуємо OR для пошуку за датою продажу АБО за датою і часом закриття зміни
            date_filter = ProductSale.sale_date >= start_date
            datetime_filter = ProductSale.sale_datetime >= start_datetime
            query = query.filter(or_(date_filter, datetime_filter))

        if end_date:
            date_filter = ProductSale.sale_date <= end_date
            datetime_filter = ProductSale.sale_datetime <= end_datetime
            query = query.filter(or_(date_filter, datetime_filter))

        # Логуємо параметри запиту
        logger.info(
            f"Застосовано фільтр за датами: з {start_date} по {end_date}",
            module="report_processor",
            data={
                "action": "date_filter",
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "start_datetime": (
                    start_datetime.isoformat() if start_datetime else None
                ),
                "end_datetime": end_datetime.isoformat() if end_datetime else None,
            },
        )

        # Отримуємо відфільтровані записи
        existing_sales = query.all()

        # Статистика оновлення
        stats = {"found": 0, "not_found": 0, "errors": 0, "total": len(additional_data)}

        # Створюємо словники для пошуку
        primary_dict = {}
        for sale in existing_sales:
            key = (sale.product_code, sale.receipt_numbers, sale.quantity)
            if key not in primary_dict:
                primary_dict[key] = []
            primary_dict[key].append(sale)

        secondary_dict = {}
        for sale in existing_sales:
            key = (sale.product_code, sale.receipt_numbers)
            if key not in secondary_dict:
                secondary_dict[key] = []
            secondary_dict[key].append(sale)

        receipt_dict = {}
        for sale in existing_sales:
            if sale.receipt_numbers not in receipt_dict:
                receipt_dict[sale.receipt_numbers] = []
            receipt_dict[sale.receipt_numbers].append(sale)

        # Логуємо словники для діагностики
        logger.info(
            f"Знайдено {len(existing_sales)} існуючих записів для оновлення",
            module="report_processor",
            data={
                "action": "update_sales_stats",
                "report_id": report_id,
                "existing_sales": len(existing_sales),
                "primary_keys": len(primary_dict),
                "secondary_keys": len(secondary_dict),
                "receipt_keys": len(receipt_dict),
            },
        )

        # Оновлюємо інформацію
        for item in additional_data:
            try:
                # Парсимо дані
                parsed = parse_item_data(item, "payments")

                # Перевіряємо, чи є ключові поля
                if not parsed["receipt_numbers"]:
                    stats["not_found"] += 1
                    logger.warning(
                        f"Відсутній номер чеку для запису",
                        module="report_processor",
                        data={
                            "action": "missing_key",
                            "product_code": parsed["product_code"],
                        },
                    )
                    continue

                sales_found = []

                # 1. Спочатку за основним ключем
                primary_key = (
                    parsed["product_code"],
                    parsed["receipt_numbers"],
                    parsed["quantity"],
                )
                if primary_dict and primary_key in primary_dict:
                    sales_found.extend(primary_dict[primary_key])
                # 2. Якщо не знайдено, спробуємо за вторинним ключем
                elif (
                    secondary_dict
                    and (parsed["product_code"], parsed["receipt_numbers"])
                    in secondary_dict
                ):
                    sales_found.extend(
                        secondary_dict[
                            (parsed["product_code"], parsed["receipt_numbers"])
                        ]
                    )
                # 3. Якщо все ще не знайдено, спробуємо за номером чеку
                elif receipt_dict and parsed["receipt_numbers"] in receipt_dict:
                    sales_found.extend(receipt_dict[parsed["receipt_numbers"]])

                # Оновлюємо всі знайдені записи
                for sale in sales_found:
                    # Знайдено відповідний запис
                    if sale:
                        # Оновлюємо додаткові поля
                        stats["found"] += 1

                        # Оновлюємо номер зміни, якщо він є
                        if parsed["shift_number"]:
                            sale.shift_number = parsed["shift_number"]

                        # Оновлюємо тип оплати, якщо він є
                        if parsed["payment_type"]:
                            sale.payment_type = parsed["payment_type"]

                        # Оновлюємо посилання на чек, якщо воно є
                        if parsed["check_link"]:
                            sale.check_link = parsed["check_link"]

                        # Оновлюємо ознаку повернення
                        sale.is_return = parsed["is_return"]

                        # Додаємо дату закриття зміни, якщо є
                        if (
                            parsed["sale_datetime"]
                            and parsed["sale_datetime"] != datetime.datetime.now()
                        ):
                            sale.sale_datetime = parsed["sale_datetime"]
                    else:
                        stats["not_found"] += 1
                        logger.warning(
                            f"Запис не знайдено для оновлення",
                            module="report_processor",
                            data={
                                "action": "record_not_found",
                                "product_code": parsed["product_code"],
                                "receipt_numbers": parsed["receipt_numbers"],
                                "quantity": parsed["quantity"],
                            },
                        )
            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    f"Помилка при оновленні запису: {str(e)}",
                    module="report_processor",
                    data={"action": "update_item_error"},
                    error=e,
                )
                continue

        # Зберігаємо зміни
        db.commit()

        # Логуємо статистику
        logger.info(
            f"Статистика оновлення: знайдено - {stats['found']}, не знайдено - {stats['not_found']}, помилок - {stats['errors']}, всього - {stats['total']}",
            module="report_processor",
            data={"action": "update_stats", "stats": stats},
        )

        return stats["found"] > 0
    except Exception as e:
        db.rollback()
        logger.error(
            f"Помилка при оновленні даних продажів: {str(e)}",
            module="report_processor",
            data={"action": "update_sales_error"},
            error=e,
        )
        return False
