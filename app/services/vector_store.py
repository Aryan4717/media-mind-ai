"""FAISS vector store service for semantic search."""

import os
import logging
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

from app.config.settings import get_settings
from app.models.embedding import ChunkEmbedding
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """FAISS-based vector store for semantic search."""
    
    def __init__(self):
        self.index = None
        self.dimension = None
        self.chunk_id_map = {}  # Maps FAISS index position to chunk_id
        self.index_path = Path(settings.faiss_index_path)
        self._ensure_index_dir()
    
    def _ensure_index_dir(self):
        """Ensure index directory exists."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def build_index(self, db: AsyncSession):
        """
        Build or rebuild FAISS index from all embeddings in database.
        
        Args:
            db: Database session
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")
        
        # Get all embeddings
        result = await db.execute(
            select(ChunkEmbedding).order_by(ChunkEmbedding.id)
        )
        embeddings = result.scalars().all()
        
        if not embeddings:
            logger.warning("No embeddings found in database")
            self.index = None
            return
        
        # Get dimension from first embedding
        first_embedding = embeddings[0]
        self.dimension = first_embedding.embedding_dimension
        
        # Build vectors array
        vectors = []
        self.chunk_id_map = {}
        
        for idx, embedding in enumerate(embeddings):
            vector = embedding.get_embedding_vector()
            vectors.append(vector)
            self.chunk_id_map[idx] = embedding.chunk_id
        
        # Convert to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Create FAISS index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to index
        self.index.add(vectors_array)
        
        logger.info(f"Built FAISS index with {len(vectors)} vectors of dimension {self.dimension}")
        
        # Save index
        self.save_index()
    
    async def add_embedding(
        self,
        chunk_id: int,
        embedding_vector: List[float],
        db: AsyncSession
    ):
        """
        Add a single embedding to the index.
        
        Args:
            chunk_id: ID of the chunk
            embedding_vector: Embedding vector
            db: Database session
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")
        
        # Initialize index if needed
        if self.index is None:
            self.dimension = len(embedding_vector)
            self.index = faiss.IndexFlatL2(self.dimension)
            self.chunk_id_map = {}
        elif self.dimension != len(embedding_vector):
            raise ValueError(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding_vector)}")
        
        # Add to index
        vector_array = np.array([embedding_vector], dtype=np.float32)
        index_position = self.index.ntotal
        self.index.add(vector_array)
        self.chunk_id_map[index_position] = chunk_id
        
        logger.info(f"Added embedding for chunk {chunk_id} to FAISS index")
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None
    ) -> List[Tuple[int, float]]:
        """
        Search for similar chunks using query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return (defaults to settings)
        
        Returns:
            List of tuples (chunk_id, distance)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")
        
        if self.index is None or self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        top_k = top_k or settings.search_top_k
        
        # Convert query to numpy array
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        # Map indices to chunk IDs
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx in self.chunk_id_map:
                chunk_id = self.chunk_id_map[idx]
                results.append((chunk_id, float(distance)))
        
        return results
    
    async def search_by_text(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        model: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        """
        Search using query text (generates embedding first).
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            model: Embedding model to use
        
        Returns:
            List of tuples (chunk_id, distance)
        """
        # Generate query embedding
        query_embedding = await EmbeddingService.generate_embedding(query_text, model)
        
        # Search
        return await self.search(query_embedding, top_k)
    
    def save_index(self):
        """Save FAISS index to disk."""
        if self.index is None:
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save chunk ID mapping
            mapping_path = self.index_path.with_suffix('.json')
            with open(mapping_path, 'w') as f:
                json.dump(self.chunk_id_map, f)
            
            logger.info(f"Saved FAISS index to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
    
    def load_index(self):
        """Load FAISS index from disk."""
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not installed. Install with: pip install faiss-cpu")
        
        if not self.index_path.exists():
            logger.info("No existing FAISS index found")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            self.dimension = self.index.d
        
            # Load chunk ID mapping
            mapping_path = self.index_path.with_suffix('.json')
            if mapping_path.exists():
                with open(mapping_path, 'r') as f:
                    self.chunk_id_map = json.load(f)
                    # Convert keys to int
                    self.chunk_id_map = {int(k): int(v) for k, v in self.chunk_id_map.items()}
            
            logger.info(f"Loaded FAISS index from {self.index_path} with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            return False


# Global vector store instance
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        # Try to load existing index
        _vector_store.load_index()
    return _vector_store

