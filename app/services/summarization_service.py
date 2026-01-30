"""Summarization service using LLM for PDFs, audio, and video transcripts."""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.document_chunk import DocumentChunk
from app.models.transcription import Transcription
from app.models.file import FileMetadata, FileType
from app.services.file_service import FileService

logger = logging.getLogger(__name__)
settings = get_settings()


class SummarizationService:
    """Service for generating summaries of PDFs, audio, and video transcripts."""
    
    @staticmethod
    async def summarize_file(
        file_id: int,
        db: AsyncSession,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a summary for a file (PDF, audio, or video).
        
        Args:
            file_id: ID of the file to summarize
            db: Database session
            model: LLM model to use (defaults to settings)
            temperature: Temperature for LLM (defaults to settings)
            max_length: Maximum summary length in words (optional)
        
        Returns:
            Dictionary with summary and metadata
        """
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for summarization")
        
        # Get file metadata
        file_metadata = await FileService.get_file_by_id(file_id, db)
        if not file_metadata:
            raise ValueError(f"File {file_id} not found")
        
        # Get content based on file type
        if file_metadata.file_type == FileType.PDF:
            content = await SummarizationService._get_pdf_content(file_id, db)
            content_type = "PDF document"
        elif file_metadata.file_type in [FileType.AUDIO, FileType.VIDEO]:
            content = await SummarizationService._get_transcript_content(file_id, db)
            content_type = f"{file_metadata.file_type.value} transcript"
        else:
            raise ValueError(f"File type {file_metadata.file_type} is not supported for summarization. Only PDF, audio, and video files are supported.")
        
        if not content or not content.strip():
            raise ValueError(f"No content found for {content_type}. Please process the file first (extract text for PDFs or transcribe for audio/video).")
        
        # Generate summary using LLM
        model = model or settings.llm_model
        temperature = temperature if temperature is not None else settings.llm_temperature
        
        try:
            summary = await SummarizationService._generate_summary(
                content=content,
                content_type=content_type,
                model=model,
                temperature=temperature,
                max_length=max_length
            )
            
            return {
                "file_id": file_id,
                "file_name": file_metadata.original_filename,
                "file_type": file_metadata.file_type.value,
                "content_type": content_type,
                "summary": summary,
                "model": model,
                "content_length": len(content),
                "summary_length": len(summary)
            }
        except Exception as e:
            logger.error(f"Error generating summary for file {file_id}: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    @staticmethod
    async def _get_pdf_content(file_id: int, db: AsyncSession) -> str:
        """Get all text content from PDF chunks."""
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.file_id == file_id)
            .order_by(DocumentChunk.chunk_index)
        )
        chunks = result.scalars().all()
        
        if not chunks:
            return ""
        
        # Combine all chunks
        texts = [chunk.text for chunk in chunks]
        return "\n\n".join(texts)
    
    @staticmethod
    async def _get_transcript_content(file_id: int, db: AsyncSession) -> str:
        """Get transcription text content."""
        result = await db.execute(
            select(Transcription)
            .where(Transcription.file_id == file_id)
            .where(Transcription.status == "completed")
            .order_by(Transcription.created_at.desc())
        )
        transcription = result.scalar_one_or_none()
        
        if not transcription:
            return ""
        
        return transcription.full_text
    
    @staticmethod
    async def _generate_summary(
        content: str,
        content_type: str,
        model: str,
        temperature: float,
        max_length: Optional[int] = None
    ) -> str:
        """
        Generate summary using LLM.
        
        Args:
            content: Content to summarize
            content_type: Type of content (for prompt)
            model: LLM model to use
            temperature: Temperature for generation
            max_length: Maximum summary length in words
        
        Returns:
            Generated summary
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Build prompt
            length_instruction = f" Keep the summary under {max_length} words." if max_length else ""
            
            prompt = f"""Please provide a comprehensive summary of the following {content_type}.{length_instruction}

Focus on:
- Main topics and themes
- Key points and important information
- Important details and conclusions

{content_type} content:
{content}

Summary:"""
            
            # Generate summary
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates clear, concise, and comprehensive summaries of documents and transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000  # Adjust based on needs
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    @staticmethod
    async def summarize_with_custom_prompt(
        file_id: int,
        custom_prompt: str,
        db: AsyncSession,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a summary with a custom prompt.
        
        Args:
            file_id: ID of the file to summarize
            custom_prompt: Custom prompt for summarization
            db: Database session
            model: LLM model to use
            temperature: Temperature for LLM
        
        Returns:
            Dictionary with summary and metadata
        """
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for summarization")
        
        # Get file metadata
        file_metadata = await FileService.get_file_by_id(file_id, db)
        if not file_metadata:
            raise ValueError(f"File {file_id} not found")
        
        # Get content
        if file_metadata.file_type == FileType.PDF:
            content = await SummarizationService._get_pdf_content(file_id, db)
            content_type = "PDF document"
        elif file_metadata.file_type in [FileType.AUDIO, FileType.VIDEO]:
            content = await SummarizationService._get_transcript_content(file_id, db)
            content_type = f"{file_metadata.file_type.value} transcript"
        else:
            raise ValueError(f"File type {file_metadata.file_type} is not supported for summarization.")
        
        if not content or not content.strip():
            raise ValueError(f"No content found for {content_type}.")
        
        # Generate summary with custom prompt
        model = model or settings.llm_model
        temperature = temperature if temperature is not None else settings.llm_temperature
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Build prompt with custom instruction
            prompt = f"""{custom_prompt}

{content_type} content:
{content}

Response:"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that follows instructions to analyze and summarize content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=2000
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {
                "file_id": file_id,
                "file_name": file_metadata.original_filename,
                "file_type": file_metadata.file_type.value,
                "content_type": content_type,
                "summary": summary,
                "model": model,
                "content_length": len(content),
                "summary_length": len(summary),
                "custom_prompt": custom_prompt
            }
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating custom summary: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")

