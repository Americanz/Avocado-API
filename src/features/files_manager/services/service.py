# Service layer for files_manager module
from typing import List, Optional, Dict, Any
from src.core.security.jwt import JWTPayload
from ..controllers.controllers import (
    get_all_files,
    get_file_by_id,
    create_file,
    update_file,
    delete_file,
    get_file_url,
)
from ..schemas.supabase_models import Files, FilesCreate, FilesUpdate


class FilesManagerService:
    """
    Service for handling file operations with Supabase
    """

    @staticmethod
    async def get_all_files(
        folder: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Files]:
        """
        Get all files with optional filtering

        Args:
            folder: Optional folder to filter by
            user_id: Optional user ID to filter by
            limit: Optional result limit

        Returns:
            List of file records
        """
        files = await get_all_files(folder, user_id, limit)

        # Отримуємо URL для кожного файлу
        for file in files:
            if file.get("file_path"):
                file["url"] = await get_file_url(
                    file_path=file["file_path"], folder=file.get("folder")
                )

        # Конвертуємо в Pydantic моделі
        return [Files(**file) for file in files]

    @staticmethod
    async def get_file_by_id(file_id: str) -> Optional[Files]:
        """
        Get file by ID

        Args:
            file_id: ID of the file

        Returns:
            File record or None
        """
        file = await get_file_by_id(file_id)

        if not file:
            return None

        # Отримуємо URL файлу
        if file.get("file_path"):
            file["url"] = await get_file_url(
                file_path=file["file_path"], folder=file.get("folder")
            )

        return Files(**file)

    @staticmethod
    async def create_file(
        file_data: FilesCreate, current_user: Optional[JWTPayload] = None
    ) -> Files:
        """
        Create a new file record

        Args:
            file_data: File data
            current_user: Current user JWT payload

        Returns:
            Created file record
        """
        # Отримуємо ID користувача, якщо він авторизований
        user_id = current_user.sub if current_user else None

        # Створюємо запис файлу
        file = await create_file(file_data, user_id)

        # Отримуємо URL файлу
        if file.get("file_path"):
            file["url"] = await get_file_url(
                file_path=file["file_path"], folder=file.get("folder")
            )

        return Files(**file)

    @staticmethod
    async def update_file(file_id: str, file_data: FilesUpdate) -> Optional[Files]:
        """
        Update a file record

        Args:
            file_id: ID of the file
            file_data: New file data

        Returns:
            Updated file record or None
        """
        # Оновлюємо файл
        updated_files = await update_file(file_id, file_data)

        if not updated_files:
            return None

        # Отримуємо оновлений файл
        return await FilesManagerService.get_file_by_id(file_id)

    @staticmethod
    async def delete_file(file_id: str) -> bool:
        """
        Delete a file

        Args:
            file_id: ID of the file

        Returns:
            True if deleted successfully
        """
        result = await delete_file(file_id)
        return bool(result)
