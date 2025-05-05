import datetime
import hashlib
import pandas as pd
from typing import Any, Optional, Union, TypeVar, Dict

# Заменяем импорт loguru на наш адаптер
from src.features.checkbox.utils.logger_adapter import checkbox_logger as logger

T = TypeVar('T')  # Для типізації функції safe_get


def safe_get(data: Dict[str, Any], key: str, default_value: T = None, convert_to_type=None) -> T:
    """
    Безпечно отримує значення з словника з можливістю конвертації типу.

    Args:
        data: Словник з даними
        key: Ключ для отримання значення
        default_value: Значення за замовчуванням, якщо ключа немає або значення None
        convert_to_type: Функція для конвертації типу (str, int, float, тощо)

    Returns:
        Значення відповідного типу або default_value
    """
    # Отримуємо значення або None
    value = data.get(key)

    # Якщо значення None, повертаємо значення за замовчуванням
    if value is None:
        return default_value

    # Якщо потрібна конвертація типу
    if convert_to_type:
        try:
            return convert_to_type(value)
        except (ValueError, TypeError):
            return default_value

    return value


def parse_string(data: Dict[str, Any], key: str, default_value: str = "") -> str:
    """
    Отримує значення як рядок.

    Args:
        data: Словник з даними
        key: Ключ для отримання значення
        default_value: Значення за замовчуванням

    Returns:
        str: Значення як рядок
    """
    return safe_get(data, key, default_value, str)


def parse_int(data: Dict[str, Any], key: str, default_value: int = 0) -> int:
    """
    Отримує значення як ціле число.

    Args:
        data: Словник з даними
        key: Ключ для отримання значення
        default_value: Значення за замовчуванням

    Returns:
        int: Значення як ціле число
    """
    return safe_get(data, key, default_value, int)


def parse_float(data: Dict[str, Any], key: str, default_value: float = 0.0) -> float:
    """
    Отримує значення як число з плаваючою точкою.

    Args:
        data: Словник з даними
        key: Ключ для отримання значення
        default_value: Значення за замовчуванням

    Returns:
        float: Значення як число з плаваючою точкою
    """
    # Спеціальна обробка для можливих форматів чисел з комами
    value = data.get(key)

    if value is None:
        return default_value

    try:
        if isinstance(value, str):
            # Замінюємо коми на крапки і видаляємо пробіли
            value = value.replace(',', '.').replace(' ', '')
        return float(value)
    except (ValueError, TypeError):
        return default_value


def parse_boolean(data: Dict[str, Any], key: str, default_value: bool = False) -> bool:
    """
    Отримує значення як булеве значення.

    Args:
        data: Словник з даними
        key: Ключ для отримання значення
        default_value: Значення за замовчуванням

    Returns:
        bool: Значення як булеве значення
    """
    value = data.get(key)

    if value is None:
        return default_value

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ["true", "так", "yes", "1"]

    try:
        return bool(value)
    except (ValueError, TypeError):
        return default_value


def parse_date(value: Any, default_date: Optional[datetime.date] = None, field_name: Optional[str] = None) -> datetime.date:
    """
    Функція для універсального парсингу дати з різних форматів.

    Args:
        value: Значення дати (str, datetime, Timestamp, тощо)
        default_date: Дата за замовчуванням, якщо парсинг не вдався
        field_name: Назва поля для логування (опціонально)

    Returns:
        datetime.date: Розпарсена дата або default_date
    """
    if default_date is None:
        default_date = datetime.date.today()

    if value is None:
        return default_date

    try:
        if isinstance(value, str):
            # Спробуємо fromisoformat для ISO форматів
            try:
                # Для форматів типу '2023-01-01' або '2023-01-01T12:00:00'
                return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            except ValueError:
                # Спробуємо різні формати дати
                formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d", "%m/%d/%Y"]
                for fmt in formats:
                    try:
                        return datetime.datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue

                # Якщо жоден формат не підійшов, логуємо помилку
                if field_name:
                    logger.warning(
                        component="date_parser",
                        action="date_format_error",
                        message=f"Не вдалося розпарсити дату для поля {field_name}",
                        data={"value": value}
                    )

                return default_date

        elif isinstance(value, datetime.datetime):
            return value.date()

        elif isinstance(value, datetime.date):
            return value

        elif isinstance(value, pd.Timestamp):
            return value.date()

        else:
            if field_name:
                logger.warning(
                    component="date_parser",
                    action="unknown_date_type",
                    message=f"Невідомий тип дати для поля {field_name}",
                    data={"type": type(value).__name__}
                )
            return default_date

    except Exception as e:
        if field_name:
            logger.error(
                component="date_parser",
                action="date_parse_error",
                message=f"Помилка при парсингу дати для поля {field_name}: {str(e)}",
                data={"value": value},
                error=e
            )
        return default_date


