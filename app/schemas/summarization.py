"""Summarization request and response schemas."""

from pydantic import ConfigDict, BaseModel, Field
from typing import Optional


class SummarizeRequest(BaseModel):
    """Request schema for summarization."""
    
    model: Optional[str] = Field(None, description="LLM model to use (defaults to settings)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for LLM generation")
    max_length: Optional[int] = Field(None, ge=50, description="Maximum summary length in words")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_length": 500
            }
        }
    )


class CustomSummarizeRequest(BaseModel):
    """Request schema for custom prompt summarization."""
    
    custom_prompt: str = Field(..., description="Custom prompt for summarization")
    model: Optional[str] = Field(None, description="LLM model to use (defaults to settings)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for LLM generation")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "custom_prompt": "Summarize the key technical concepts and provide a bullet-point list of main topics.",
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        }
    )


class SummaryResponse(BaseModel):
    """Response schema for summarization."""
    
    file_id: int
    file_name: str
    file_type: str
    content_type: str
    summary: str
    model: str
    content_length: int
    summary_length: int
    custom_prompt: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_id": 1,
                "file_name": "document.pdf",
                "file_type": "pdf",
                "content_type": "PDF document",
                "summary": "This document discusses machine learning concepts...",
                "model": "gpt-4o-mini",
                "content_length": 10000,
                "summary_length": 500,
                "custom_prompt": None
            }
        }
    )
