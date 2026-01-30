"""Media playback service for generating file URLs and timestamps."""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.services.file_service import FileService
from app.models.file import FileType

logger = logging.getLogger(__name__)
settings = get_settings()


class MediaPlaybackService:
    """Service for generating media playback URLs and timestamps."""
    
    @staticmethod
    async def get_playback_info(
        file_id: int,
        db: AsyncSession,
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get media playback information including file URL and timestamp.
        
        Args:
            file_id: ID of the media file
            timestamp: Optional timestamp in seconds to start playback from
            db: Database session
        
        Returns:
            Dictionary with file URL, timestamp, and metadata
        """
        # Get file metadata
        file_metadata = await FileService.get_file_by_id(file_id, db)
        
        if not file_metadata:
            raise ValueError(f"File {file_id} not found")
        
        # Check if file is audio or video
        if file_metadata.file_type not in [FileType.AUDIO, FileType.VIDEO]:
            raise ValueError(f"File type {file_metadata.file_type} is not supported for playback. Only audio and video files are supported.")
        
        # Generate file URL
        file_url = MediaPlaybackService._generate_file_url(file_id, file_metadata)
        
        # Validate timestamp if provided
        if timestamp is not None and timestamp < 0:
            raise ValueError("Timestamp must be non-negative")
        
        return {
            "file_id": file_id,
            "file_name": file_metadata.original_filename,
            "file_type": file_metadata.file_type.value,
            "file_url": file_url,
            "timestamp": timestamp if timestamp is not None else 0.0,
            "formatted_timestamp": MediaPlaybackService._format_timestamp(timestamp) if timestamp is not None else "00:00.000",
            "mime_type": file_metadata.mime_type,
            "file_size_mb": file_metadata.file_size_mb
        }
    
    @staticmethod
    def _generate_file_url(file_id: int, file_metadata) -> str:
        """
        Generate URL for file download/streaming.
        
        Args:
            file_id: File ID
            file_metadata: File metadata object
        
        Returns:
            File URL
        """
        # Use the download endpoint URL
        # In production, you might want to use a CDN or storage service URL
        # For now, use the API endpoint which works for both development and production
        file_url = f"/api/v1/files/{file_id}/download"
        
        return file_url
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """
        Format timestamp in seconds to HH:MM:SS.mmm format.
        
        Args:
            seconds: Time in seconds
        
        Returns:
            Formatted timestamp string
        """
        if seconds is None:
            return "00:00.000"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    @staticmethod
    async def get_playback_info_from_timestamp(
        file_id: int,
        db: AsyncSession,
        start_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get playback info from a timestamp (e.g., from Q&A response).
        
        Args:
            file_id: ID of the media file
            timestamp_id: Optional timestamp ID from Q&A response
            start_time: Optional start time in seconds
            db: Database session
        
        Returns:
            Dictionary with file URL and timestamp
        """
        # Use provided start_time or default to 0
        timestamp = start_time if start_time is not None else 0.0
        
        return await MediaPlaybackService.get_playback_info(
            file_id=file_id,
            db=db,
            timestamp=timestamp
        )

