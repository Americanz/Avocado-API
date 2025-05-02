"""
Routes for interacting with existing Supabase table data.
This module allows fetching, processing, and updating data in Supabase tables.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from src.core.security.jwt import get_current_user
from supabase import create_client

from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY
from ..utils.table_inspector import SupabaseTableInspector
from ..utils.columns_inspector import SupabaseColumnsInspector

router = APIRouter(tags=["table-data"])

# Создаем клиент Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.get("/{table_name}")
async def get_table_data(
    table_name: str = Path(..., description="Name of the Supabase table to fetch data from"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    current_user  = Depends(get_current_user)
):
    """
    Fetch data from a specific Supabase table.

    This endpoint retrieves records from the specified table with pagination support.
    """
    try:
        # Получаем данные из таблицы
        response = supabase.table(table_name).select("*").range(offset, offset + limit - 1).execute()

        return {
            "table_name": table_name,
            "total": len(response.data),
            "limit": limit,
            "offset": offset,
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error fetching data from table '{table_name}': {str(e)}"
        )

@router.post("/{table_name}/process")
async def process_table_data(
    table_name: str = Path(..., description="Name of the Supabase table to process data from"),
    transformation: Dict[str, Any] = Body(..., description="Transformation rules to apply to the data"),
    current_user = Depends(get_current_user)
):
    """
    Process data from a Supabase table and return transformed results.

    The transformation parameter should contain rules for processing the data.
    Example:
    {
        "filters": {"column_name": "value"},
        "calculations": ["sum", "average", "count"],
        "group_by": ["column_name"],
        "transform": {"operation": "multiply", "field": "price", "value": 1.2}
    }
    """
    try:
        # Получаем данные из таблицы
        query = supabase.table(table_name).select("*")

        # Применяем фильтры, если они указаны
        if "filters" in transformation:
            for field, value in transformation["filters"].items():
                query = query.eq(field, value)

        # Выполняем запрос
        response = query.execute()
        data = response.data

        # Применяем трансформации к данным
        processed_data = []

        # Обработка данных в соответствии с правилами трансформации
        if "transform" in transformation:
            transform = transformation["transform"]

            # Пример трансформации: умножение числового поля на коэффициент
            if transform.get("operation") == "multiply" and "field" in transform and "value" in transform:
                field = transform["field"]
                value = transform["value"]

                for item in data:
                    if field in item and isinstance(item[field], (int, float)):
                        item_copy = item.copy()
                        item_copy[field] = item[field] * value
                        processed_data.append(item_copy)
                    else:
                        processed_data.append(item)

            # Пример трансформации: добавление нового поля
            elif transform.get("operation") == "add_field" and "field" in transform and "value" in transform:
                field = transform["field"]
                value = transform["value"]

                for item in data:
                    item_copy = item.copy()
                    item_copy[field] = value
                    processed_data.append(item_copy)

            # Если трансформация не определена, возвращаем данные как есть
            else:
                processed_data = data
        else:
            processed_data = data

        # Вычисления агрегатных значений, если они требуются
        aggregations = {}

        if "calculations" in transformation:
            calculations = transformation["calculations"]

            # Например, если нужно вычислить сумму по определенному полю
            if "sum" in calculations and "field" in transformation:
                field = transformation["field"]
                aggregations["sum"] = sum(item.get(field, 0) for item in data if field in item)

            # Среднее значение
            if "average" in calculations and "field" in transformation:
                field = transformation["field"]
                values = [item.get(field, 0) for item in data if field in item]
                aggregations["average"] = sum(values) / len(values) if values else 0

            # Количество записей
            if "count" in calculations:
                aggregations["count"] = len(data)

        return {
            "table_name": table_name,
            "original_count": len(data),
            "processed_count": len(processed_data),
            "aggregations": aggregations,
            "processed_data": processed_data[:100]  # Ограничиваем возвращаемый результат
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing data from table '{table_name}': {str(e)}"
        )

@router.post("/{table_name}/update")
async def update_table_data(
    table_name: str = Path(..., description="Name of the Supabase table to update data in"),
    data: List[Dict[str, Any]] = Body(..., description="Data to update in the table"),
    id_field: str = Query("id", description="Field to use as the primary key for updates"),
    current_user = Depends(get_current_user)
):
    """
    Update data in a Supabase table.

    This endpoint updates records in the specified table based on the provided data.
    Each object in the data list should contain the ID field specified by id_field.
    """
    try:
        results = []

        for item in data:
            if id_field not in item:
                results.append({"error": f"Missing ID field '{id_field}'", "item": item})
                continue

            id_value = item[id_field]

            try:
                # Обновляем запись по ID
                response = supabase.table(table_name).update(item).eq(id_field, id_value).execute()

                if response.data:
                    results.append({"success": True, "id": id_value, "updated_item": response.data[0]})
                else:
                    results.append({"success": False, "id": id_value, "error": "Record not found or no changes made"})

            except Exception as update_error:
                results.append({"success": False, "id": id_value, "error": str(update_error)})

        return {
            "table_name": table_name,
            "total_processed": len(data),
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating data in table '{table_name}': {str(e)}"
        )

@router.get("/{table_name}/schema")
async def get_table_schema(
    table_name: str = Path(..., description="Name of the Supabase table to get schema for"),
    generate_models: bool = Query(False, description="Whether to generate Pydantic models for the table"),
    current_user = Depends(get_current_user)
):
    """
    Get the schema of a Supabase table and optionally generate Pydantic models.
    """
    try:
        # Создаем инспектор таблицы
        inspector = SupabaseTableInspector(table_name)

        # Получаем образец данных
        sample_data = await inspector.get_table_sample(limit=3)

        # Определяем схему из данных
        schema = await inspector.infer_schema_from_data(sample_data)

        response = {
            "table_name": table_name,
            "schema": schema,
            "sample_data": sample_data
        }

        # Если запрошена генерация моделей
        if generate_models:
            models_code = await inspector.generate_models_code()
            response["models_code"] = models_code

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting schema for table '{table_name}': {str(e)}"
        )

@router.get("/{table_name}/columns")
async def get_table_columns(
    table_name: str = Path(..., description="Name of the Supabase table to get columns for"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information about columns in a specific Supabase table.
    
    This endpoint retrieves metadata about the columns including name, data type, 
    nullable status, and other properties.
    """
    try:
        # Создаем инспектор колонок
        columns_inspector = SupabaseColumnsInspector()
        
        # Проверяем существование таблицы
        table_exists = await columns_inspector.check_table_existence(table_name)
        
        if not table_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{table_name}' does not exist or is not accessible"
            )
        
        # Получаем информацию о колонках
        columns = await columns_inspector.get_table_columns(table_name)
        
        if not columns:
            return {
                "table_name": table_name,
                "columns": [],
                "warning": "Could not retrieve column information. Table may be empty or you may not have sufficient permissions."
            }
        
        # Получаем образец данных (первую запись)
        try:
            sample_response = supabase.table(table_name).select("*").limit(1).execute()
            sample_data = sample_response.data[0] if sample_response.data else None
        except Exception:
            sample_data = None
        
        # Формируем ответ
        return {
            "table_name": table_name,
            "columns_count": len(columns),
            "columns": columns,
            "sample_data": sample_data
        }
        
    except HTTPException:
        # Пробрасываем HTTPException дальше
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting columns for table '{table_name}': {str(e)}"
        )
