"""
Utility for getting table columns information from Supabase directly from PostgreSQL metadata.
"""

import logging
from typing import List, Dict, Any
from supabase import create_client

from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)


class SupabaseColumnsInspector:
    """Class for inspecting table columns in Supabase using PostgreSQL metadata"""

    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed information about columns in a specific table

        Args:
            table_name: Name of the table to inspect

        Returns:
            List of column details including name, type, nullable status, etc.
        """
        try:
            # Используем прямой запрос к таблице вместо RPC
            try:
                logger.info(
                    f"Trying to get column information for table '{table_name}' directly..."
                )

                # Попытка использовать прямой SQL запрос через функцию supabase.table().query()
                # Эта функция безопаснее, чем произвольный SQL через RPC
                response = (
                    self.supabase.from_("information_schema.columns")
                    .select(
                        "column_name,data_type,is_nullable,column_default,character_maximum_length,numeric_precision,numeric_scale,ordinal_position"
                    )
                    .eq("table_schema", "public")
                    .eq("table_name", table_name)
                    .order("ordinal_position")
                    .execute()
                )

                if response.data:
                    logger.info(
                        f"Found {len(response.data)} columns for table '{table_name}' using direct query"
                    )
                    return response.data
                else:
                    logger.warning(
                        f"No columns found for table '{table_name}' using direct query"
                    )

            except Exception as direct_error:
                logger.error(
                    f"Failed to get columns using direct query: {str(direct_error)}"
                )
                logger.info("Falling back to alternative approach...")

            # Если прямой запрос не работает, пробуем использовать метаданные через postgrest
            try:
                logger.info(
                    f"Trying to get column information for table '{table_name}' via metadata..."
                )

                # Получение метаданных таблицы через OpenAPI спецификацию PostgREST
                # Этот метод работает без необходимости создания специальных функций
                metadata_response = self.supabase.postgrest.schema().execute()

                if (
                    hasattr(metadata_response, "definitions")
                    and metadata_response.definitions
                ):
                    table_schema = metadata_response.definitions.get(
                        f"public_{table_name}"
                    )
                    if table_schema and hasattr(table_schema, "properties"):
                        columns = []
                        for col_name, col_info in table_schema.properties.items():
                            column_info = {
                                "column_name": col_name,
                                "data_type": col_info.get("type", "unknown"),
                                "is_nullable": (
                                    "YES"
                                    if col_name not in table_schema.required
                                    else "NO"
                                ),
                                "column_default": None,
                                "inferred_from_schema": True,
                            }
                            columns.append(column_info)

                        logger.info(
                            f"Found {len(columns)} columns for table '{table_name}' from schema metadata"
                        )
                        return columns

            except Exception as metadata_error:
                logger.error(
                    f"Failed to get columns from metadata: {str(metadata_error)}"
                )

            # Если предыдущие методы не работают, пробуем альтернативный подход
            # через анализ образца данных
            try:
                logger.info(
                    f"Trying to infer columns from data sample for table '{table_name}'..."
                )
                response = (
                    self.supabase.table(table_name).select("*").limit(1).execute()
                )

                if not response.data:
                    logger.warning(
                        f"Table '{table_name}' exists but has no data to infer columns"
                    )
                    return []

                # Получаем колонки из первой записи
                sample_record = response.data[0]
                inferred_columns = []

                for col_name, value in sample_record.items():
                    column_info = {
                        "column_name": col_name,
                        "data_type": self._infer_data_type(value),
                        "is_nullable": "YES",  # Предполагаем, что поле может быть NULL
                        "column_default": None,
                        "inferred": True,  # Отмечаем, что информация получена путем анализа данных
                    }
                    inferred_columns.append(column_info)

                logger.info(
                    f"Inferred {len(inferred_columns)} columns from data sample"
                )
                return inferred_columns

            except Exception as sample_error:
                logger.error(
                    f"Failed to infer columns from sample: {str(sample_error)}"
                )
                return []

        except Exception as e:
            logger.error(f"Error getting columns for table '{table_name}': {str(e)}")
            return []

    def _infer_data_type(self, value: Any) -> str:
        """Infer PostgreSQL data type from Python value"""
        if value is None:
            return "unknown"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "numeric"
        elif isinstance(value, str):
            return "text"
        elif isinstance(value, dict):
            return "jsonb"
        elif isinstance(value, list):
            return "jsonb"
        else:
            return f"unknown ({type(value).__name__})"

    async def check_table_existence(self, table_name: str) -> bool:
        """
        Check if a table exists in the Supabase database

        Args:
            table_name: Name of the table to check

        Returns:
            True if the table exists, False otherwise
        """
        try:
            # Пробуем получить данные из таблицы
            response = self.supabase.table(table_name).select("*").limit(1).execute()
            # Если запрос выполнился без ошибок, таблица существует
            return True
        except Exception:
            return False
