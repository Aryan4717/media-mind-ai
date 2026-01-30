"""Summarization endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.summarization_service import SummarizationService
from app.schemas.summarization import (
    SummarizeRequest,
    CustomSummarizeRequest,
    SummaryResponse
)

router = APIRouter()


@router.post("/files/{file_id}/summarize", response_model=SummaryResponse)
async def summarize_file(
    file_id: int,
    request: SummarizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a summary of a PDF, audio transcript, or video transcript.
    
    - **file_id**: ID of the file to summarize
    - **model**: Optional LLM model to use
    - **temperature**: Optional temperature for generation
    - **max_length**: Optional maximum summary length in words
    
    The file must be processed first:
    - PDFs: Process using `/api/v1/files/{file_id}/process`
    - Audio/Video: Transcribe using `/api/v1/files/{file_id}/transcribe`
    """
    try:
        result = await SummarizationService.summarize_file(
            file_id=file_id,
            db=db,
            model=request.model,
            temperature=request.temperature,
            max_length=request.max_length
        )
        
        return SummaryResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            content_type=result["content_type"],
            summary=result["summary"],
            model=result["model"],
            content_length=result["content_length"],
            summary_length=result["summary_length"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post("/files/{file_id}/summarize/custom", response_model=SummaryResponse)
async def summarize_file_custom(
    file_id: int,
    request: CustomSummarizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a summary with a custom prompt.
    
    - **file_id**: ID of the file to summarize
    - **custom_prompt**: Custom prompt for summarization (e.g., "Summarize key points as bullet points")
    - **model**: Optional LLM model to use
    - **temperature**: Optional temperature for generation
    
    Allows for custom summarization styles (bullet points, structured format, etc.).
    """
    if not request.custom_prompt or not request.custom_prompt.strip():
        raise HTTPException(status_code=400, detail="custom_prompt is required")
    
    try:
        result = await SummarizationService.summarize_with_custom_prompt(
            file_id=file_id,
            custom_prompt=request.custom_prompt,
            db=db,
            model=request.model,
            temperature=request.temperature
        )
        
        return SummaryResponse(
            file_id=result["file_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            content_type=result["content_type"],
            summary=result["summary"],
            model=result["model"],
            content_length=result["content_length"],
            summary_length=result["summary_length"],
            custom_prompt=result.get("custom_prompt")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom summarization failed: {str(e)}")

