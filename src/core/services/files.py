"""
File service for file operations.
"""
import os
import uuid
from typing import BinaryIO, List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status

from src.config import settings
from src.config.constants import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_UPLOAD_SIZE,
)


class FileService:
    """Service for handling file operations."""
    
    def __init__(self, base_path: str = None):
        """
        Initialize file service.
        
        Args:
            base_path: Base path for file storage
        """
        # Set base path for file storage
        self.base_path = base_path or os.path.join(os.getcwd(), "uploads")
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_file_path(self, file_id: str, folder: str = None) -> str:
        """
        Get file path for given file ID and folder.
        
        Args:
            file_id: File ID
            folder: Folder name
        
        Returns:
            str: File path
        """
        if folder:
            # Create folder if it doesn't exist
            folder_path = os.path.join(self.base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            return os.path.join(folder_path, file_id)
        
        return os.path.join(self.base_path, file_id)
    
    def _get_extension(self, filename: str) -> str:
        """
        Get file extension from filename.
        
        Args:
            filename: Filename
        
        Returns:
            str: File extension
        """
        return os.path.splitext(filename)[1].lower().lstrip(".")
    
    def _validate_file(
        self, 
        file: UploadFile, 
        allowed_extensions: List[str] = None,
        max_size: int = None,
    ) -> None:
        """
        Validate file extension and size.
        
        Args:
            file: File to validate
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size in bytes
        
        Raises:
            HTTPException: If file is invalid
        """
        # Validate file extension
        if allowed_extensions:
            extension = self._get_extension(file.filename)
            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file extension. Allowed extensions: {', '.join(allowed_extensions)}",
                )
        
        # Validate file size
        if max_size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum size of {max_size / (1024 * 1024):.2f} MB",
            )
    
    async def save_file(
        self,
        file: UploadFile,
        folder: str = None,
        allowed_extensions: List[str] = None,
        max_size: int = MAX_UPLOAD_SIZE,
        custom_filename: str = None,
    ) -> Tuple[str, str]:
        """
        Save file to storage.
        
        Args:
            file: File to save
            folder: Folder to save file in
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size in bytes
            custom_filename: Custom filename to use
        
        Returns:
            Tuple[str, str]: Tuple of (file ID, file URL)
        
        Raises:
            HTTPException: If file is invalid
        """
        # Validate file
        self._validate_file(file, allowed_extensions, max_size)
        
        # Get file extension
        extension = self._get_extension(file.filename)
        
        # Generate unique file ID
        file_id = custom_filename or f"{uuid.uuid4().hex}.{extension}"
        
        # Get file path
        file_path = self._get_file_path(file_id, folder)
        
        # Save file
        with open(file_path, "wb") as f:
            # Read file in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1 MB
            while chunk := await file.read(chunk_size):
                f.write(chunk)
        
        # Generate file URL
        file_url = f"/uploads/{folder}/{file_id}" if folder else f"/uploads/{file_id}"
        
        return file_id, file_url
    
    def save_image(
        self,
        file: UploadFile,
        folder: str = "images",
        allowed_extensions: List[str] = ALLOWED_IMAGE_EXTENSIONS,
        max_size: int = MAX_UPLOAD_SIZE,
        custom_filename: str = None,
    ) -> Tuple[str, str]:
        """
        Save image file to storage.
        
        Args:
            file: Image file to save
            folder: Folder to save image in
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size in bytes
            custom_filename: Custom filename to use
        
        Returns:
            Tuple[str, str]: Tuple of (file ID, file URL)
        
        Raises:
            HTTPException: If file is invalid
        """
        return self.save_file(
            file=file,
            folder=folder,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
            custom_filename=custom_filename,
        )
    
    def save_document(
        self,
        file: UploadFile,
        folder: str = "documents",
        allowed_extensions: List[str] = ALLOWED_DOCUMENT_EXTENSIONS,
        max_size: int = MAX_UPLOAD_SIZE,
        custom_filename: str = None,
    ) -> Tuple[str, str]:
        """
        Save document file to storage.
        
        Args:
            file: Document file to save
            folder: Folder to save document in
            allowed_extensions: List of allowed extensions
            max_size: Maximum file size in bytes
            custom_filename: Custom filename to use
        
        Returns:
            Tuple[str, str]: Tuple of (file ID, file URL)
        
        Raises:
            HTTPException: If file is invalid
        """
        return self.save_file(
            file=file,
            folder=folder,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
            custom_filename=custom_filename,
        )
    
    def get_file(self, file_id: str, folder: str = None) -> Optional[BinaryIO]:
        """
        Get file from storage.
        
        Args:
            file_id: File ID
            folder: Folder name
        
        Returns:
            Optional[BinaryIO]: File object if found, None otherwise
        """
        # Get file path
        file_path = self._get_file_path(file_id, folder)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return None
        
        # Return file
        return open(file_path, "rb")
    
    def delete_file(self, file_id: str, folder: str = None) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_id: File ID
            folder: Folder name
        
        Returns:
            bool: True if file was deleted, False otherwise
        """
        # Get file path
        file_path = self._get_file_path(file_id, folder)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return False
        
        # Delete file
        os.remove(file_path)
        
        return True