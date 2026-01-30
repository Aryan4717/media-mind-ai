"""Document chunk database model for PDF text extraction."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Integer as SQLInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.config.database import Base


class DocumentChunk(Base):
    """Document chunk model for storing extracted and chunked text from PDFs."""
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=False, index=True)
    chunk_index = Column(SQLInteger, nullable=False)  # Order of chunk in document
    text = Column(Text, nullable=False)  # Chunk text content
    char_count = Column(SQLInteger, nullable=False)  # Character count
    token_count = Column(SQLInteger, nullable=True)  # Token count (for embeddings)
    page_number = Column(SQLInteger, nullable=True)  # Page number in PDF (if applicable)
    start_char = Column(SQLInteger, nullable=True)  # Start character position in original text
    end_char = Column(SQLInteger, nullable=True)  # End character position in original text
    chunk_metadata = Column(Text, nullable=True)  # JSON metadata (e.g., section, heading)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to file
    file = relationship("FileMetadata", backref="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, file_id={self.file_id}, chunk_index={self.chunk_index})>"

