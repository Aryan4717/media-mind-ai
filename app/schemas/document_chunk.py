"""Document chunk schemas."""

from pydantic import ConfigDict, BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class DocumentChunkResponse(BaseModel):
    """Response schema for a document chunk."""
    
    id: int
    file_id: int
    chunk_index: int
    text: str
    char_count: int
    token_count: Optional[int] = None
    page_number: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    chunk_metadata: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "file_id": 5,
                "chunk_index": 0,
                "text": "This is a chunk of text extracted from a PDF document...",
                "char_count": 500,
                "token_count": 125,
                "page_number": 1,
                "start_char": 0,
                "end_char": 500,
                "chunk_metadata": None,
                "created_at": "2024-01-01T12:00:00"
            }
        }
    )


class DocumentChunkListResponse(BaseModel):
    """Response schema for a list of document chunks."""
    
    chunks: List[DocumentChunkResponse]
    total: int
    file_id: int


class ProcessPDFRequest(BaseModel):
    """Request schema for PDF processing."""
    
    chunk_size: Optional[int] = Field(None, description="Characters per chunk (defaults to settings)")
    chunk_overlap: Optional[int] = Field(None, description="Character overlap between chunks (defaults to settings)")
    strategy: Optional[str] = Field(None, description="Chunking strategy: 'fixed', 'sentence', or 'paragraph'")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "strategy": "sentence"
            }
        }
    )


class ProcessPDFResponse(BaseModel):
    """Response schema for PDF processing."""
    
    file_id: int
    chunks_created: int
    total_characters: int
    total_tokens: Optional[int] = None
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": 5,
                "chunks_created": 15,
                "total_characters": 15000,
                "total_tokens": 3750,
                "message": "PDF processed successfully"
            }
        }
    )
