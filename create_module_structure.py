import os
import argparse
from pathlib import Path


def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")


def create_file(path, content=""):
    """Create file with optional content"""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")


def create_init_file(path):
    """Create __init__.py file"""
    create_file(os.path.join(path, "__init__.py"))


def create_standard_module_structure(base_path, module_name, with_supabase=False):
    """Create standard module structure with typical FastAPI components"""
    module_path = os.path.join(base_path, "features", module_name)
    
    # Create main module directory
    create_directory(module_path)
    create_init_file(module_path)
    
    # Create standard subdirectories
    subdirs = ["routes", "schemas", "services", "controllers"]
    
    for subdir in subdirs:
        subdir_path = os.path.join(module_path, subdir)
        create_directory(subdir_path)
        create_init_file(subdir_path)
    
    # Create routes file with APIRouter
    routes_content = """from fastapi import APIRouter, Depends, HTTPException, status
from src.core.security.jwt import get_current_user
from ..schemas.schemas import *
from ..controllers.controllers import *

router = APIRouter(tags=["{}"])

@router.get("/")
async def get_root():
    return {{"message": "Welcome to {} module"}}
""".format(module_name, module_name)
    create_file(os.path.join(module_path, "routes", "routes.py"), routes_content)
    
    # Create schemas file
    schemas_content = """from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Define your Pydantic models here
class {}Base(BaseModel):
    name: str
    description: Optional[str] = None

class {}Create({}Base):
    pass

class {}Response({}Base):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
""".format(
        module_name.capitalize(), 
        module_name.capitalize(), 
        module_name.capitalize(),
        module_name.capitalize(),
        module_name.capitalize()
    )
    create_file(os.path.join(module_path, "schemas", "schemas.py"), schemas_content)
    
    # Create controllers file
    controllers_content = """# Controller logic for {} module
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.core.database.connection import get_db
from ..schemas.schemas import *

async def get_all_items(db: AsyncSession):
    # Implement logic to get all items
    pass

async def get_item_by_id(item_id: int, db: AsyncSession):
    # Implement logic to get item by ID
    pass

async def create_item(item: {}Create, db: AsyncSession):
    # Implement logic to create item
    pass

async def update_item(item_id: int, item: {}Create, db: AsyncSession):
    # Implement logic to update item
    pass

async def delete_item(item_id: int, db: AsyncSession):
    # Implement logic to delete item
    pass
""".format(module_name, module_name.capitalize(), module_name.capitalize())
    create_file(os.path.join(module_path, "controllers", "controllers.py"), controllers_content)
    
    # Create models file if needed
    models_path = os.path.join(module_path, "models")
    create_directory(models_path)
    create_init_file(models_path)
    
    model_content = """from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.models.base_model import Base

class {}(Base):
    __tablename__ = "{}"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Add relationships and other fields here
    
    def __repr__(self):
        return f"<{} id={{self.id}}, name={{self.name}}>"
""".format(
        module_name.capitalize(), 
        module_name.lower(),
        module_name.capitalize()
    )
    create_file(os.path.join(models_path, "models.py"), model_content)
    
    # Create service file
    service_content = """# Service layer for {} module
from src.core.database.connection import get_db
from ..controllers.controllers import *
from ..schemas.schemas import *

class {}Service:
    \"\"\"
    Service for handling {} operations
    \"\"\"
    
    @staticmethod
    async def get_all_items():
        async with get_db() as db:
            return await get_all_items(db)
            
    @staticmethod
    async def get_item_by_id(item_id: int):
        async with get_db() as db:
            return await get_item_by_id(item_id, db)
    
    @staticmethod
    async def create_item(item: {}Create):
        async with get_db() as db:
            return await create_item(item, db)
            
    @staticmethod
    async def update_item(item_id: int, item: {}Create):
        async with get_db() as db:
            return await update_item(item_id, item, db)
            
    @staticmethod
    async def delete_item(item_id: int):
        async with get_db() as db:
            return await delete_item(item_id, db)
""".format(
        module_name, 
        module_name.capitalize(), 
        module_name,
        module_name.capitalize(),
        module_name.capitalize()
    )
    create_file(os.path.join(module_path, "services", "service.py"), service_content)
    
    # Add Supabase specific files if requested
    if with_supabase:
        create_supabase_extras(module_path, module_name)
    
    print(f"\nModule '{module_name}' structure created successfully!")
    print(f"Location: {module_path}")
    print("\nNext steps:")
    print(f"1. Update your module registration in src/core/loader_factory/registry_factory/")
    print(f"2. Add routes to the appropriate router in src/core/loader_factory/registry_factory/loader.py")
    print(f"3. Implement your business logic in the controllers and services")


