"""Document processing endpoints for PDF text extraction and chunking."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config.database import get_db
from app.services.pdf_service import PDFService
from app.services.file_service import FileService
from app.schemas.document_chunk import (
    DocumentChunkResponse,
    DocumentChunkListResponse,
    ProcessPDFRequest,
    ProcessPDFResponse
)
from app.models.file import FileType

router = APIRouter()


@router.post("/files/{file_id}/process", response_model=ProcessPDFResponse, status_code=201)
async def process_pdf(
    file_id: int,
    request: ProcessPDFRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract text from PDF and split into chunks.
    
    - **file_id**: ID of the uploaded PDF file
    - **chunk_size**: Optional characters per chunk (defaults to settings)
    - **chunk_overlap**: Optional character overlap (defaults to settings)
    - **strategy**: Optional chunking strategy: 'fixed', 'sentence', or 'paragraph'
    
    Returns processing results with chunk count and statistics.
    """
    # Get file metadata
    file_metadata = await FileService.get_file_by_id(file_id, db)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is PDF
    if file_metadata.file_type != FileType.PDF:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_metadata.file_type}' is not supported. Only PDF files can be processed."
        )
    
    try:
        chunks = await PDFService.process_pdf(
            file_metadata,
            db,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            strategy=request.strategy
        )
        
        # Calculate statistics
        total_chars = sum(chunk.char_count for chunk in chunks)
        total_tokens = sum(chunk.token_count for chunk in chunks if chunk.token_count)
        
        return ProcessPDFResponse(
            file_id=file_id,
            chunks_created=len(chunks),
            total_characters=total_chars,
            total_tokens=total_tokens if total_tokens else None,
            message="PDF processed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


@router.get("/files/{file_id}/chunks", response_model=DocumentChunkListResponse)
async def get_file_chunks(
    file_id: int,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of chunks to return"),
    offset: int = Query(0, ge=0, description="Number of chunks to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chunks for a PDF file.
    
    - **file_id**: ID of the file
    - **limit**: Maximum number of chunks to return (optional)
    - **offset**: Number of chunks to skip (for pagination)
    """
    # Verify file exists
    file_metadata = await FileService.get_file_by_id(file_id, db)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    chunks = await PDFService.get_chunks_by_file_id(file_id, db, limit=limit, offset=offset)
    
    # Get total count
    all_chunks = await PDFService.get_chunks_by_file_id(file_id, db)
    total = len(all_chunks)
    
    return DocumentChunkListResponse(
        chunks=[
            DocumentChunkResponse(
                id=chunk.id,
                file_id=chunk.file_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                char_count=chunk.char_count,
                token_count=chunk.token_count,
                page_number=chunk.page_number,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                chunk_metadata=chunk.chunk_metadata,
                created_at=chunk.created_at
            )
            for chunk in chunks
        ],
        total=total,
        file_id=file_id
    )


@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(
    chunk_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific chunk by ID.
    
    - **chunk_id**: ID of the chunk
    """
    chunk = await PDFService.get_chunk_by_id(chunk_id, db)
    
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    return DocumentChunkResponse(
        id=chunk.id,
        file_id=chunk.file_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        char_count=chunk.char_count,
        token_count=chunk.token_count,
        page_number=chunk.page_number,
        start_char=chunk.start_char,
        end_char=chunk.end_char,
        metadata=chunk.metadata,
        created_at=chunk.created_at
    )


@router.delete("/files/{file_id}/chunks", status_code=204)
async def delete_file_chunks(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all chunks for a file.
    
    - **file_id**: ID of the file
    """
    # Verify file exists
    file_metadata = await FileService.get_file_by_id(file_id, db)
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    deleted_count = await PDFService.delete_chunks_by_file_id(file_id, db)
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="No chunks found for this file")
    
    return None

