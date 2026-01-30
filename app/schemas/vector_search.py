"""Vector search schemas."""

from pydantic import ConfigDict, BaseModel, Field
from typing import List, Optional, Dict, Any


class SearchRequest(BaseModel):
    """Request schema for semantic search."""
    
    query: str = Field(..., description="Search query text")
    top_k: Optional[int] = Field(None, description="Number of results to return")
    file_id: Optional[int] = Field(None, description="Optional file ID to filter results")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is machine learning?",
                "top_k": 5,
                "file_id": None
            }
        }
    )


class SearchResult(BaseModel):
    """Schema for a single search result."""
    
    chunk_id: int
    file_id: int
    chunk_index: int
    text: str
    score: float = Field(..., description="Similarity score (0-1, higher is better)")
    distance: float = Field(..., description="L2 distance (lower is better)")
    char_count: int
    page_number: Optional[int] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": 1,
                "file_id": 5,
                "chunk_index": 0,
                "text": "Machine learning is a subset of artificial intelligence...",
                "score": 0.95,
                "distance": 0.05,
                "char_count": 500,
                "page_number": 1
            }
        }
    )


class SearchResponse(BaseModel):
    """Response schema for semantic search."""
    
    query: str
    results: List[SearchResult]
    total_results: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What is machine learning?",
                "results": [
                    {
                        "chunk_id": 1,
                        "file_id": 5,
                        "chunk_index": 0,
                        "text": "Machine learning is...",
                        "score": 0.95,
                        "distance": 0.05,
                        "char_count": 500,
                        "page_number": 1
                    }
                ],
                "total_results": 1
            }
        }
    )


class GenerateEmbeddingsRequest(BaseModel):
    """Request schema for generating embeddings."""
    
    chunk_ids: Optional[List[int]] = Field(None, description="Specific chunk IDs (if not provided, all chunks for file)")
    model: Optional[str] = Field(None, description="Embedding model to use")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_ids": [1, 2, 3],
                "model": "text-embedding-ada-002"
            }
        }
    )


class GenerateEmbeddingsResponse(BaseModel):
    """Response schema for embedding generation."""
    
    embeddings_created: int
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embeddings_created": 10,
                "message": "Embeddings generated successfully"
            }
        }
    )
