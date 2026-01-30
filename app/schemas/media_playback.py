"""Media playback request and response schemas."""

from pydantic import ConfigDict, BaseModel, Field
from typing import Optional


class PlaybackInfoResponse(BaseModel):
    """Response schema for media playback information."""
    
    file_id: int
    file_name: str
    file_type: str
    file_url: str = Field(..., description="URL to access the media file")
    timestamp: float = Field(..., description="Start timestamp in seconds")
    formatted_timestamp: str = Field(..., description="Formatted timestamp (HH:MM:SS.mmm)")
    mime_type: Optional[str] = None
    file_size_mb: float
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": 1,
                "file_name": "video.mp4",
                "file_type": "video",
                "file_url": "http://localhost:8000/api/v1/files/1/download",
                "timestamp": 10.5,
                "formatted_timestamp": "00:10.500",
                "mime_type": "video/mp4",
                "file_size_mb": 25.5
            }
        }
    )


class PlaybackRequest(BaseModel):
    """Request schema for media playback."""
    
    timestamp: Optional[float] = Field(None, ge=0, description="Start timestamp in seconds (optional)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": 10.5
            }
        }
    )
