from pydantic import BaseModel, Field
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
