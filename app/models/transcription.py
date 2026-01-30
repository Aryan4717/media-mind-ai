"""Transcription database model."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.config.database import Base


class Transcription(Base):
    """Transcription database model."""
    
    __tablename__ = "transcriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_metadata.id"), nullable=False, index=True)
    full_text = Column(Text, nullable=False)  # Complete transcription text
    language = Column(String, nullable=True)  # Detected language
    duration = Column(Float, nullable=True)  # Audio/video duration in seconds
    segments = Column(JSON, nullable=True)  # Timestamped segments with text
    status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # Error message if transcription failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship to file
    file = relationship("FileMetadata", backref="transcriptions")
    
    def __repr__(self):
        return f"<Transcription(id={self.id}, file_id={self.file_id}, status='{self.status}')>"

