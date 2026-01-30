"""Q&A request and response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QuestionRequest(BaseModel):
    """Request schema for asking a question."""
    
    question: str = Field(..., description="The question to ask")
    file_id: Optional[int] = Field(None, description="Optional file ID to limit search to specific file")
    top_k: Optional[int] = Field(None, description="Number of chunks to retrieve (defaults to settings)")
    model: Optional[str] = Field(None, description="LLM model to use (defaults to settings)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for LLM generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is machine learning?",
                "file_id": None,
                "top_k": 5,
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        }


class TimestampInfo(BaseModel):
    """Schema for timestamp information."""
    
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Segment text")
    duration: float = Field(..., description="Duration in seconds")
    formatted_start: str = Field(..., description="Formatted start time (HH:MM:SS)")
    formatted_end: str = Field(..., description="Formatted end time (HH:MM:SS)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "start": 10.5,
                "end": 25.3,
                "text": "This is the transcript segment...",
                "duration": 14.8,
                "formatted_start": "00:10.500",
                "formatted_end": "00:25.300"
            }
        }


class SourceInfo(BaseModel):
    """Schema for source chunk information."""
    
    chunk_id: int
    file_id: int
    chunk_index: int
    text_preview: str
    score: float
    page_number: Optional[int] = None
    timestamps: Optional[List[TimestampInfo]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": 1,
                "file_id": 5,
                "chunk_index": 0,
                "text_preview": "Machine learning is a subset of artificial intelligence...",
                "score": 0.95,
                "page_number": 1
            }
        }


class AnswerResponse(BaseModel):
    """Response schema for Q&A."""
    
    answer: str
    sources: List[SourceInfo]
    confidence: float = Field(..., description="Average confidence score (0-1)")
    chunks_used: int
    model: str
    timestamps: Optional[List[TimestampInfo]] = Field(None, description="Timestamps for audio/video files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
                "sources": [
                    {
                        "chunk_id": 1,
                        "file_id": 5,
                        "chunk_index": 0,
                        "text_preview": "Machine learning is...",
                        "score": 0.95,
                        "page_number": 1
                    }
                ],
                "confidence": 0.92,
                "chunks_used": 3,
                "model": "gpt-4o-mini"
            }
        }

