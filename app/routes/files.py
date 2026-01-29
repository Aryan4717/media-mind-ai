"""File upload and management endpoints."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pathlib import Path

from app.config.database import get_db
from app.services.file_service import FileService
from app.schemas.file import FileUploadResponse, FileListResponse, FileListPaginated
from app.models.file import FileType

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file (PDF, audio, or video).
    
    - **file**: The file to upload
    - Returns file metadata including ID, filename, type, and size
    """
    try:
        file_metadata = await FileService.save_file(file, db)
        
        return FileUploadResponse(
            id=file_metadata.id,
            filename=file_metadata.filename,
            original_filename=file_metadata.original_filename,
            file_type=file_metadata.file_type,
            file_size=file_metadata.file_size,
            file_size_mb=file_metadata.file_size_mb,
            mime_type=file_metadata.mime_type,
            upload_time=file_metadata.upload_time,
            message="File uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post("/upload/multiple", response_model=List[FileUploadResponse], status_code=201)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple files at once.
    
    - **files**: List of files to upload
    - Returns list of file metadata for each uploaded file
    """
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            file_metadata = await FileService.save_file(file, db)
            uploaded_files.append(FileUploadResponse(
                id=file_metadata.id,
                filename=file_metadata.filename,
                original_filename=file_metadata.original_filename,
                file_type=file_metadata.file_type,
                file_size=file_metadata.file_size,
                file_size_mb=file_metadata.file_size_mb,
                mime_type=file_metadata.mime_type,
                upload_time=file_metadata.upload_time,
                message="File uploaded successfully"
            ))
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    if errors and not uploaded_files:
        raise HTTPException(
            status_code=400,
            detail=f"All files failed to upload: {', '.join(errors)}"
        )
    
    return uploaded_files


@router.get("/list", response_model=FileListPaginated)
async def list_files(
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    List uploaded files with pagination.
    
    - **file_type**: Optional filter by file type (pdf, audio, video, etc.)
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    """
    files, total = await FileService.list_files(db, file_type, page, page_size)
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return FileListPaginated(
        files=[FileListResponse(
            id=f.id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_type=f.file_type,
            file_size=f.file_size,
            file_size_mb=f.file_size_mb,
            mime_type=f.mime_type,
            upload_time=f.upload_time
        ) for f in files],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{file_id}", response_model=FileListResponse)
async def get_file_metadata(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get file metadata by ID.
    
    - **file_id**: The ID of the file
    """
    file_metadata = await FileService.get_file_by_id(file_id, db)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileListResponse(
        id=file_metadata.id,
        filename=file_metadata.filename,
        original_filename=file_metadata.original_filename,
        file_type=file_metadata.file_type,
        file_size=file_metadata.file_size,
        file_size_mb=file_metadata.file_size_mb,
        mime_type=file_metadata.mime_type,
        upload_time=file_metadata.upload_time
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Download a file by ID.
    
    - **file_id**: The ID of the file to download
    """
    file_metadata = await FileService.get_file_by_id(file_id, db)
    
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file_metadata.file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_metadata.original_filename,
        media_type=file_metadata.mime_type or "application/octet-stream"
    )


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a file and its metadata.
    
    - **file_id**: The ID of the file to delete
    """
    success = await FileService.delete_file(file_id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return None

