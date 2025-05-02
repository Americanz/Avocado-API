from supabase.storage import StorageClient
from ..config.supabase_config import SUPABASE_BUCKET
from .supabase_client import get_supabase_client
from typing import Optional, BinaryIO, List, Dict, Any
import os

class SupabaseStorageService:
    """
    Service for handling file operations with Supabase Storage
    """
    
    @staticmethod
    def get_storage() -> StorageClient:
        """Returns the Supabase storage client"""
        client = get_supabase_client()
        return client.storage
    
    @staticmethod
    async def upload_file(
        file_path: str, 
        file_binary: BinaryIO,
        content_type: Optional[str] = None,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Supabase Storage
        
        Args:
            file_path: Path/name for the file in the bucket
            file_binary: File binary data
            content_type: MIME type of the file
            folder: Optional folder within the bucket
            
        Returns:
            Dict with upload result
        """
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        result = bucket.upload(
            path=path,
            file=file_binary,
            file_options={{"content_type": content_type}} if content_type else None
        )
        
        return result
    
    @staticmethod
    async def download_file(file_path: str, folder: Optional[str] = None) -> bytes:
        """
        Download a file from Supabase Storage
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            File content as bytes
        """
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.download(path)
    
    @staticmethod
    async def get_file_url(file_path: str, folder: Optional[str] = None) -> str:
        """
        Get public URL for a file
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            Public URL for the file
        """
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.get_public_url(path)
    
    @staticmethod
    async def list_files(folder: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a bucket or folder
        
        Args:
            folder: Optional folder within the bucket
            
        Returns:
            List of file information dictionaries
        """
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        search = folder or ""
        return bucket.list(search)
    
    @staticmethod
    async def delete_file(file_path: str, folder: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            Result of the deletion operation
        """
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.remove([path])
