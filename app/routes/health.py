"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns the current status of the API and system information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint.
    
    Used by orchestration systems to determine if the service is ready to accept traffic.
    """
    # Add readiness checks here (e.g., database connectivity, external services)
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Used by orchestration systems to determine if the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

