"""Transcription service using OpenAI Whisper."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.transcription import Transcription
from app.models.file import FileMetadata, FileType

logger = logging.getLogger(__name__)
settings = get_settings()


class TranscriptionService:
    """Service for transcribing audio and video files."""
    
    @staticmethod
    async def transcribe_file(
        file_metadata: FileMetadata,
        db: AsyncSession,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Transcription:
        """
        Transcribe an audio or video file.
        
        Args:
            file_metadata: The file metadata to transcribe
            db: Database session
            language: Optional language code (auto-detect if None)
            task: "transcribe" or "translate"
        
        Returns:
            Transcription object
        """
        # Check if file is audio or video
        if file_metadata.file_type not in [FileType.AUDIO, FileType.VIDEO]:
            raise ValueError(f"File type {file_metadata.file_type} is not supported for transcription")
        
        # Check if transcription already exists
        existing = await TranscriptionService.get_transcription_by_file_id(file_metadata.id, db)
        if existing and existing.status == "completed":
            logger.info(f"Transcription already exists for file {file_metadata.id}")
            return existing
        
        # Create or update transcription record
        if existing:
            transcription = existing
            transcription.status = "processing"
        else:
            transcription = Transcription(
                file_id=file_metadata.id,
                full_text="",
                status="processing"
            )
            db.add(transcription)
            await db.commit()
            await db.refresh(transcription)
        
        try:
            file_path = Path(file_metadata.file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Use OpenAI API or local Whisper
            if settings.use_openai_whisper_api and settings.openai_api_key:
                result = await TranscriptionService._transcribe_with_openai_api(
                    file_path, language, task
                )
            else:
                result = await TranscriptionService._transcribe_with_local_whisper(
                    file_path, language, task
                )
            
            # Update transcription with results
            transcription.full_text = result["text"]
            transcription.language = result.get("language")
            transcription.duration = result.get("duration")
            transcription.segments = result.get("segments", [])
            transcription.status = "completed"
            transcription.error_message = None
            
            await db.commit()
            await db.refresh(transcription)
            
            logger.info(f"Successfully transcribed file {file_metadata.id}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing file {file_metadata.id}: {str(e)}")
            transcription.status = "failed"
            transcription.error_message = str(e)
            await db.commit()
            raise
    
    @staticmethod
    async def _transcribe_with_openai_api(
        file_path: Path,
        language: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            with open(file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language else None,
                    response_format="verbose_json"
                )
            
            # Format segments with timestamps
            segments = []
            if hasattr(transcript, 'segments'):
                for seg in transcript.segments:
                    segments.append({
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text
                    })
            
            return {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else None,
                "duration": getattr(transcript, 'duration', None),
                "segments": segments
            }
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI API transcription failed: {str(e)}")
    
    @staticmethod
    async def _transcribe_with_local_whisper(
        file_path: Path,
        language: Optional[str],
        task: str
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model."""
        try:
            import whisper
            
            # Load model
            model = whisper.load_model(settings.whisper_model)
            
            # Transcribe
            result = model.transcribe(
                str(file_path),
                language=language if language else None,
                task=task,
                verbose=False
            )
            
            # Format segments
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text", "").strip()
                })
            
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language"),
                "duration": result.get("duration"),
                "segments": segments
            }
        except ImportError:
            raise ImportError("Whisper library not installed. Install with: pip install openai-whisper")
        except Exception as e:
            raise Exception(f"Local Whisper transcription failed: {str(e)}")
    
    @staticmethod
    async def get_transcription_by_file_id(
        file_id: int,
        db: AsyncSession
    ) -> Optional[Transcription]:
        """Get transcription by file ID."""
        result = await db.execute(
            select(Transcription).where(Transcription.file_id == file_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_transcription_by_id(
        transcription_id: int,
        db: AsyncSession
    ) -> Optional[Transcription]:
        """Get transcription by ID."""
        result = await db.execute(
            select(Transcription).where(Transcription.id == transcription_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_transcription(
        transcription_id: int,
        db: AsyncSession
    ) -> bool:
        """Delete a transcription."""
        transcription = await TranscriptionService.get_transcription_by_id(transcription_id, db)
        
        if not transcription:
            return False
        
        await db.delete(transcription)
        await db.commit()
        
        return True

