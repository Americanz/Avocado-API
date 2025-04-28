import datetime
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr

# Базова схема для звіту
class ReportBase(BaseModel):
    from_date: str
    to_date: str
    cash_register_id: str
    emails: List[EmailStr]
    custom: bool = False

# Схема для створення звіту
class ReportCreate(BaseModel):
    from_date: str
    to_date: str
    branch_id: str
    cash_register_id: str
    emails: List[EmailStr]
    export_extension: str = "JSON"
    custom: bool = False

# Схема для оновлення звіту
class ReportUpdate(BaseModel):
    processing_status: Optional[str] = None
    report_data: Optional[str] = None
    error_message: Optional[str] = None
    is_processed: Optional[bool] = None

# Схема для відповіді
class ReportResponse(BaseModel):
    id: UUID
    date_created: datetime.datetime
    date_updated: Optional[datetime.datetime] = None
    from_date: datetime.datetime
    to_date: datetime.datetime
    cash_register_id: str
    emails: List[str]
    processing_status: str
    report_data: Optional[Union[Dict[str, Any], str]] = None
    error_message: Optional[str] = None
    is_processed: bool

    model_config = {"from_attributes": True}
