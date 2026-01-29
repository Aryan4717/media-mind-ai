"""File upload and response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.file import FileType


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    
    id: int
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int = Field(..., description="File size in bytes")
    file_size_mb: float = Field(..., description="File size in megabytes")
    mime_type: Optional[str] = None
    upload_time: datetime
    message: str = "File uploaded successfully"
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "document_20240101_123456.pdf",
                "original_filename": "my_document.pdf",
                "file_type": "pdf",
                "file_size": 1048576,
                "file_size_mb": 1.0,
                "mime_type": "application/pdf",
                "upload_time": "2024-01-01T12:34:56",
                "message": "File uploaded successfully"
            }
        }


class FileListResponse(BaseModel):
    """Response schema for file list."""
    
    id: int
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int
    file_size_mb: float
    mime_type: Optional[str] = None
    upload_time: datetime
    
    class Config:
        from_attributes = True


class FileListPaginated(BaseModel):
    """Paginated file list response."""
    
    files: list[FileListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

