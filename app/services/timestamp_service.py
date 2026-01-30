"""Timestamp extraction service for mapping answers to transcript segments."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.transcription import Transcription
from app.models.file import FileMetadata, FileType
from app.services.file_service import FileService

logger = logging.getLogger(__name__)
settings = get_settings()


class TimestampService:
    """Service for extracting timestamps from transcript segments."""
    
    @staticmethod
    async def extract_timestamps_for_text(
        file_id: int,
        text: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Extract timestamps for given text from transcript segments.
        
        Args:
            file_id: ID of the audio/video file
            text: Text to find timestamps for
            db: Database session
        
        Returns:
            List of timestamp dictionaries with start, end, and segment text
        """
        # Get file metadata
        file_metadata = await FileService.get_file_by_id(file_id, db)
        if not file_metadata:
            raise ValueError(f"File {file_id} not found")
        
        # Check if file is audio or video
        if file_metadata.file_type not in [FileType.AUDIO, FileType.VIDEO]:
            raise ValueError(f"File type {file_metadata.file_type} is not supported. Only audio and video files have timestamps.")
        
        # Get transcription
        transcription = await TimestampService._get_transcription(file_id, db)
        if not transcription or not transcription.segments:
            raise ValueError(f"No transcription segments found for file {file_id}")
        
        # Find segments containing the text
        matching_segments = TimestampService._find_matching_segments(
            text, transcription.segments
        )
        
        return matching_segments
    
    @staticmethod
    async def extract_timestamps_for_chunks(
        file_id: int,
        chunk_texts: List[str],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Extract timestamps for multiple chunk texts.
        
        Args:
            file_id: ID of the audio/video file
            chunk_texts: List of text chunks to find timestamps for
            db: Database session
        
        Returns:
            List of timestamp dictionaries grouped by chunk
        """
        # Get transcription
        transcription = await TimestampService._get_transcription(file_id, db)
        if not transcription or not transcription.segments:
            return []
        
        all_timestamps = []
        
        for chunk_text in chunk_texts:
            matching_segments = TimestampService._find_matching_segments(
                chunk_text, transcription.segments
            )
            
            if matching_segments:
                all_timestamps.append({
                    "chunk_text": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                    "timestamps": matching_segments
                })
        
        return all_timestamps
    
    @staticmethod
    async def _get_transcription(
        file_id: int,
        db: AsyncSession
    ) -> Optional[Transcription]:
        """Get transcription for a file."""
        result = await db.execute(
            select(Transcription)
            .where(Transcription.file_id == file_id)
            .where(Transcription.status == "completed")
            .order_by(Transcription.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def _find_matching_segments(
        search_text: str,
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find transcript segments that contain the search text.
        
        Args:
            search_text: Text to search for
            segments: List of transcript segments with timestamps
        
        Returns:
            List of matching segments with timestamps
        """
        if not segments or not search_text:
            return []
        
        # Normalize search text for matching
        search_text_lower = search_text.lower().strip()
        search_words = set(search_text_lower.split())
        
        matching_segments = []
        
        for segment in segments:
            segment_text = segment.get("text", "").lower()
            
            # Check if segment contains significant overlap with search text
            if TimestampService._text_overlap(search_text_lower, segment_text, threshold=0.3):
                matching_segments.append({
                    "start": segment.get("start", 0.0),
                    "end": segment.get("end", 0.0),
                    "text": segment.get("text", ""),
                    "duration": segment.get("end", 0.0) - segment.get("start", 0.0)
                })
        
        # Sort by start time
        matching_segments.sort(key=lambda x: x["start"])
        
        # Merge overlapping segments
        merged_segments = TimestampService._merge_overlapping_segments(matching_segments)
        
        return merged_segments
    
    @staticmethod
    def _text_overlap(text1: str, text2: str, threshold: float = 0.3) -> bool:
        """
        Check if two texts have significant overlap.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Minimum overlap ratio (0-1)
        
        Returns:
            True if overlap exceeds threshold
        """
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return False
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    @staticmethod
    def _merge_overlapping_segments(
        segments: List[Dict[str, Any]],
        gap_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Merge overlapping or closely spaced segments.
        
        Args:
            segments: List of segments with start/end times
            gap_threshold: Maximum gap in seconds to merge segments
        
        Returns:
            List of merged segments
        """
        if not segments:
            return []
        
        merged = []
        current = segments[0].copy()
        
        for segment in segments[1:]:
            # If segments overlap or are close, merge them
            if segment["start"] <= current["end"] + gap_threshold:
                current["end"] = max(current["end"], segment["end"])
                current["text"] += " " + segment["text"]
                current["duration"] = current["end"] - current["start"]
            else:
                merged.append(current)
                current = segment.copy()
        
        merged.append(current)
        return merged
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Format timestamp in seconds to HH:MM:SS format.
        
        Args:
            seconds: Time in seconds
        
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{secs:02d}.{milliseconds:03d}"

