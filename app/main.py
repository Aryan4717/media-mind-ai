"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config.settings import get_settings
from app.config.database import init_db
from app.routes import health, files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Media Mind AI Backend...")
    logger.info(f"Environment: {settings.environment}")
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Media Mind AI Backend...")


# Create FastAPI application
app = FastAPI(
    title="Media Mind AI API",
    description="AI-powered document and multimedia Q&A system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Media Mind AI API",
        "version": "1.0.0",
        "status": "running"
    }

