# """
# Routes for file storage operations
# """

# from fastapi import (
#     APIRouter,
#     Depends,
#     UploadFile,
#     File,
#     HTTPException,
#     status,
#     Path,
#     Query,
# )
# from fastapi.responses import JSONResponse, StreamingResponse
# from typing import List, Optional
# from src.core.security.jwt import get_current_user, JWTPayload
# from ..services.supabase_storage import SupabaseStorageService
# import io

# router = APIRouter(tags=["file-storage"])


# @router.post("/upload")
# async def upload_file_to_storage(
#     file: UploadFile = File(...),
#     folder: Optional[str] = Query(None, description="Folder to store the file in"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Upload a file directly to Supabase Storage
#     """
#     try:
#         file_content = await file.read()
#         file_buffer = io.BytesIO(file_content)

#         result = await SupabaseStorageService.upload_file(
#             file_path=file.filename,
#             file_binary=file_buffer,
#             content_type=file.content_type,
#             folder=folder,
#         )

#         file_url = await SupabaseStorageService.get_file_url(
#             file_path=file.filename, folder=folder
#         )

#         return {
#             "success": True,
#             "filename": file.filename,
#             "size": len(file_content),
#             "content_type": file.content_type,
#             "folder": folder,
#             "url": file_url,
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to upload file: {str(e)}",
#         )


# @router.get("/files")
# async def list_files(
#     folder: Optional[str] = Query(None, description="Folder to list files from"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     List files in storage, optionally filtered by folder
#     """
#     try:
#         files = await SupabaseStorageService.list_files(folder=folder)
#         return files

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to list files: {str(e)}",
#         )


# @router.get("/download/{filename}")
# async def download_file(
#     filename: str = Path(..., description="File name to download"),
#     folder: Optional[str] = Query(None, description="Folder where the file is stored"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Download a file from storage
#     """
#     try:
#         file_data, content_type = await SupabaseStorageService.download_file(
#             file_path=filename, folder=folder
#         )

#         return StreamingResponse(
#             io.BytesIO(file_data),
#             media_type=content_type,
#             headers={"Content-Disposition": f"attachment; filename={filename}"},
#         )

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to download file: {str(e)}",
#         )


# @router.delete("/{filename}")
# async def delete_file_from_storage(
#     filename: str = Path(..., description="File name to delete"),
#     folder: Optional[str] = Query(None, description="Folder where the file is stored"),
#     current_user: JWTPayload = Depends(get_current_user),
# ):
#     """
#     Delete a file from storage
#     """
#     try:
#         result = await SupabaseStorageService.delete_file(
#             file_path=filename, folder=folder
#         )

#         return {
#             "success": True,
#             "message": f"File {filename} deleted successfully",
#             "filename": filename,
#             "folder": folder,
#         }

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete file: {str(e)}",
#         )
