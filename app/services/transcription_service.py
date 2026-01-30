"""Transcription service using OpenAI Whisper."""

import logging
import ssl
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config.settings import get_settings
from app.models.transcription import Transcription
from app.models.file import FileMetadata, FileType
from app.models.document_chunk import DocumentChunk
from app.services.pdf_service import PDFService
from app.services.semantic_search_service import SemanticSearchService

logger = logging.getLogger(__name__)
settings = get_settings()

# Approximate model sizes in bytes (for progress tracking)
MODEL_SIZES = {
    "tiny": 39 * 1024 * 1024,      # ~39 MB
    "base": 74 * 1024 * 1024,      # ~74 MB
    "small": 244 * 1024 * 1024,    # ~244 MB
    "medium": 769 * 1024 * 1024,   # ~769 MB
    "large": 1550 * 1024 * 1024,   # ~1550 MB
}

# Disable SSL verification for Whisper model downloads if needed
# This is a workaround for environments with self-signed certificates
_ssl_patched = False

def _get_whisper_cache_path() -> Path:
    """Get the Whisper model cache directory path."""
    # Whisper stores models in ~/.cache/whisper/ by default
    cache_dir = Path.home() / ".cache" / "whisper"
    return cache_dir


def _get_model_file_path(model_name: str) -> Path:
    """Get the expected file path for a Whisper model."""
    cache_dir = _get_whisper_cache_path()
    # Models are stored as {model_name}.pt
    return cache_dir / f"{model_name}.pt"


def _monitor_model_download_progress(model_name: str, expected_size: int, max_wait: float = 1800.0) -> None:
    """
    Monitor and log the progress of model download.
    
    Args:
        model_name: Name of the Whisper model
        expected_size: Expected file size in bytes
        max_wait: Maximum time to wait in seconds (default 30 minutes)
    """
    model_path = _get_model_file_path(model_name)
    last_size = 0
    last_log_time = time.time()
    start_time = time.time()
    log_interval = 2.0  # Log every 2 seconds
    check_interval = 0.5  # Check every 0.5 seconds
    
    while (time.time() - start_time) < max_wait:
        if model_path.exists():
            try:
                current_size = model_path.stat().st_size
                current_time = time.time()
                
                # Calculate progress percentage
                if expected_size > 0:
                    progress = min(100, int((current_size / expected_size) * 100))
                else:
                    progress = 0
                
                # Log if size changed or enough time passed
                if current_size != last_size or (current_time - last_log_time) >= log_interval:
                    size_mb = current_size / (1024 * 1024)
                    expected_mb = expected_size / (1024 * 1024)
                    elapsed = int(current_time - start_time)
                    logger.info(
                        f"Model download progress: {progress}% "
                        f"({size_mb:.1f} MB / {expected_mb:.1f} MB) "
                        f"[{elapsed}s elapsed]"
                    )
                    last_size = current_size
                    last_log_time = current_time
                    
                    # If download appears complete, check one more time and exit
                    if expected_size > 0 and current_size >= expected_size * 0.95:  # 95% threshold
                        time.sleep(0.5)  # Wait a bit for final writes
                        if model_path.exists():
                            final_size = model_path.stat().st_size
                            if final_size >= expected_size * 0.95:
                                logger.info(f"Model download complete: {final_size / (1024 * 1024):.1f} MB")
                                return
            except (OSError, FileNotFoundError):
                # File might be temporarily unavailable, continue monitoring
                pass
        else:
            # File doesn't exist yet, log that we're waiting
            if time.time() - last_log_time >= log_interval:
                elapsed = int(time.time() - start_time)
                logger.info(f"Waiting for model download to start... [{elapsed}s elapsed]")
                last_log_time = time.time()
        
        time.sleep(check_interval)
    
    # Timeout reached
    if model_path.exists():
        final_size = model_path.stat().st_size / (1024 * 1024)
        logger.warning(f"Progress monitoring timeout. Model file exists: {final_size:.1f} MB")
    else:
        logger.warning("Progress monitoring timeout. Model file not found yet.")


