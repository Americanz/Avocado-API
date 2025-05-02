# Controller logic for files_manager module
from typing import List, Optional, Dict, Any
from ..services.supabase_database import SupabaseDatabaseService
from ..schemas.supabase_models import Files, FilesCreate, FilesUpdate
from ..services.supabase_storage import SupabaseStorageService

# Назва таблиці в Supabase
SUPABASE_TABLE = "files"

async def get_all_files(
    folder: Optional[str] = None, 
    user_id: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get all files, optionally filtered by folder and user_id
    
    Args:
        folder: Optional folder filter
        user_id: Optional user_id filter
        limit: Optional limit for number of results
    
    Returns:
        List of file records
    """
    filters = {}
    if folder:
        filters["folder"] = folder
    if user_id:
        filters["user_id"] = user_id
        
    return await SupabaseDatabaseService.select(
        table=SUPABASE_TABLE,
        filters=filters,
        limit=limit,
        order="created_at",
        ascending=False
    )

async def get_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file by ID
    
    Args:
        file_id: File ID to retrieve
    
    Returns:
        File record or None if not found
    """
    files = await SupabaseDatabaseService.select(
        table=SUPABASE_TABLE,
        filters={"id": file_id}
    )
    return files[0] if files else None

async def create_file(file_data: FilesCreate, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new file record
    
    Args:
        file_data: File data to create
        user_id: Optional user_id to associate with the file
    
    Returns:
        Created file record
    """
    # Перетворення даних Pydantic моделі в словник
    data = file_data.model_dump()
    
    # Додавання user_id, якщо надано
    if user_id and "user_id" not in data:
        data["user_id"] = user_id
    
    # Вставка запису в Supabase
    return await SupabaseDatabaseService.insert(
        table=SUPABASE_TABLE,
        data=data
    )

async def update_file(file_id: str, file_data: FilesUpdate) -> List[Dict[str, Any]]:
    """
    Update an existing file record
    
    Args:
        file_id: ID of the file to update
        file_data: New file data
    
    Returns:
        Updated file record
    """
    # Перетворення даних Pydantic моделі в словник, виключаючи None значення
    data = {k: v for k, v in file_data.model_dump().items() if v is not None}
    
    # Оновлення запису в Supabase
    return await SupabaseDatabaseService.update(
        table=SUPABASE_TABLE,
        filters={"id": file_id},
        data=data
    )

async def delete_file(file_id: str) -> List[Dict[str, Any]]:
    """
    Delete a file record
    
    Args:
        file_id: ID of the file to delete
    
    Returns:
        Deleted file record
    """
    # Спочатку отримуємо інформацію про файл
    file = await get_file_by_id(file_id)
    
    if file and file.get("file_path"):
        # Видаляємо файл з Storage
        await SupabaseStorageService.delete_file(
            file_path=file["file_path"],
            folder=file.get("folder")
        )
    
    # Видаляємо запис з бази даних
    return await SupabaseDatabaseService.delete(
        table=SUPABASE_TABLE,
        filters={"id": file_id}
    )

async def get_file_url(file_path: str, folder: Optional[str] = None) -> str:
    """
    Get public URL for a file
    
    Args:
        file_path: Path to the file
        folder: Optional folder
    
    Returns:
        Public URL for the file
    """
    return await SupabaseStorageService.get_file_url(
        file_path=file_path,
        folder=folder
    )
