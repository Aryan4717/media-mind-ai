"""Health check response schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str
    timestamp: str
    service: str
    version: str
    environment: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00",
                "service": "Media Mind AI",
                "version": "1.0.0",
                "environment": "development"
            }
        }

