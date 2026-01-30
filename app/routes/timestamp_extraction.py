"""Timestamp extraction endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional

from app.config.database import get_db
from app.services.timestamp_service import TimestampService
from app.schemas.qa import TimestampInfo

router = APIRouter()


class ExtractTimestampsRequest(BaseModel):
    """Request schema for timestamp extraction."""
    
    text: str = Field(..., description="Text to find timestamps for")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is the text to find in the transcript"
            }
        }


class ExtractTimestampsResponse(BaseModel):
    """Response schema for timestamp extraction."""
    
    file_id: int
    text: str
    timestamps: List[TimestampInfo]
    total_segments: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1,
                "text": "This is the text to find",
                "timestamps": [
                    {
                        "start": 10.5,
                        "end": 25.3,
                        "text": "This is the transcript segment...",
                        "duration": 14.8,
                        "formatted_start": "00:10.500",
                        "formatted_end": "00:25.300"
                    }
                ],
                "total_segments": 1
            }
        }


@router.post("/files/{file_id}/timestamps", response_model=ExtractTimestampsResponse)
async def extract_timestamps(
    file_id: int,
    request: ExtractTimestampsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract timestamps for given text from audio/video transcript.
    
    - **file_id**: ID of the audio/video file
    - **text**: Text to find timestamps for
    
    Returns timestamps where the text appears in the transcript.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        timestamps = await TimestampService.extract_timestamps_for_text(
            file_id=file_id,
            text=request.text,
            db=db
        )
        
        # Format timestamps
        formatted_timestamps = [
            TimestampInfo(
                start=ts["start"],
                end=ts["end"],
                text=ts["text"],
                duration=ts["duration"],
                formatted_start=TimestampService.format_timestamp(ts["start"]),
                formatted_end=TimestampService.format_timestamp(ts["end"])
            )
            for ts in timestamps
        ]
        
        return ExtractTimestampsResponse(
            file_id=file_id,
            text=request.text,
            timestamps=formatted_timestamps,
            total_segments=len(formatted_timestamps)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timestamp extraction failed: {str(e)}")


@router.get("/files/{file_id}/timestamps/answer/{answer_id}", response_model=ExtractTimestampsResponse)
async def extract_timestamps_for_answer(
    file_id: int,
    answer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract timestamps for a chatbot answer.
    
    This endpoint extracts timestamps for an answer that was generated from a Q&A query.
    The answer_id can be used to identify which answer to extract timestamps for.
    
    Note: This is a simplified version. In a full implementation, you might store
    answer metadata and retrieve the original answer text.
    """
    raise HTTPException(
        status_code=501,
        detail="This endpoint requires answer storage. Use /files/{file_id}/timestamps with text parameter instead."
    )

