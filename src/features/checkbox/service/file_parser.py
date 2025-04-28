import json
import pandas as pd
import io
from typing import Dict, Any
import logging
from src.core.models.logging.providers import get_global_logger

# Отримуємо логер з резервним варіантом, якщо глобальний логер ще не ініціалізований
logger = get_global_logger()
# Якщо глобальний логер не ініціалізований, використовуємо стандартний logging
if logger is None:
    standard_logger = logging.getLogger("file_parser")
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

# Стандартні назви колонок для файлів без заголовків
DEFAULT_COLUMN_NAMES = [
    "Код товару",
    "Найменування",
    "УКТ ЗЕД",
    "Фіскальні номери чеків",
    "Вид операції",
    "Вартість",
    "Кількість",
    "Сума",
    "Чеків з товаром",
    "Назва податку",
    "Податок",
    "Дод. збір",
    "Сума знижок",
    "Сума націнок",
    "Загальна сума",
    "Дата продажу",
    "Фіскальний номер ПРРО",
    "Адреса каси",
    "Акцизна марка",
    "Штрих-код",
    "Тип оплати",
    "Номер зміни",
    "Дата та час закриття зміни",
]


class CustomJSONEncoder(json.JSONEncoder):
    """Кастомний JSON енкодер для серіалізації pandas Timestamp."""

    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)


def convert_for_json(obj):
    """
    Рекурсивно конвертує об'єкти, які не можна серіалізувати в JSON, в серіалізовані формати.

    Args:
        obj: Вхідний об'єкт

    Returns:
        Конвертований об'єкт
    """
    if isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(i) for i in obj]
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif hasattr(obj, "isoformat") and callable(getattr(obj, "isoformat")):
        return obj.isoformat()
    else:
        return obj