def _patch_ssl_for_whisper():
    """Patch urllib and requests to disable SSL verification for Whisper model downloads."""
    global _ssl_patched
    if _ssl_patched:
        return
    
    try:
        import urllib.request
        
        # Store original urlopen
        _original_urlopen = urllib.request.urlopen
        
        def _urlopen_without_ssl_verify(*args, **kwargs):
            """Wrapper for urlopen that disables SSL verification."""
            # Create SSL context without verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Always use our SSL context
            kwargs['context'] = ssl_context
            
            return _original_urlopen(*args, **kwargs)
        
        # Patch urllib.request.urlopen
        urllib.request.urlopen = _urlopen_without_ssl_verify
        logger.debug("Patched urllib.request.urlopen for SSL verification bypass")
        
        # Also patch urllib.request.install_opener to use our handler
        class NoSSLHTTPSHandler(urllib.request.HTTPSHandler):
            def __init__(self, *args, **kwargs):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                super().__init__(*args, context=ssl_context, **kwargs)
        
        # Install opener with our handler
        opener = urllib.request.build_opener(NoSSLHTTPSHandler())
        urllib.request.install_opener(opener)
        
        # Also patch requests if available (Whisper might use it)
        try:
            import requests
            original_get = requests.get
            original_post = requests.post
            
            def _requests_get_without_ssl(*args, **kwargs):
                kwargs['verify'] = False
                return original_get(*args, **kwargs)
            
            def _requests_post_without_ssl(*args, **kwargs):
                kwargs['verify'] = False
                return original_post(*args, **kwargs)
            
            requests.get = _requests_get_without_ssl
            requests.post = _requests_post_without_ssl
        except ImportError:
            pass  # requests not available, that's fine
        
        _ssl_patched = True
        logger.warning("Patched SSL to disable certificate verification for Whisper model downloads. "
                      "This is less secure but needed for environments with self-signed certificates.")
    except Exception as e:
        logger.warning(f"Failed to patch SSL for Whisper: {e}")


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
            
            # Automatically create chunks from transcription for RAG/search
            try:
                chunks = await TranscriptionService._create_chunks_from_transcription(
                    file_metadata.id,
                    transcription.full_text,
                    db
                )
                
                # Automatically generate embeddings for the chunks if OpenAI API key is available
                if chunks and settings.openai_api_key:
                    try:
                        chunk_ids = [chunk.id for chunk in chunks]
                        await SemanticSearchService.generate_embeddings_for_chunks(
                            chunk_ids=chunk_ids,
                            db=db
                        )
                        logger.info(f"Successfully generated embeddings for {len(chunk_ids)} chunks from transcription")
                    except Exception as embed_err:
                        # Log error but don't fail transcription
                        logger.warning(f"Failed to generate embeddings for transcription chunks: {embed_err}")
            except Exception as chunk_err:
                # Log error but don't fail transcription
                logger.warning(f"Failed to create chunks from transcription for file {file_metadata.id}: {chunk_err}")
            
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
            # Patch SSL before importing whisper (whisper uses urllib internally)
            _patch_ssl_for_whisper()
            
            import whisper
            
            logger.info(f"Loading Whisper model: {settings.whisper_model}")
            
            # Check if model already exists
            model_path = _get_model_file_path(settings.whisper_model)
            model_exists = model_path.exists()
            
            if model_exists:
                model_size = model_path.stat().st_size / (1024 * 1024)
                logger.info(f"Model found in cache ({model_size:.1f} MB). Loading...")
            else:
                expected_size = MODEL_SIZES.get(settings.whisper_model, 0)
                if expected_size > 0:
                    logger.info(
                        f"Model not found in cache. Downloading {settings.whisper_model} "
                        f"(~{expected_size / (1024 * 1024):.0f} MB). "
                        f"This may take 5-15 minutes depending on your internet speed."
                    )
                else:
                    logger.info(
                        f"Model not found in cache. Downloading {settings.whisper_model}. "
                        f"This may take several minutes depending on your internet speed."
                    )
            
            # Load model (may download if not cached)
            # SSL verification is disabled via urllib patching above
            # Run in executor to avoid blocking the event loop
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Start progress monitoring in background if model doesn't exist
            if not model_exists:
                expected_size = MODEL_SIZES.get(settings.whisper_model, 0)
                if expected_size > 0:
                    # Start progress monitoring in a separate task
                    async def monitor_progress():
                        await loop.run_in_executor(
                            None,
                            _monitor_model_download_progress,
                            settings.whisper_model,
                            expected_size
                        )
                    
                    # Start monitoring (don't await, let it run in background)
                    asyncio.create_task(monitor_progress())
            
            # Add timeout for model loading
            # Use shorter timeout for cached models (2 min), longer for downloads (10 min)
            load_timeout = 120.0 if model_exists else 600.0  # 2 min cached, 10 min download
            
            try:
                logger.info(f"Starting model load (timeout: {int(load_timeout)}s)...")
                start_load_time = time.time()
                
                model = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: whisper.load_model(settings.whisper_model)
                    ),
                    timeout=load_timeout
                )
                
                load_duration = int(time.time() - start_load_time)
                logger.info(f"Whisper model '{settings.whisper_model}' loaded successfully in {load_duration}s")
            except asyncio.TimeoutError:
                error_msg = (
                    f"Model loading timed out after {int(load_timeout)}s. "
                    f"The local Whisper model is taking too long to load."
                )
                logger.error(error_msg)
                
                # Try to fallback to OpenAI API if available
                if settings.openai_api_key:
                    logger.warning("Falling back to OpenAI Whisper API due to local model loading timeout...")
                    try:
                        logger.info("Using OpenAI Whisper API for transcription...")
                        return await TranscriptionService._transcribe_with_openai_api(
                            file_path, language, task
                        )
                    except Exception as api_err:
                        logger.error(f"OpenAI API fallback also failed: {api_err}")
                        raise Exception(
                            f"{error_msg}\n\n"
                            f"Both local Whisper and OpenAI API failed. "
                            f"To use OpenAI API exclusively, set USE_OPENAI_WHISPER_API=true in your .env file."
                        )
                else:
                    raise Exception(
                        f"{error_msg}\n\n"
                        f"To fix this:\n"
                        f"1. Use OpenAI Whisper API by setting USE_OPENAI_WHISPER_API=true and OPENAI_API_KEY in your .env file\n"
                        f"2. Try a smaller model (tiny instead of base)\n"
                        f"3. Check system resources (RAM/CPU)"
                    )
            except Exception as load_err:
                # Handle other model loading errors (memory issues, corrupted model, etc.)
                error_msg = f"Failed to load local Whisper model: {str(load_err)}"
                logger.error(error_msg)
                
                # Try to fallback to OpenAI API if available
                if settings.openai_api_key:
                    logger.warning("Falling back to OpenAI Whisper API due to local model loading error...")
                    try:
                        logger.info("Using OpenAI Whisper API for transcription...")
                        return await TranscriptionService._transcribe_with_openai_api(
                            file_path, language, task
                        )
                    except Exception as api_err:
                        logger.error(f"OpenAI API fallback also failed: {api_err}")
                        raise Exception(
                            f"{error_msg}\n\n"
                            f"Both local Whisper and OpenAI API failed. "
                            f"To use OpenAI API exclusively, set USE_OPENAI_WHISPER_API=true in your .env file."
                        )
                else:
                    raise Exception(
                        f"{error_msg}\n\n"
                        f"To fix this:\n"
                        f"1. Use OpenAI Whisper API by setting USE_OPENAI_WHISPER_API=true and OPENAI_API_KEY in your .env file\n"
                        f"2. Try deleting the cached model and re-downloading: rm ~/.cache/whisper/{settings.whisper_model}.pt\n"
                        f"3. Check system resources (RAM/CPU)"
                    )
            
            logger.info(f"Starting transcription of {file_path}")
            # Transcribe (also run in executor as it's CPU-intensive)
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(
                    str(file_path),
                    language=language if language else None,
                    task=task,
                    verbose=False
                )
            )
            logger.info(f"Transcription completed successfully")
            
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
            error_msg = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in error_msg or "SSL" in error_msg or "certificate" in error_msg.lower():
                logger.error("SSL certificate error during Whisper model download. "
                           "Consider using OpenAI Whisper API instead by setting USE_OPENAI_WHISPER_API=true")
                raise Exception(
                    f"Local Whisper transcription failed due to SSL certificate error: {error_msg}. "
                    "To fix this, either:\n"
                    "1. Use OpenAI Whisper API by setting USE_OPENAI_WHISPER_API=true in your .env file\n"
                    "2. Install/update certificates: pip install --upgrade certifi\n"
                    "3. Configure your system's SSL certificates properly"
                )
            raise Exception(f"Local Whisper transcription failed: {error_msg}")
    
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
    async def _create_chunks_from_transcription(
        file_id: int,
        transcription_text: str,
        db: AsyncSession,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Create document chunks from transcription text for RAG/search.
        
        Args:
            file_id: ID of the file
            transcription_text: Full transcription text
            db: Database session
            chunk_size: Characters per chunk (defaults to settings)
            chunk_overlap: Character overlap (defaults to settings)
            strategy: Chunking strategy (defaults to settings)
        
        Returns:
            List of DocumentChunk objects
        """
        if not transcription_text or not transcription_text.strip():
            logger.warning(f"No transcription text to chunk for file {file_id}")
            return []
        
        # Use settings defaults if not provided
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        strategy = strategy or settings.chunking_strategy
        
        # Delete existing chunks for this file
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.file_id == file_id)
        )
        await db.commit()
        
        # Split text into chunks using PDFService chunking logic
        chunks_data = PDFService._split_text_into_chunks(
            transcription_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy
        )
        
        # Create chunk records
        chunk_objects = []
        for idx, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                file_id=file_id,
                chunk_index=idx,
                text=chunk_data["text"],
                char_count=len(chunk_data["text"]),
                token_count=chunk_data.get("token_count"),
                page_number=None,  # Not applicable for transcriptions
                start_char=chunk_data.get("start_char"),
                end_char=chunk_data.get("end_char"),
                chunk_metadata=None  # Can add timestamp info later if needed
            )
            db.add(chunk)
            chunk_objects.append(chunk)
        
        await db.commit()
        
        # Refresh all chunks to get IDs
        for chunk in chunk_objects:
            await db.refresh(chunk)
        
        logger.info(f"Successfully created {len(chunk_objects)} chunks from transcription for file {file_id}")
        return chunk_objects
    
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

