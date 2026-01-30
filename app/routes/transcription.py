"""Transcription endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config.database import get_db
from app.services.transcription_service import TranscriptionService
from app.services.file_service import FileService
from app.models.transcription import Transcription
from app.schemas.transcription import (
    TranscriptionResponse,
    TranscriptionRequest,
    TranscriptionStatusResponse
)

router = APIRouter()


@router.post("/files/{file_id}/transcribe", response_model=TranscriptionResponse, status_code=201)
async def transcribe_file(
    file_id: int,
    request: Optional[TranscriptionRequest] = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Transcribe an audio or video file.
    
    - **file_id**: ID of the uploaded file to transcribe
    - **language**: Optional language code (auto-detect if not provided)
    - **task**: "transcribe" or "translate"
    
    Returns transcription with full text and timestamped segments.
    """
    # Create default request if none provided
    if request is None:
        request = TranscriptionRequest()
    
    # Get file metadata
    file_metadata = await FileService.get_file_by_id(file_id, db)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is audio or video
    from app.models.file import FileType
    if file_metadata.file_type not in [FileType.AUDIO, FileType.VIDEO]:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_metadata.file_type}' is not supported for transcription. Only audio and video files are supported."
        )
    
    try:
        transcription = await TranscriptionService.transcribe_file(
            file_metadata,
            db,
            language=request.language if request else None,
            task=request.task if request else "transcribe"
        )
        
        return TranscriptionResponse(
            id=transcription.id,
            file_id=transcription.file_id,
            full_text=transcription.full_text,
            language=transcription.language,
            duration=transcription.duration,
            segments=transcription.segments,
            status=transcription.status,
            error_message=transcription.error_message,
            created_at=transcription.created_at,
            updated_at=transcription.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/files/{file_id}/transcribe/async", response_model=TranscriptionStatusResponse, status_code=202)
async def transcribe_file_async(
    file_id: int,
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start transcription in the background (asynchronous).
    
    - **file_id**: ID of the uploaded file to transcribe
    - **language**: Optional language code
    - **task**: "transcribe" or "translate"
    
    Returns transcription status. Use GET endpoint to check progress.
    """
    # Get file metadata
    file_metadata = await FileService.get_file_by_id(file_id, db)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is audio or video
    from app.models.file import FileType
    if file_metadata.file_type not in [FileType.AUDIO, FileType.VIDEO]:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_metadata.file_type}' is not supported for transcription."
        )
    
    # Start transcription in background
    async def transcribe_background():
        from app.config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db_session:
            try:
                file_meta = await FileService.get_file_by_id(file_id, db_session)
                if file_meta:
                    await TranscriptionService.transcribe_file(
                        file_meta,
                        db_session,
                        language=request.language or None,
                        task=request.task
                    )
            except Exception as e:
                # Update transcription status on error
                transcription = await TranscriptionService.get_transcription_by_file_id(file_id, db_session)
                if transcription:
                    transcription.status = "failed"
                    transcription.error_message = str(e)
                    await db_session.commit()
    
    # Get or create transcription record
    transcription = await TranscriptionService.get_transcription_by_file_id(file_id, db)
    
    if not transcription:
        transcription = Transcription(
            file_id=file_id,
            full_text="",
            status="pending"
        )
        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)
    
    # Add background task
    background_tasks.add_task(transcribe_background)
    
    return TranscriptionStatusResponse(
        id=transcription.id,
        file_id=transcription.file_id,
        status=transcription.status,
        error_message=transcription.error_message,
        created_at=transcription.created_at
    )


@router.get("/files/{file_id}/transcription", response_model=TranscriptionResponse)
async def get_transcription(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription for a file.
    
    - **file_id**: ID of the file
    """
    transcription = await TranscriptionService.get_transcription_by_file_id(file_id, db)
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return TranscriptionResponse(
        id=transcription.id,
        file_id=transcription.file_id,
        full_text=transcription.full_text,
        language=transcription.language,
        duration=transcription.duration,
        segments=transcription.segments,
        status=transcription.status,
        error_message=transcription.error_message,
        created_at=transcription.created_at,
        updated_at=transcription.updated_at
    )


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription_by_id(
    transcription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription by ID.
    
    - **transcription_id**: ID of the transcription
    """
    transcription = await TranscriptionService.get_transcription_by_id(transcription_id, db)
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return TranscriptionResponse(
        id=transcription.id,
        file_id=transcription.file_id,
        full_text=transcription.full_text,
        language=transcription.language,
        duration=transcription.duration,
        segments=transcription.segments,
        status=transcription.status,
        error_message=transcription.error_message,
        created_at=transcription.created_at,
        updated_at=transcription.updated_at
    )


@router.delete("/transcriptions/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a transcription.
    
    - **transcription_id**: ID of the transcription to delete
    """
    success = await TranscriptionService.delete_transcription(transcription_id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return None

