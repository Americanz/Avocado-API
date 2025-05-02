# from fastapi import (
#     APIRouter,
#     Depends,
#     HTTPException,
#     UploadFile,
#     File,
#     Form,
#     Query,
#     status,
#     Path,
# )
# from fastapi.responses import JSONResponse
# from typing import List, Optional
# from src.core.security.jwt import get_current_user, JWTPayload
# from ..services.service import FilesManagerService
# from ..services.supabase_storage import SupabaseStorageService
# from ..schemas.supabase_models import Files, FilesCreate, FilesUpdate
# import io
# import uuid
# from datetime import datetime

# router = APIRouter(tags=["files-manager"])


# @router.get("/", response_model=List[Files])
# async def get_files(
#     folder: Optional[str] = Query(None, description="Filter files by folder"),
#     limit: Optional[int] = Query(50, description="Limit number of results"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Get all files for the current user or in a specific folder
#     """
#     return await FilesManagerService.get_all_files(
#         folder=folder, user_id=current_user.sub, limit=limit
#     )


# @router.get("/{file_id}", response_model=Files)
# async def get_file(
#     file_id: str = Path(..., description="The ID of the file to get"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Get a specific file by ID
#     """
#     file = await FilesManagerService.get_file_by_id(file_id)

#     if not file:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
#         )

#     # Перевірка доступу: файл має належати поточному користувачу або бути публічним
#     if not file.is_public and file.user_id != current_user.sub:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this file"
#         )

#     return file


# @router.post("/upload", response_model=Files)
# async def upload_file(
#     file: UploadFile = File(...),
#     folder: Optional[str] = Form(None),
#     description: Optional[str] = Form(None),
#     is_public: bool = Form(True),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Upload a file to Supabase Storage and create a database record
#     """
#     try:
#         # Читаємо вміст файлу
#         file_content = await file.read()
#         file_size = len(file_content)

#         # Генеруємо унікальне ім'я файлу
#         file_ext = file.filename.split(".")[-1] if "." in file.filename else ""
#         unique_filename = (
#             f"{uuid.uuid4()}.{file_ext}" if file_ext else f"{uuid.uuid4()}"
#         )

#         # Завантажуємо файл у Supabase Storage
#         file_binary = io.BytesIO(file_content)
#         result = await SupabaseStorageService.upload_file(
#             file_path=unique_filename,
#             file_binary=file_binary,
#             content_type=file.content_type,
#             folder=folder,
#         )

#         # Створюємо запис у базі даних
#         file_data = FilesCreate(
#             name=file.filename,
#             description=description,
#             file_path=unique_filename,
#             file_size=file_size,
#             mime_type=file.content_type,
#             folder=folder,
#             is_public=is_public,
#             metadata={
#                 "original_name": file.filename,
#                 "upload_date": datetime.now().isoformat(),
#             },
#         )

#         # Зберігаємо запис і повертаємо результат
#         return await FilesManagerService.create_file(file_data, current_user)

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to upload file: {str(e)}",
#         )


# @router.put("/{file_id}", response_model=Files)
# async def update_file_metadata(
#     file_id: str,
#     file_data: FilesUpdate,
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Update file metadata
#     """
#     # Перевіряємо, чи існує файл і чи має користувач доступ
#     file = await FilesManagerService.get_file_by_id(file_id)

#     if not file:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
#         )

#     if file.user_id != current_user.sub:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have permission to update this file",
#         )

#     # Оновлюємо метадані файлу
#     updated_file = await FilesManagerService.update_file(file_id, file_data)

#     if not updated_file:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to update file metadata",
#         )

#     return updated_file


# @router.delete("/{file_id}")
# async def delete_file(
#     file_id: str, current_user: JWTPayload = Depends(get_current_user)
# ):
#     """
#     Delete a file and its metadata
#     """
#     # Перевіряємо, чи існує файл і чи має користувач доступ
#     file = await FilesManagerService.get_file_by_id(file_id)

#     if not file:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
#         )

#     if file.user_id != current_user.sub:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have permission to delete this file",
#         )

#     # Видаляємо файл та його запис
#     success = await FilesManagerService.delete_file(file_id)

#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete file",
#         )

#     return JSONResponse(
#         status_code=status.HTTP_200_OK,
#         content={"message": "File deleted successfully", "id": file_id},
#     )