def parse_datetime(value: Any, default_datetime: Optional[datetime.datetime] = None, field_name: Optional[str] = None) -> datetime.datetime:
    """
    Функція для універсального парсингу дати і часу з різних форматів.

    Args:
        value: Значення дати та часу (str, datetime, Timestamp, тощо)
        default_datetime: Дата та час за замовчуванням, якщо парсинг не вдався
        field_name: Назва поля для логування (опціонально)

    Returns:
        datetime.datetime: Розпарсені дата та час або default_datetime
    """
    if default_datetime is None:
        default_datetime = datetime.datetime.now()

    if value is None:
        return default_datetime

    try:
        if isinstance(value, str):
            # Спробуємо fromisoformat для ISO форматів
            try:
                # Для форматів типу '2023-01-01T12:00:00' або '2023-01-01 12:00:00'
                return datetime.datetime.fromisoformat(value.replace('Z', '+00:00').replace(' ', 'T'))
            except ValueError:
                # Спробуємо різні формати дати та часу
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%d.%m.%Y %H:%M:%S",
                    "%d/%m/%Y %H:%M:%S",
                    "%Y/%m/%d %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S"
                ]
                for fmt in formats:
                    try:
                        return datetime.datetime.strptime(value, fmt)
                    except ValueError:
                        continue

                # Якщо це лише дата без часу
                date_val = parse_date(value, field_name=field_name)
                if date_val != default_datetime.date():
                    return datetime.datetime.combine(date_val, datetime.time.min)

                # Якщо жоден формат не підійшов, логуємо помилку
                if field_name:
                    logger.warning(
                        component="date_parser",
                        action="datetime_format_error",
                        message=f"Не вдалося розпарсити дату та час для поля {field_name}",
                        data={"value": value}
                    )

                return default_datetime

        elif isinstance(value, datetime.datetime):
            return value

        elif isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time.min)

        elif isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        else:
            if field_name:
                logger.warning(
                    component="date_parser",
                    action="unknown_datetime_type",
                    message=f"Невідомий тип дати та часу для поля {field_name}",
                    data={"type": type(value).__name__}
                )
            return default_datetime

    except Exception as e:
        if field_name:
            logger.error(
                component="date_parser",
                action="datetime_parse_error",
                message=f"Помилка при парсингу дати та часу для поля {field_name}: {str(e)}",
                data={"value": value},
                error=e
            )
        return default_datetime


