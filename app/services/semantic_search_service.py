"""Semantic search service combining embeddings and vector search."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.document_chunk import DocumentChunk
from app.models.embedding import ChunkEmbedding
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
settings = get_settings()


class SemanticSearchService:
    """Service for semantic search over document chunks."""
    
    @staticmethod
    async def generate_embeddings_for_chunks(
        chunk_ids: List[int],
        db: AsyncSession,
        model: Optional[str] = None
    ) -> Dict[int, ChunkEmbedding]:
        """
        Generate and store embeddings for chunks.
        
        Args:
            chunk_ids: List of chunk IDs to process
            db: Database session
            model: Embedding model to use
        
        Returns:
            Dictionary mapping chunk_id to ChunkEmbedding
        """
        # Get chunks
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
        )
        chunks = result.scalars().all()
        
        if not chunks:
            return {}
        
        # Extract texts
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = await EmbeddingService.generate_embeddings_batch(texts, model)
        
        # Store embeddings
        embedding_objects = {}
        vector_store = get_vector_store()
        
        for chunk, embedding_vector in zip(chunks, embeddings):
            # Check if embedding already exists
            existing = await db.execute(
                select(ChunkEmbedding).where(ChunkEmbedding.chunk_id == chunk.id)
            )
            existing_embedding = existing.scalar_one_or_none()
            
            if existing_embedding:
                # Update existing
                existing_embedding.set_embedding_vector(embedding_vector)
                existing_embedding.embedding_model = model or settings.embedding_model
                embedding_objects[chunk.id] = existing_embedding
            else:
                # Create new
                chunk_embedding = ChunkEmbedding(
                    chunk_id=chunk.id,
                    embedding_model=model or settings.embedding_model
                )
                chunk_embedding.set_embedding_vector(embedding_vector)
                db.add(chunk_embedding)
                embedding_objects[chunk.id] = chunk_embedding
            
            # Add to vector store
            await vector_store.add_embedding(chunk.id, embedding_vector, db)
        
        await db.commit()
        
        # Refresh embeddings to get IDs
        for embedding in embedding_objects.values():
            await db.refresh(embedding)
        
        # Save vector store
        vector_store.save_index()
        
        logger.info(f"Generated embeddings for {len(embedding_objects)} chunks")
        return embedding_objects
    
    @staticmethod
    async def generate_embeddings_for_file(
        file_id: int,
        db: AsyncSession,
        model: Optional[str] = None
    ) -> int:
        """
        Generate embeddings for all chunks of a file.
        
        Args:
            file_id: File ID
            db: Database session
            model: Embedding model to use
        
        Returns:
            Number of embeddings created
        """
        # Get all chunks for file
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.file_id == file_id)
        )
        chunks = result.scalars().all()
        
        if not chunks:
            raise ValueError(f"No chunks found for file {file_id}")
        
        chunk_ids = [chunk.id for chunk in chunks]
        embeddings = await SemanticSearchService.generate_embeddings_for_chunks(
            chunk_ids, db, model
        )
        
        return len(embeddings)
    
    @staticmethod
    async def search(
        query_text: str,
        db: AsyncSession,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        file_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search over document chunks.
        
        Args:
            query_text: Search query
            db: Database session
            top_k: Number of results to return
            model: Embedding model to use
            file_id: Optional file ID to filter results
        
        Returns:
            List of search results with chunks and scores
        """
        vector_store = get_vector_store()
        
        # Rebuild index if needed
        if vector_store.index is None:
            await vector_store.build_index(db)
        
        # Search
        results = await vector_store.search_by_text(query_text, top_k, model)
        
        if not results:
            return []
        
        # Get chunks
        chunk_ids = [chunk_id for chunk_id, _ in results]
        
        query = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
        if file_id:
            query = query.where(DocumentChunk.file_id == file_id)
        
        result = await db.execute(query)
        chunks = {chunk.id: chunk for chunk in result.scalars().all()}
        
        # Build results
        search_results = []
        for chunk_id, distance in results:
            if chunk_id in chunks:
                chunk = chunks[chunk_id]
                search_results.append({
                    "chunk_id": chunk.id,
                    "file_id": chunk.file_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "score": 1.0 / (1.0 + distance),  # Convert distance to similarity score
                    "distance": distance,
                    "char_count": chunk.char_count,
                    "page_number": chunk.page_number
                })
        
        # Sort by score (highest first)
        search_results.sort(key=lambda x: x["score"], reverse=True)
        
        return search_results

