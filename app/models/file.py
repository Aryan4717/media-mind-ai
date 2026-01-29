"""File metadata database model."""

from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.config.database import Base


class FileType(str, enum.Enum):
    """File type enumeration."""
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"
    OTHER = "other"


class FileMetadata(Base):
    """File metadata database model."""
    
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False, index=True)
    file_path = Column(String, nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_size_mb = Column(Float, nullable=False)  # Size in MB
    mime_type = Column(String, nullable=True)
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<FileMetadata(id={self.id}, filename='{self.filename}', type='{self.file_type}')>"

