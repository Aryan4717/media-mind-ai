"""Transcription request and response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class TranscriptionSegment(BaseModel):
    """Transcription segment with timestamp."""
    
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text for this segment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start": 0.0,
                "end": 5.2,
                "text": "Hello, this is a transcription segment."
            }
        }


class TranscriptionResponse(BaseModel):
    """Response schema for transcription."""
    
    id: int
    file_id: int
    full_text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    segments: Optional[List[Dict[str, Any]]] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "file_id": 5,
                "full_text": "This is the complete transcription text...",
                "language": "en",
                "duration": 120.5,
                "segments": [
                    {"start": 0.0, "end": 5.2, "text": "First segment"},
                    {"start": 5.2, "end": 10.5, "text": "Second segment"}
                ],
                "status": "completed",
                "error_message": None,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:05:00"
            }
        }


class TranscriptionRequest(BaseModel):
    """Request schema for transcription."""
    
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'es'). Auto-detect if not provided.")
    task: str = Field("transcribe", description="Task type: 'transcribe' or 'translate'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "language": "en",
                "task": "transcribe"
            }
        }


class TranscriptionStatusResponse(BaseModel):
    """Response schema for transcription status."""
    
    id: int
    file_id: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