def create_supabase_extras(module_path, module_name):
    """Create Supabase specific files and directories"""
    
    # Create Supabase config
    config_path = os.path.join(module_path, "config")
    create_directory(config_path)
    create_init_file(config_path)
    
    supabase_config_content = """# Supabase configuration for {} module
import os
from src.config.settings import settings

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
SUPABASE_BUCKET = "{}_bucket"
""".format(module_name, module_name.lower())
    create_file(os.path.join(config_path, "supabase_config.py"), supabase_config_content)
    
    # Create Supabase client
    client_content = """from supabase import create_client, Client
from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

def get_supabase_client() -> Client:
    \"\"\"
    Returns a Supabase client instance
    \"\"\"
    return create_client(SUPABASE_URL, SUPABASE_KEY)
"""
    create_file(os.path.join(module_path, "services", "supabase_client.py"), client_content)
    
    # Create Supabase storage service
    storage_service_content = """from supabase.storage import StorageClient
from ..config.supabase_config import SUPABASE_BUCKET
from .supabase_client import get_supabase_client
from typing import Optional, BinaryIO, List, Dict, Any
import os

class SupabaseStorageService:
    \"\"\"
    Service for handling file operations with Supabase Storage
    \"\"\"
    
    @staticmethod
    def get_storage() -> StorageClient:
        \"\"\"Returns the Supabase storage client\"\"\"
        client = get_supabase_client()
        return client.storage
    
    @staticmethod
    async def upload_file(
        file_path: str, 
        file_binary: BinaryIO,
        content_type: Optional[str] = None,
        folder: Optional[str] = None
    ) -> Dict[str, Any]:
        \"\"\"
        Upload a file to Supabase Storage
        
        Args:
            file_path: Path/name for the file in the bucket
            file_binary: File binary data
            content_type: MIME type of the file
            folder: Optional folder within the bucket
            
        Returns:
            Dict with upload result
        \"\"\"
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
        \"\"\"
        Download a file from Supabase Storage
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            File content as bytes
        \"\"\"
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.download(path)
    
    @staticmethod
    async def get_file_url(file_path: str, folder: Optional[str] = None) -> str:
        \"\"\"
        Get public URL for a file
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            Public URL for the file
        \"\"\"
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.get_public_url(path)
    
    @staticmethod
    async def list_files(folder: Optional[str] = None) -> List[Dict[str, Any]]:
        \"\"\"
        List files in a bucket or folder
        
        Args:
            folder: Optional folder within the bucket
            
        Returns:
            List of file information dictionaries
        \"\"\"
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        search = folder or ""
        return bucket.list(search)
    
    @staticmethod
    async def delete_file(file_path: str, folder: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path/name of the file in the bucket
            folder: Optional folder within the bucket
            
        Returns:
            Result of the deletion operation
        \"\"\"
        storage = SupabaseStorageService.get_storage()
        bucket = storage.from_(SUPABASE_BUCKET)
        
        path = file_path
        if folder:
            path = f"{folder}/{file_path}"
            
        return bucket.remove([path])
"""
    create_file(os.path.join(module_path, "services", "supabase_storage.py"), storage_service_content)
    
    # Create Supabase database service
    db_service_content = """from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY
from .supabase_client import get_supabase_client
from typing import Dict, List, Any, Optional

class SupabaseDatabaseService:
    \"\"\"
    Service for handling database operations with Supabase
    \"\"\"
    
    @staticmethod
    def get_client():
        \"\"\"Returns the Supabase client\"\"\"
        return get_supabase_client()
    
    @staticmethod
    async def select(
        table: str,
        columns: str = "*", 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        ascending: bool = True
    ) -> List[Dict[str, Any]]:
        \"\"\"
        Select data from a Supabase table
        
        Args:
            table: Table name
            columns: Columns to select (default: "*")
            filters: Optional dict of filters
            limit: Optional result limit
            order: Optional column to order by
            ascending: Whether to order ascending (default: True)
            
        Returns:
            List of records
        \"\"\"
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
                
        if order:
            if ascending:
                query = query.order(order)
            else:
                query = query.order(order, desc=True)
                
        if limit:
            query = query.limit(limit)
            
        response = query.execute()
        return response.data
    
    @staticmethod
    async def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Insert data into a Supabase table
        
        Args:
            table: Table name
            data: Data to insert
            
        Returns:
            Inserted record
        \"\"\"
        client = SupabaseDatabaseService.get_client()
        response = client.table(table).insert(data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    async def update(
        table: str, 
        data: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        \"\"\"
        Update data in a Supabase table
        
        Args:
            table: Table name
            data: Data to update
            filters: Filters to identify rows to update
            
        Returns:
            Updated records
        \"\"\"
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
            
        response = query.execute()
        return response.data
    
    @staticmethod
    async def delete(table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        \"\"\"
        Delete data from a Supabase table
        
        Args:
            table: Table name
            filters: Filters to identify rows to delete
            
        Returns:
            Deleted records
        \"\"\"
        client = SupabaseDatabaseService.get_client()
        query = client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
            
        response = query.execute()
        return response.data
"""
    create_file(os.path.join(module_path, "services", "supabase_database.py"), db_service_content)
    
    # Create Supabase authentication service if needed
    auth_service_content = """from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY
from .supabase_client import get_supabase_client
from typing import Dict, Any, Optional

class SupabaseAuthService:
    \"\"\"
    Service for handling authentication with Supabase
    \"\"\"
    
    @staticmethod
    def get_client():
        \"\"\"Returns the Supabase client\"\"\"
        return get_supabase_client()
    
    @staticmethod
    async def sign_up(email: str, password: str) -> Dict[str, Any]:
        \"\"\"
        Register a new user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            User data
        \"\"\"
        client = SupabaseAuthService.get_client()
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        return response
    
    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        \"\"\"
        Sign in a user
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Session and user data
        \"\"\"
        client = SupabaseAuthService.get_client()
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    
    @staticmethod
    async def sign_out(jwt: str) -> None:
        \"\"\"
        Sign out a user
        
        Args:
            jwt: User JWT token
        \"\"\"
        client = SupabaseAuthService.get_client()
        client.auth.sign_out()
    
    @staticmethod
    async def reset_password(email: str) -> Dict[str, Any]:
        \"\"\"
        Send password reset email
        
        Args:
            email: User email
            
        Returns:
            Result of operation
        \"\"\"
        client = SupabaseAuthService.get_client()
        return client.auth.reset_password_for_email(email)
    
    @staticmethod
    async def get_user(jwt: str) -> Optional[Dict[str, Any]]:
        \"\"\"
        Get user data from JWT
        
        Args:
            jwt: User JWT token
            
        Returns:
            User data or None
        \"\"\"
        client = SupabaseAuthService.get_client()
        try:
            return client.auth.get_user(jwt)
        except Exception:
            return None
"""
    create_file(os.path.join(module_path, "services", "supabase_auth.py"), auth_service_content)
    
    # Add schema definitions for file operations
    file_schemas_content = """from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FileUploadResponse(BaseModel):
    path: str
    url: str
    size: Optional[int] = None
    mimetype: Optional[str] = None

class FileInfo(BaseModel):
    name: str
    id: str
    size: int
    last_modified: datetime
    mime_type: Optional[str] = None
    url: Optional[str] = None

class FileList(BaseModel):
    files: List[FileInfo] = []
    total: int
"""
    create_file(os.path.join(module_path, "schemas", "file_schemas.py"), file_schemas_content)
    
    # Add enhanced routes for file operations
    file_routes_content = """from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
from src.core.security.jwt import get_current_user
from ..services.supabase_storage import SupabaseStorageService
from ..config.supabase_config import SUPABASE_BUCKET
from ..schemas.file_schemas import FileUploadResponse, FileList, FileInfo
from typing import List, Optional
import io

router = APIRouter(tags=["supabase-files"])

@router.post("/upload/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    \"\"\"
    Upload a file to Supabase Storage
    \"\"\"
    try:
        file_content = await file.read()
        file_binary = io.BytesIO(file_content)
        
        result = await SupabaseStorageService.upload_file(
            file_path=file.filename,
            file_binary=file_binary,
            content_type=file.content_type,
            folder=folder
        )
        
        file_url = await SupabaseStorageService.get_file_url(
            file_path=file.filename,
            folder=folder
        )
        
        return FileUploadResponse(
            path=f"{folder + '/' if folder else ''}{file.filename}",
            url=file_url,
            size=len(file_content),
            mimetype=file.content_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/files/", response_model=FileList)
async def list_files(
    folder: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    \"\"\"
    List files in Supabase Storage
    \"\"\"
    try:
        files = await SupabaseStorageService.list_files(folder)
        
        file_infos = []
        for file in files:
            file_url = await SupabaseStorageService.get_file_url(
                file_path=file["name"],
                folder=folder
            )
            
            # Convert the file info to our schema
            file_infos.append(FileInfo(
                name=file["name"],
                id=file.get("id", ""),
                size=file.get("metadata", {}).get("size", 0),
                last_modified=file.get("metadata", {}).get("lastModified", datetime.now()),
                mime_type=file.get("metadata", {}).get("mimetype", None),
                url=file_url
            ))
        
        return FileList(files=file_infos, total=len(file_infos))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get("/files/{file_path}")
async def download_file(
    file_path: str,
    folder: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    \"\"\"
    Download a file from Supabase Storage
    \"\"\"
    try:
        file_bytes = await SupabaseStorageService.download_file(
            file_path=file_path,
            folder=folder
        )
        
        # You might want to detect the content type or store it in metadata
        content_type = "application/octet-stream"
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={file_path}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.delete("/files/{file_path}")
async def delete_file(
    file_path: str,
    folder: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    \"\"\"
    Delete a file from Supabase Storage
    \"\"\"
    try:
        result = await SupabaseStorageService.delete_file(
            file_path=file_path,
            folder=folder
        )
        
        return {"message": "File deleted successfully", "path": file_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
"""
    create_file(os.path.join(module_path, "routes", "file_routes.py"), file_routes_content)
    
    print(f"\nSupabase integration for '{module_name}' module created successfully!")
    print("Don't forget to add the following environment variables to your .env file:")
    print("SUPABASE_URL=your_supabase_url")
    print("SUPABASE_KEY=your_supabase_key")
    print("SUPABASE_BUCKET={}_bucket".format(module_name.lower()))


def main():
    parser = argparse.ArgumentParser(description="Create a new module structure for Avocado FastAPI project")
    parser.add_argument("module_name", help="Name of the module to create")
    parser.add_argument("--path", help="Path to the project root", default=".")
    parser.add_argument("--supabase", help="Add Supabase integration", action="store_true")
    
    args = parser.parse_args()
    
    # Use absolute paths
    base_path = os.path.abspath(args.path)
    
    # Create the module structure
    create_standard_module_structure(base_path, args.module_name, args.supabase)
    
    # Add Supabase package to requirements if needed
    if args.supabase:
        try:
            with open(os.path.join(base_path, "requirements.txt"), "r+") as file:
                content = file.read()
                if "supabase" not in content:
                    file.write("\n# Supabase client\nsupabase>=1.0.3\n")
                    print("Added supabase package to requirements.txt")
        except FileNotFoundError:
            with open(os.path.join(base_path, "requirements.txt"), "w") as file:
                file.write("# Supabase client\nsupabase>=1.0.3\n")
                print("Created requirements.txt with supabase package")


if __name__ == "__main__":
    main()