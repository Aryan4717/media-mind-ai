"""Embedding model for storing vector embeddings."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
import json

from app.config.database import Base


class ChunkEmbedding(Base):
    """Model for storing vector embeddings of document chunks."""
    
    __tablename__ = "chunk_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False, unique=True, index=True)
    embedding_model = Column(String, nullable=False)  # e.g., "text-embedding-ada-002"
    embedding_vector = Column(Text, nullable=False)  # JSON array of floats
    embedding_dimension = Column(Integer, nullable=False)  # Dimension of the embedding vector
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to chunk
    chunk = relationship("DocumentChunk", backref="embedding")
    
    def get_embedding_vector(self) -> list[float]:
        """Parse and return embedding vector as list of floats."""
        return json.loads(self.embedding_vector)
    
    def set_embedding_vector(self, vector: list[float]):
        """Set embedding vector from list of floats."""
        self.embedding_vector = json.dumps(vector)
        self.embedding_dimension = len(vector)
    
    def __repr__(self):
        return f"<ChunkEmbedding(id={self.id}, chunk_id={self.chunk_id}, model='{self.embedding_model}')>"

