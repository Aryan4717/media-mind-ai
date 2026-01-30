"""File storage and management service."""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func as sql_func
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.models.file import FileMetadata, FileType
from app.models.transcription import Transcription
from app.models.document_chunk import DocumentChunk
from app.models.embedding import ChunkEmbedding

logger = logging.getLogger(__name__)
settings = get_settings()


class FileService:
    """Service for file operations."""
    
    # Base storage directory
    STORAGE_BASE = Path("uploads")
    
    # File type to folder mapping
    TYPE_FOLDERS = {
        FileType.PDF: "pdfs",
        FileType.AUDIO: "audio",
        FileType.VIDEO: "video",
        FileType.IMAGE: "images",
        FileType.DOCUMENT: "documents",
        FileType.OTHER: "other"
    }
    
    # MIME type to file type mapping
    MIME_TYPE_MAPPING = {
        # PDFs
        "application/pdf": FileType.PDF,
        # Audio
        "audio/mpeg": FileType.AUDIO,
        "audio/mp3": FileType.AUDIO,
        "audio/wav": FileType.AUDIO,
        "audio/wave": FileType.AUDIO,
        "audio/x-wav": FileType.AUDIO,
        "audio/ogg": FileType.AUDIO,
        "audio/aac": FileType.AUDIO,
        "audio/flac": FileType.AUDIO,
        # Video
        "video/mp4": FileType.VIDEO,
        "video/mpeg": FileType.VIDEO,
        "video/quicktime": FileType.VIDEO,
        "video/x-msvideo": FileType.VIDEO,
        "video/webm": FileType.VIDEO,
        # Images
        "image/jpeg": FileType.IMAGE,
        "image/jpg": FileType.IMAGE,
        "image/png": FileType.IMAGE,
        "image/gif": FileType.IMAGE,
        "image/webp": FileType.IMAGE,
        # Documents
        "application/msword": FileType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCUMENT,
        "application/vnd.ms-excel": FileType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.DOCUMENT,
        "application/vnd.ms-powerpoint": FileType.DOCUMENT,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": FileType.DOCUMENT,
        "text/plain": FileType.DOCUMENT,
    }
    
    @classmethod
    def _ensure_storage_dirs(cls):
        """Ensure all storage directories exist."""
        cls.STORAGE_BASE.mkdir(parents=True, exist_ok=True)
        for folder in cls.TYPE_FOLDERS.values():
            (cls.STORAGE_BASE / folder).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def _get_file_type(cls, filename: str, mime_type: Optional[str] = None) -> FileType:
        """Determine file type from filename and MIME type."""
        # Try MIME type first
        if mime_type and mime_type in cls.MIME_TYPE_MAPPING:
            return cls.MIME_TYPE_MAPPING[mime_type]
        
        # Fall back to file extension
        ext = Path(filename).suffix.lower().lstrip('.')
        if ext == "pdf":
            return FileType.PDF
        elif ext in ["mp3", "wav", "ogg", "aac", "flac", "m4a"]:
            return FileType.AUDIO
        elif ext in ["mp4", "avi", "mov", "webm", "mkv"]:
            return FileType.VIDEO
        elif ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            return FileType.IMAGE
        elif ext in ["doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"]:
            return FileType.DOCUMENT
        else:
            return FileType.OTHER
    
    @classmethod
    def _generate_filename(cls, original_filename: str) -> str:
        """Generate a unique filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ext = Path(original_filename).suffix
        name = Path(original_filename).stem
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        return f"{safe_name}_{timestamp}{ext}"
    
    @classmethod
    async def save_file(
        cls,
        file: UploadFile,
        db: AsyncSession
    ) -> FileMetadata:
        """Save uploaded file and create metadata record."""
        try:
            # Ensure storage directories exist
            cls._ensure_storage_dirs()
            
            # Validate filename
            if not file.filename:
                raise HTTPException(
                    status_code=400,
                    detail="Filename is required"
                )
            
            # Validate file size
            file_content = await file.read()
            file_size = len(file_content)
            
            if file_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="File is empty"
                )
            
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > settings.max_file_size_mb:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({settings.max_file_size_mb} MB)"
                )
            
            # Determine file type
            file_type = cls._get_file_type(file.filename, file.content_type)
            
            # Check if file type is allowed
            ext = Path(file.filename).suffix.lower().lstrip('.')
            if ext not in settings.allowed_file_types and file_type == FileType.OTHER:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{ext}' is not allowed. Allowed types: {', '.join(settings.allowed_file_types)}"
                )
            
            # Generate unique filename
            unique_filename = cls._generate_filename(file.filename)
            
            # Determine storage path
            type_folder = cls.TYPE_FOLDERS[file_type]
            file_path = cls.STORAGE_BASE / type_folder / unique_filename
            
            # Save file to disk
            file_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(file_path, "wb") as f:
                    f.write(file_content)
            except Exception as e:
                logger.error(f"Error writing file to disk: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save file to disk: {str(e)}"
                )
            
            # Create metadata record with retry logic for database locks
            import asyncio
            max_retries = 3
            retry_delay = 0.5  # seconds
            
            for attempt in range(max_retries):
                try:
                    file_metadata = FileMetadata(
                        filename=unique_filename,
                        original_filename=file.filename,
                        file_type=file_type,
                        file_path=str(file_path),
                        file_size=file_size,
                        file_size_mb=round(file_size_mb, 2),
                        mime_type=file.content_type
                    )
                    
                    db.add(file_metadata)
                    await db.commit()
                    await db.refresh(file_metadata)
                    
                    return file_metadata
                except Exception as e:
                    error_str = str(e).lower()
                    # Check if it's a database lock error
                    if "locked" in error_str or "database is locked" in error_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"Database locked, retrying ({attempt + 1}/{max_retries})...")
                            await db.rollback()
                            await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            # Final attempt failed
                            await db.rollback()
                            if file_path.exists():
                                try:
                                    file_path.unlink()
                                except:
                                    pass
                            logger.error(f"Database locked after {max_retries} attempts. Close DB Browser if open.")
                            raise HTTPException(
                                status_code=503,
                                detail="Database is locked. Please close DB Browser for SQLite if it's open and try again."
                            )
                    else:
                        # Other database errors
                        await db.rollback()
                        if file_path.exists():
                            try:
                                file_path.unlink()
                            except:
                                pass
                        logger.error(f"Error saving file metadata to database: {str(e)}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to save file metadata: {str(e)}"
                        )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in save_file: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading file: {str(e)}"
            )
    
    @classmethod
    async def get_file_by_id(cls, file_id: int, db: AsyncSession) -> Optional[FileMetadata]:
        """Get file metadata by ID."""
        result = await db.execute(
            select(FileMetadata).where(FileMetadata.id == file_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def list_files(
        cls,
        db: AsyncSession,
        file_type: Optional[FileType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[FileMetadata], int]:
        """List files with pagination."""
        query = select(FileMetadata)
        
        if file_type:
            query = query.where(FileMetadata.file_type == file_type)
        
        # Get total count
        count_query = select(sql_func.count()).select_from(FileMetadata)
        if file_type:
            count_query = count_query.where(FileMetadata.file_type == file_type)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(FileMetadata.upload_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        files = result.scalars().all()
        
        return list(files), total
    
    @classmethod
    async def delete_file(cls, file_id: int, db: AsyncSession) -> bool:
        """Delete file and all related data (transcriptions, chunks, embeddings)."""
        file_metadata = await cls.get_file_by_id(file_id, db)
        
        if not file_metadata:
            return False
        
        try:
            # Delete related transcriptions first
            await db.execute(
                delete(Transcription).where(Transcription.file_id == file_id)
            )
            logger.info(f"Deleted transcriptions for file {file_id}")
            
            # Get all chunks for this file to delete their embeddings
            chunks_result = await db.execute(
                select(DocumentChunk.id).where(DocumentChunk.file_id == file_id)
            )
            chunk_ids = [row[0] for row in chunks_result.fetchall()]
            
            # Delete embeddings for these chunks
            if chunk_ids:
                await db.execute(
                    delete(ChunkEmbedding).where(ChunkEmbedding.chunk_id.in_(chunk_ids))
                )
                logger.info(f"Deleted embeddings for {len(chunk_ids)} chunks of file {file_id}")
            
            # Delete document chunks
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.file_id == file_id)
            )
            logger.info(f"Deleted chunks for file {file_id}")
            
            # Delete file from disk
            file_path = Path(file_metadata.file_path)
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"Deleted file from disk: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file from disk {file_path}: {e}")
            
            # Delete file metadata (this will cascade delete any remaining relationships)
            await db.delete(file_metadata)
            await db.commit()
            
            logger.info(f"Successfully deleted file {file_id} and all related data")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise

