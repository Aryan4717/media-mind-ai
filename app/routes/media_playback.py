"""Media playback endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config.database import get_db
from app.services.media_playback_service import MediaPlaybackService
from app.schemas.media_playback import PlaybackInfoResponse, PlaybackRequest

router = APIRouter()


@router.get("/files/{file_id}/playback", response_model=PlaybackInfoResponse)
async def get_media_playback_info(
    file_id: int,
    timestamp: Optional[float] = Query(None, ge=0, description="Start timestamp in seconds"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get media playback information including file URL and timestamp.
    
    - **file_id**: ID of the audio/video file
    - **timestamp**: Optional start timestamp in seconds (query parameter)
    
    Returns file URL and timestamp for frontend media player integration.
    """
    try:
        result = await MediaPlaybackService.get_playback_info(
            file_id=file_id,
            db=db,
            timestamp=timestamp
        )
        
        return PlaybackInfoResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            file_url=result["file_url"],
            timestamp=result["timestamp"],
            formatted_timestamp=result["formatted_timestamp"],
            mime_type=result.get("mime_type"),
            file_size_mb=result["file_size_mb"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get playback info: {str(e)}")


@router.post("/files/{file_id}/playback", response_model=PlaybackInfoResponse)
async def get_media_playback_info_post(
    file_id: int,
    request: PlaybackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get media playback information (POST method with body).
    
    - **file_id**: ID of the audio/video file
    - **timestamp**: Optional start timestamp in seconds (in request body)
    
    Returns file URL and timestamp for frontend media player integration.
    """
    try:
        result = await MediaPlaybackService.get_playback_info(
            file_id=file_id,
            timestamp=request.timestamp,
            db=db
        )
        
        return PlaybackInfoResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            file_url=result["file_url"],
            timestamp=result["timestamp"],
            formatted_timestamp=result["formatted_timestamp"],
            mime_type=result.get("mime_type"),
            file_size_mb=result["file_size_mb"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get playback info: {str(e)}")


@router.get("/files/{file_id}/playback/from-timestamp/{start_time}", response_model=PlaybackInfoResponse)
async def get_media_playback_from_timestamp(
    file_id: int,
    start_time: float = Path(..., ge=0, description="Start timestamp in seconds"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get media playback info starting from a specific timestamp.
    
    - **file_id**: ID of the audio/video file
    - **start_time**: Start timestamp in seconds (path parameter)
    
    Convenient endpoint for starting playback from a specific time.
    """
    try:
        result = await MediaPlaybackService.get_playback_info_from_timestamp(
            file_id=file_id,
            db=db,
            start_time=start_time
        )
        
        return PlaybackInfoResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            file_url=result["file_url"],
            timestamp=result["timestamp"],
            formatted_timestamp=result["formatted_timestamp"],
            mime_type=result.get("mime_type"),
            file_size_mb=result["file_size_mb"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get playback info: {str(e)}")

