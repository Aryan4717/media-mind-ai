"""Run the FastAPI application locally on port 8000 (Docker backend uses 8001)."""

import uvicorn
from app.config.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    # Run on port 8000 for local development (Docker backend uses 8001)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=8000,  # Local development on default port
        reload=settings.debug,
        log_level="info"
    )