def parse_report_file(file_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Парсинг файлу звіту в залежності від його формату.

    Args:
        file_data: Байтові дані файлу.
        filename: Назва файлу.

    Returns:
        Dict[str, Any]: Дані звіту або словник з помилкою.
    """
    try:
        logger.info(
            f"Початок парсингу файлу: {filename}",
            module="file_parser",
            data={"action": "parse_file"},
        )

        # Визначаємо формат файлу за розширенням
        if filename.lower().endswith(".json"):
            report_data = parse_json_report(file_data)
        elif filename.lower().endswith(".csv"):
            report_data = parse_csv_report(file_data)
        elif filename.lower().endswith(".xlsx"):
            report_data = parse_excel_report(file_data)
        else:
            error_msg = f"Непідтримуваний формат файлу: {filename}"
            logger.error(
                error_msg, module="file_parser", data={"action": "unsupported_format"}
            )
            return {"error": error_msg}

        # Конвертуємо дані для безпечної серіалізації в JSON
        if "error" not in report_data:
            report_data = convert_for_json(report_data)

        return report_data
    except Exception as e:
        error_msg = f"Помилка при парсингу файлу: {str(e)}"
        logger.error(
            error_msg, module="file_parser", data={"action": "parse_error"}, error=e
        )
        return {"error": error_msg}


def parse_json_report(file_data: bytes) -> Dict[str, Any]:
    """
    Парсинг JSON файлу.

    Args:
        file_data: Байтові дані JSON файлу.

    Returns:
        Dict[str, Any]: Дані звіту.
    """
    try:
        data = json.loads(file_data.decode("utf-8"))
        return data
    except json.JSONDecodeError as e:
        return {"error": f"Помилка декодування JSON: {str(e)}"}


def parse_excel_report(file_data: bytes) -> Dict[str, Any]:
    """
    Парсинг Excel файлу.

    Args:
        file_data: Байтові дані Excel файлу.

    Returns:
        Dict[str, Any]: Дані звіту.
    """
    try:
        # Зчитуємо всі аркуші з Excel файлу
        excel_data = {}
        excel_file = io.BytesIO(file_data)

        # Зчитуємо всі аркуші
        xlsx = pd.ExcelFile(excel_file)
        for sheet_name in xlsx.sheet_names:
            df = pd.read_excel(xlsx, sheet_name=sheet_name)

            # Очищення назв колонок від пробілів на початку і в кінці
            df.columns = [
                col.strip() if isinstance(col, str) else col for col in df.columns
            ]

            # Перевіряємо формат і виправляємо, якщо потрібно
            df = fix_checkbox_report_format(df)

            excel_data[sheet_name] = {
                "data": df.to_dict(orient="records"),
                "columns": df.columns.tolist(),
                "summary": {"rows": len(df), "columns": len(df.columns)},
            }

        return {"sheets": excel_data, "sheet_names": xlsx.sheet_names}
    except Exception as e:
        return {"error": f"Помилка при парсингу Excel: {str(e)}"}


def fix_checkbox_report_format(
    df: pd.DataFrame, report_type: str = None
) -> pd.DataFrame:
    """
    Виправляє формат DataFrame, якщо він не відповідає очікуваному формату Checkbox.

    Args:
        df: DataFrame для виправлення.
        report_type: Тип звіту ("goods" або "payments"). Якщо None, буде спроба визначити.

    Returns:
        pd.DataFrame: Виправлений DataFrame.
    """
    # Якщо DataFrame порожній, повертаємо його без змін
    if df.empty:
        return df

    # Очищення назв колонок від пробілів на початку і в кінці
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]

    # Спробуємо визначити тип звіту, якщо він не вказаний
    if report_type is None:
        if "Тип оплати" in df.columns or "Номер зміни" in df.columns:
            report_type = "payments"
        elif "УКТ ЗЕД" in df.columns or "Штрих-код" in df.columns:
            report_type = "goods"

    # Визначимо необхідні поля в залежності від типу
    required_columns = ["Код товару", "Фіскальні номери чеків"]
    if report_type == "goods":
        required_columns.extend(
            ["Найменування", "Вартість", "Кількість", "Загальна сума"]
        )
    elif report_type == "payments":
        required_columns.extend(["Тип оплати", "Номер зміни"])

    # Перевіряємо наявність необхідних колонок
    has_required = all(col in df.columns for col in required_columns)

    # Якщо потрібні колонки відсутні, спробуємо виправити формат
    if not has_required:
        # Виводимо поточні колонки для діагностики
        logger.info(
            f"Наявні колонки: {list(df.columns)}, потрібні: {required_columns}",
            module="file_parser",
            data={
                "action": "fix_format",
                "current_columns": list(df.columns),
                "required_columns": required_columns,
            },
        )

        # Спроба виявити заголовки в перших рядках
        potential_header_row = None
        header_match_score = 0

        for i in range(min(5, len(df))):
            row_values = df.iloc[i].astype(str).tolist()
            # Порівнюємо рядок зі списком необхідних колонок
            match_score = sum(
                1
                for val in row_values
                if any(col.lower() in val.lower() for col in required_columns)
            )

            if match_score > header_match_score:
                header_match_score = match_score
                potential_header_row = i

        # Якщо знайдено потенційний рядок з заголовками, переробляємо DataFrame
        if potential_header_row is not None and header_match_score >= 2:
            # Використовуємо знайдений рядок як заголовки
            headers = df.iloc[potential_header_row].astype(str)
            df = df.iloc[potential_header_row + 1 :].reset_index(drop=True)
            df.columns = headers

            # Очищаємо назви колонок знову
            df.columns = [col.strip() for col in df.columns]

            logger.info(
                f"Знайдено заголовки в рядку {potential_header_row}",
                module="file_parser",
                data={
                    "action": "header_found",
                    "headers": list(df.columns),
                    "match_score": header_match_score,
                },
            )
        else:
            # Спробуємо використати евристику для визначення колонок з оплатами
            if report_type == "payments" and "Тип оплати" not in df.columns:
                # Пошук колонки з типовими типами оплати
                payment_types = [
                    "готівка",
                    "картка",
                    "безготівковий",
                    "інтернет",
                    "банк",
                ]
                for col_idx, col_name in enumerate(df.columns):
                    col_values = df.iloc[:, col_idx].astype(str).str.lower()
                    payment_matches = col_values.str.contains(
                        "|".join(payment_types), regex=True
                    ).sum()

                    if (
                        payment_matches > len(df) * 0.5
                    ):  # Якщо більше 50% значень схожі на типи оплати
                        logger.info(
                            f"Знайдено колонку 'Тип оплати' за значеннями: {col_name}",
                            module="file_parser",
                            data={"action": "column_detection"},
                        )
                        # Перейменовуємо колонку
                        df = df.rename(columns={col_name: "Тип оплати"})

            # Для колонки "Фіскальні номери чеків" шукаємо колонку з унікальними ідентифікаторами
            # if "Фіскальні номери чеків" not in df.columns:
            #     for col_idx, col_name in enumerate(df.columns):
            #         col_values = df.iloc[:, col_idx].astype(str)
            #         # Якщо колонка містить ID-подібні значення (8+ символів, з літерами і цифрами)
            #         if col_values.str.len().mean() > 8 and col_values.str.contains('[a-zA-Z]').mean() > 0.5:
            #             logger.info(
            #                 f"Знайдено колонку 'Фіскальні номери чеків' за форматом: {col_name}",
            #                 module="file_parser",
            #                 data={"action": "column_detection"},
            #             )
            #             df = df.rename(columns={col_name: "Фіскальні номери чеків"})
            #             break

    # Конвертація типів даних для числових колонок
    numeric_columns = [
        "Вартість",
        "Кількість",
        "Сума",
        "Загальна сума",
        "Чеків з товаром",
        "Дод. збір",
        "Сума знижок",
        "Сума націнок",
        "Номер зміни",
    ]

    for col in numeric_columns:
        if col in df.columns:
            # Замінюємо коми на крапки і конвертуємо в float
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ".").str.replace(" ", ""),
                errors="coerce",
            ).fillna(0)

    # Конвертація дати
    if "Дата продажу" in df.columns:
        # Спробуємо різні формати дати
        df["Дата продажу"] = pd.to_datetime(df["Дата продажу"], errors="coerce")
        # Якщо дату не вдалося розпарсити, використовуємо поточну дату
        if df["Дата продажу"].isna().all():
            df["Дата продажу"] = pd.Timestamp.today()

    # Конвертація дати та часу
    if "Дата та час закриття зміни" in df.columns:
        df["Дата та час закриття зміни"] = pd.to_datetime(
            df["Дата та час закриття зміни"], errors="coerce"
        )

    return df


def parse_csv_report(file_data: bytes) -> Dict[str, Any]:
    """
    Парсинг CSV звіту з продажів товарів Checkbox.

    Args:
        file_data: Байтові дані CSV файлу.

    Returns:
        Dict[str, Any]: Оброблені дані звіту.
    """
    try:
        # Спробуємо різні кодування для обробки CSV файлу
        encodings = ["utf-8", "windows-1251", "cp1251", "latin-1"]
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(io.BytesIO(file_data), encoding=encoding)
                # Перевіряємо, чи вдалося розпарсити дані
                if not df.empty:
                    break
            except UnicodeDecodeError:
                continue

        if df is None or df.empty:
            return {"error": "Не вдалося декодувати CSV файл або файл порожній"}

        # Очищення назв колонок від пробілів на початку і в кінці
        df.columns = [col.strip() for col in df.columns]

        # Перевіряємо формат і виправляємо, якщо потрібно
        df = fix_checkbox_report_format(df)

        # Список очікуваних колонок для перевірки
        expected_columns = DEFAULT_COLUMN_NAMES

        # Перевіряємо наявність необхідних колонок (мінімальний набір)
        minimal_columns = [
            "Код товару",
            "Найменування",
            "Вартість",
            "Кількість",
            "Загальна сума",
        ]
        missing_columns = [col for col in minimal_columns if col not in df.columns]
        if missing_columns:
            return {
                "error": f"Відсутні необхідні колонки: {', '.join(missing_columns)}",
                "columns": df.columns.tolist(),
            }

        # Додаємо відсутні колонки з порожніми значеннями
        for col in expected_columns:
            if col not in df.columns:
                if col in [
                    "Вартість",
                    "Кількість",
                    "Сума",
                    "Чеків з товаром",
                    "Дод. збір",
                    "Сума знижок",
                    "Сума націнок",
                    "Загальна сума",
                ]:
                    df[col] = 0.0
                else:
                    df[col] = ""

        # Конвертація дати і часу закриття зміни (виконується один раз)
        if "Дата та час закриття зміни" in df.columns:
            df["Дата та час закриття зміни"] = pd.to_datetime(
                df["Дата та час закриття зміни"], errors="coerce"
            )

        # Обчислення загальних підсумків
        totals = {
            "total_items": len(df),
            "total_sales": (
                df["Загальна сума"].sum() if "Загальна сума" in df.columns else 0
            ),
            "total_quantity": df["Кількість"].sum() if "Кількість" in df.columns else 0,
            "unique_products": (
                df["Код товару"].nunique() if "Код товару" in df.columns else 0
            ),
        }

        # Групування за датою продажу (якщо є)
        sales_by_date = {}
        if "Дата продажу" in df.columns and not df["Дата продажу"].isna().all():
            date_grouped = df.groupby(df["Дата продажу"].dt.date)["Загальна сума"].sum()
            sales_by_date = date_grouped.to_dict()
            # Конвертуємо ключі дати у рядки (JSON serializable)
            sales_by_date = {str(k): float(v) for k, v in sales_by_date.items()}

        # Групування за товарами
        products_summary = {}
        if (
            "Код товару" in df.columns
            and "Найменування" in df.columns
            and "Загальна сума" in df.columns
        ):
            product_grouped = (
                df.groupby(["Код товару", "Найменування"])
                .agg(
                    {
                        "Кількість": "sum",
                        "Загальна сума": "sum",
                        "Чеків з товаром": (
                            "sum" if "Чеків з товаром" in df.columns else lambda x: 0
                        ),
                    }
                )
                .reset_index()
            )

            products_summary = product_grouped.to_dict(orient="records")

        # Повертаємо структуровані дані
        return {
            "data": df.to_dict(orient="records"),
            "columns": df.columns.tolist(),
            "summary": {
                "rows": len(df),
                "columns": len(df.columns),
                "totals": totals,
                "sales_by_date": sales_by_date,
                "products_summary": products_summary,
            },
        }
    except Exception as e:
        return {"error": f"Помилка при парсингу CSV: {str(e)}"}
