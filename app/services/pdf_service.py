"""PDF processing service for text extraction and chunking."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.config.settings import get_settings
from app.models.document_chunk import DocumentChunk
from app.models.file import FileMetadata, FileType

logger = logging.getLogger(__name__)
settings = get_settings()


class PDFService:
    """Service for processing PDF files: extracting text and creating chunks."""
    
    @staticmethod
    async def process_pdf(
        file_metadata: FileMetadata,
        db: AsyncSession,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: Optional[str] = None
    ) -> List[DocumentChunk]:
        """
        Extract text from PDF and split into chunks.
        
        Args:
            file_metadata: The PDF file metadata
            db: Database session
            chunk_size: Characters per chunk (defaults to settings)
            chunk_overlap: Character overlap between chunks (defaults to settings)
            strategy: Chunking strategy (defaults to settings)
        
        Returns:
            List of DocumentChunk objects
        """
        # Check if file is PDF
        if file_metadata.file_type != FileType.PDF:
            raise ValueError(f"File type {file_metadata.file_type} is not supported. Only PDF files are supported.")
        
        # Use settings defaults if not provided
        chunk_size = chunk_size or settings.chunk_size
        chunk_overlap = chunk_overlap or settings.chunk_overlap
        strategy = strategy or settings.chunking_strategy
        
        file_path = Path(file_metadata.file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Delete existing chunks for this file
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.file_id == file_metadata.id)
        )
        await db.commit()
        
        # Extract text from PDF
        try:
            extracted_text = await PDFService._extract_text_from_pdf(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_metadata.id}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
        
        if not extracted_text or not extracted_text.strip():
            raise ValueError("No text could be extracted from the PDF")
        
        # Split text into chunks
        chunks_data = PDFService._split_text_into_chunks(
            extracted_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy
        )
        
        # Create chunk records
        chunk_objects = []
        for idx, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                file_id=file_metadata.id,
                chunk_index=idx,
                text=chunk_data["text"],
                char_count=len(chunk_data["text"]),
                token_count=chunk_data.get("token_count"),
                page_number=chunk_data.get("page_number"),
                start_char=chunk_data.get("start_char"),
                end_char=chunk_data.get("end_char"),
                chunk_metadata=chunk_data.get("metadata")
            )
            db.add(chunk)
            chunk_objects.append(chunk)
        
        await db.commit()
        
        # Refresh all chunks to get IDs
        for chunk in chunk_objects:
            await db.refresh(chunk)
        
        logger.info(f"Successfully processed PDF {file_metadata.id} into {len(chunk_objects)} chunks")
        return chunk_objects
    
    @staticmethod
    async def _extract_text_from_pdf(file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            import pdfplumber
            
            full_text = []
            page_texts = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        full_text.append(text)
                        page_texts.append({
                            "page": page_num,
                            "text": text
                        })
            
            return "\n\n".join(full_text)
        except ImportError:
            raise ImportError("pdfplumber not installed. Install with: pip install pdfplumber")
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def _split_text_into_chunks(
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        strategy: str = "fixed"
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks based on strategy.
        
        Args:
            text: Text to split
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            strategy: "fixed", "sentence", or "paragraph"
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if strategy == "sentence":
            return PDFService._chunk_by_sentence(text, chunk_size, chunk_overlap)
        elif strategy == "paragraph":
            return PDFService._chunk_by_paragraph(text, chunk_size, chunk_overlap)
        else:  # fixed
            return PDFService._chunk_fixed_size(text, chunk_size, chunk_overlap)
    
    @staticmethod
    def _chunk_fixed_size(
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Split text into fixed-size chunks."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            # Try to end at a word boundary
            if end < len(text):
                # Look for the last space before the end
                last_space = chunk_text.rfind(' ')
                if last_space > chunk_size * 0.7:  # Only if we're not too far from target
                    chunk_text = chunk_text[:last_space]
                    end = start + last_space
            
            chunks.append({
                "text": chunk_text.strip(),
                "start_char": start,
                "end_char": start + len(chunk_text),
                "token_count": PDFService._estimate_tokens(chunk_text)
            })
            
            start = end - chunk_overlap
            chunk_index += 1
        
        return chunks
    
    @staticmethod
    def _chunk_by_sentence(
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Split text into chunks at sentence boundaries."""
        import re
        
        # Split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start_char": start_char,
                    "end_char": start_char + len(chunk_text),
                    "token_count": PDFService._estimate_tokens(chunk_text)
                })
                
                # Start new chunk with overlap
                overlap_text = chunk_text[-chunk_overlap:] if chunk_overlap > 0 else ""
                current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                current_size = len(' '.join(current_chunk))
                start_char = chunks[-1]["end_char"] - len(overlap_text) if overlap_text else chunks[-1]["end_char"]
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1  # +1 for space
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start_char": start_char,
                "end_char": start_char + len(chunk_text),
                "token_count": PDFService._estimate_tokens(chunk_text)
            })
        
        return chunks
    
    @staticmethod
    def _chunk_by_paragraph(
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        start_char = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start_char": start_char,
                    "end_char": start_char + len(chunk_text),
                    "token_count": PDFService._estimate_tokens(chunk_text)
                })
                
                # Start new chunk
                current_chunk = [para]
                current_size = para_size
                start_char = chunks[-1]["end_char"]
                chunk_index += 1
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for \n\n
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start_char": start_char,
                "end_char": start_char + len(chunk_text),
                "token_count": PDFService._estimate_tokens(chunk_text)
            })
        
        return chunks
    
    @staticmethod
    def _estimate_tokens(text: str) -> Optional[int]:
        """Estimate token count for text (for embedding purposes)."""
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")  # Used by GPT-4
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
        except Exception:
            return None
    
    @staticmethod
    async def get_chunks_by_file_id(
        file_id: int,
        db: AsyncSession,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[DocumentChunk]:
        """Get all chunks for a file."""
        query = select(DocumentChunk).where(
            DocumentChunk.file_id == file_id
        ).order_by(DocumentChunk.chunk_index)
        
        if limit:
            query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_chunk_by_id(
        chunk_id: int,
        db: AsyncSession
    ) -> Optional[DocumentChunk]:
        """Get a chunk by ID."""
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_chunks_by_file_id(
        file_id: int,
        db: AsyncSession
    ) -> int:
        """Delete all chunks for a file."""
        result = await db.execute(
            delete(DocumentChunk).where(DocumentChunk.file_id == file_id)
        )
        await db.commit()
        return result.rowcount