def parse_item_data(item: Dict[str, Any], report_type: str = "goods") -> Dict[str, Any]:
    """
    Парсить дані з запису звіту, перетворюючи їх у відповідні типи.

    Args:
        item: Запис даних звіту
        report_type: Тип звіту ('goods' або 'payments')

    Returns:
        Dict[str, Any]: Оброблені дані з правильними типами
    """
    parsed_data = {
        # Спільні поля для обох типів звітів
        "product_code": parse_string(item, "Код товару"),
        "barcode": parse_string(item, "Штрих-код"),
        "fiscal_number": parse_string(item, "Фіскальний номер ПРРО"),
        "quantity": parse_float(item, "Кількість", 0.0),
        "total_amount": parse_float(item, "Загальна сума", 0.0),
        "is_return": parse_boolean(item, "Повернення", False),
        "shift_number": parse_int(item, "Номер зміни", 0),
        "payment_type": parse_string(item, "Тип оплати"),
    }

    # Обробка ідентифікатора чека (різні назви в різних файлах)
    if "Фіскальні номери чеків" in item:
        parsed_data["receipt_numbers"] = parse_string(item, "Фіскальні номери чеків")
    elif "Фіскальний номер" in item:
        parsed_data["receipt_numbers"] = parse_string(item, "Фіскальний номер")
    # elif "ID чека" in item:
    #     parsed_data["receipt_numbers"] = parse_string(item, "ID чека")
    else:
        parsed_data["receipt_numbers"] = ""  # Порожнє значення за замовчуванням

    # Обробка дати (різні назви в різних файлах)
    if "Дата продажу" in item:
        parsed_data["sale_date"] = parse_date(item.get("Дата продажу"), field_name="Дата продажу")
    else:
        parsed_data["sale_date"] = None

    # Обробка дати та часу (різні назви в різних файлах)
    if "Дата та час закриття зміни" in item:
        parsed_data["sale_datetime"] = parse_datetime(item.get("Дата та час закриття зміни"), field_name="Дата та час закриття зміни")
    elif "Дата/Час" in item:
        parsed_data["sale_datetime"] = parse_datetime(item.get("Дата/Час"), field_name="Дата/Час")
    else:
        parsed_data["sale_datetime"] = None

    # Поля, специфічні для звіту товарів
    if report_type == "goods":
        parsed_data.update({
            "product_name": parse_string(item, "Найменування"),
            "ukt_zed_code": parse_string(item, "УКТ ЗЕД"),
            "operation_type": parse_string(item, "Вид операції"),
            "tax_name": parse_string(item, "Назва податку"),
            "tax_rate": parse_string(item, "Податок"),
            "register_address": parse_string(item, "Адреса каси"),
            "excise_stamp": parse_string(item, "Акцизна марка"),
            "price": parse_float(item, "Вартість", 0.0),
            "amount": parse_float(item, "Сума", 0.0),
            "receipts_count": parse_int(item, "Чеків з товаром", 0),
            "additional_fee": parse_float(item, "Дод. збір", 0.0),
            "discount_amount": parse_float(item, "Сума знижок", 0.0),
            "markup_amount": parse_float(item, "Сума націнок", 0.0),
        })

    # Поля, специфічні для звіту оплат
    elif report_type == "payments":
        parsed_data.update({
            "check_link": parse_string(item, "Посилання"),
            "amount_with_rounding": parse_float(item, "Сума з урахуванням заокруглення (грн)", 0.0),
            "local_prro_number": parse_string(item, "Локальний номер ПРРО"),
            "is_offline": parse_boolean(item, "Офлайн", False),
            "check_discount": parse_float(item, "Знижка на чек", 0.0),
            "check_header": parse_string(item, "Шапка"),
            "service_info": parse_string(item, "Службова інформація"),
        })

    return parsed_data


def count_processed_rows(report_data: Dict[str, Any], filename: str) -> int:
    """
    Підраховує кількість оброблених рядків в звіті.

    Args:
        report_data: Оброблені дані звіту
        filename: Назва файлу для визначення формату

    Returns:
        int: Кількість оброблених рядків
    """
    # Для Excel файлів
    if filename.lower().endswith(".xlsx"):
        # Якщо є дані про аркуші
        if "sheets" in report_data and isinstance(report_data["sheets"], dict):
            return sum(
                len(sheet_data.get("data", []))
                for sheet_data in report_data.get("sheets", {}).values()
                if isinstance(sheet_data, dict)
            )

    # Для CSV/JSON файлів або якщо формат не розпізнано
    if "data" in report_data and isinstance(report_data.get("data"), list):
        return len(report_data["data"])

    # Для звітів з невідомою структурою або без даних
    return 0


def calculate_file_hash(file_data: bytes) -> str:
    """
    Обчислює MD5 хеш вмісту файлу.

    Args:
        file_data: Байтові дані файлу

    Returns:
        str: MD5 хеш
    """
    md5 = hashlib.md5()
    md5.update(file_data)
    return md5.hexdigest()
