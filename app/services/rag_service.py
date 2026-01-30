"""RAG (Retrieval-Augmented Generation) service for Q&A."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.services.semantic_search_service import SemanticSearchService
from app.services.timestamp_service import TimestampService
from app.models.file import FileType

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGService:
    """Service for RAG-based Q&A using retrieved document chunks."""
    
    @staticmethod
    def _build_context_from_chunks(chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks.
        
        Args:
            chunks: List of chunk dictionaries from search results
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for idx, chunk in enumerate(chunks, 1):
            chunk_text = chunk.get("text", "").strip()
            if chunk_text:
                # Add chunk with metadata
                page_info = f" (Page {chunk.get('page_number')})" if chunk.get("page_number") else ""
                context_parts.append(f"[Chunk {idx}{page_info}]\n{chunk_text}\n")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """
        Build RAG prompt with question and context.
        
        Args:
            question: User's question
            context: Retrieved context from documents
        
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from uploaded documents. 

IMPORTANT INSTRUCTIONS:
- Answer the question using ONLY the information provided in the context below
- If the context does not contain enough information to answer the question, say "I cannot answer this question based on the provided documents."
- Do not use any external knowledge or information not present in the context
- Be concise and accurate
- Cite which chunk(s) you used if relevant

Context from documents:
{context}

Question: {question}

Answer:"""
        return prompt
    
    @staticmethod
    async def answer_question(
        question: str,
        db: AsyncSession,
        top_k: Optional[int] = None,
        file_id: Optional[int] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG (Retrieval-Augmented Generation).
        
        Args:
            question: User's question
            db: Database session
            top_k: Number of chunks to retrieve (defaults to settings)
            file_id: Optional file ID to filter search
            model: LLM model to use (defaults to settings)
            temperature: Temperature for LLM (defaults to settings)
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for Q&A")
        
        # Retrieve relevant chunks using semantic search
        top_k = top_k or settings.rag_context_chunks
        search_results = await SemanticSearchService.search(
            query_text=question,
            db=db,
            top_k=top_k,
            file_id=file_id
        )
        
        if not search_results:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents to answer your question.",
                "sources": [],
                "confidence": 0.0,
                "chunks_used": 0
            }
        
        # Build context from retrieved chunks
        context = RAGService._build_context_from_chunks(search_results)
        
        # Build prompt
        prompt = RAGService._build_prompt(question, context)
        
        # Generate answer using LLM
        model = model or settings.llm_model
        temperature = temperature if temperature is not None else settings.llm_temperature
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Generate response
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based only on the provided context from documents. If the context doesn't contain enough information, say so."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Prepare sources
            sources = []
            all_timestamps = []
            
            for result in search_results:
                source_info = {
                    "chunk_id": result["chunk_id"],
                    "file_id": result["file_id"],
                    "chunk_index": result["chunk_index"],
                    "text_preview": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                    "score": result["score"],
                    "page_number": result.get("page_number"),
                    "timestamps": None
                }
                
                # Extract timestamps for audio/video files
                try:
                    # Check if this is an audio/video file
                    from app.services.file_service import FileService
                    file_meta = await FileService.get_file_by_id(result["file_id"], db)
                    
                    if file_meta and file_meta.file_type in [FileType.AUDIO, FileType.VIDEO]:
                        # Extract timestamps for this chunk's text
                        chunk_timestamps = await TimestampService.extract_timestamps_for_text(
                            result["file_id"],
                            result["text"],
                            db
                        )
                        
                        # Format timestamps
                        formatted_timestamps = [
                            {
                                "start": ts["start"],
                                "end": ts["end"],
                                "text": ts["text"],
                                "duration": ts["duration"],
                                "formatted_start": TimestampService.format_timestamp(ts["start"]),
                                "formatted_end": TimestampService.format_timestamp(ts["end"])
                            }
                            for ts in chunk_timestamps
                        ]
                        
                        source_info["timestamps"] = formatted_timestamps
                        all_timestamps.extend(formatted_timestamps)
                except Exception as e:
                    logger.warning(f"Could not extract timestamps for file {result['file_id']}: {str(e)}")
                
                sources.append(source_info)
            
            # Calculate average confidence from search scores
            avg_confidence = sum(r["score"] for r in search_results) / len(search_results) if search_results else 0.0
            
            # Remove duplicate timestamps (same start/end)
            unique_timestamps = []
            seen = set()
            for ts in all_timestamps:
                key = (ts["start"], ts["end"])
                if key not in seen:
                    seen.add(key)
                    unique_timestamps.append(ts)
            
            # Sort timestamps by start time
            unique_timestamps.sort(key=lambda x: x["start"])
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": round(avg_confidence, 3),
                "chunks_used": len(search_results),
                "model": model,
                "timestamps": unique_timestamps if unique_timestamps else None
            }
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    @staticmethod
    async def answer_question_with_streaming(
        question: str,
        db: AsyncSession,
        top_k: Optional[int] = None,
        file_id: Optional[int] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Answer a question using RAG with streaming response.
        
        Yields:
            Generator of answer chunks
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for Q&A")
        
        # Retrieve relevant chunks
        top_k = top_k or settings.rag_context_chunks
        search_results = await SemanticSearchService.search(
            query_text=question,
            db=db,
            top_k=top_k,
            file_id=file_id
        )
        
        if not search_results:
            yield {
                "type": "error",
                "content": "I couldn't find any relevant information in the uploaded documents to answer your question."
            }
            return
        
        # Build context and prompt
        context = RAGService._build_context_from_chunks(search_results)
        prompt = RAGService._build_prompt(question, context)
        
        model = model or settings.llm_model
        temperature = temperature if temperature is not None else settings.llm_temperature
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Stream response
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based only on the provided context from documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=1000,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {
                        "type": "content",
                        "content": chunk.choices[0].delta.content
                    }
            
            # Send sources at the end
            sources = [
                {
                    "chunk_id": result["chunk_id"],
                    "file_id": result["file_id"],
                    "chunk_index": result["chunk_index"],
                    "text_preview": result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"],
                    "score": result["score"],
                    "page_number": result.get("page_number")
                }
                for result in search_results
            ]
            
            yield {
                "type": "sources",
                "sources": sources
            }
            
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating streaming answer: {str(e)}")
            yield {
                "type": "error",
                "content": f"Failed to generate answer: {str(e)}"
            }

