# Media Mind AI - Backend API

A production-ready FastAPI backend for an AI-powered document and multimedia Q&A system.

## Features

- 🚀 FastAPI with async support
- 📁 Modular architecture (routes, services, models, schemas, config)
- 🔐 Environment variable configuration
- 🏥 Health check endpoints (health, readiness, liveness)
- 📤 File upload system (PDF, audio, video) with metadata storage
- 💾 SQLite database with SQLAlchemy async ORM
- 📂 Structured file storage with organized folders
- 🌐 CORS middleware support
- 📝 Auto-generated API documentation
- 🔒 Production-ready settings

## Project Structure

```
media-mind-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py      # Environment configuration
│   │   └── database.py      # Database configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── files.py         # File upload endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── file_service.py  # File storage service
│   ├── models/
│   │   ├── __init__.py
│   │   └── file.py          # File metadata model
│   └── schemas/
│       ├── __init__.py
│       ├── health.py        # Health check schemas
│       └── file.py          # File upload schemas
├── uploads/                 # File storage directory (created automatically)
│   ├── pdfs/
│   ├── audio/
│   ├── video/
│   ├── images/
│   ├── documents/
│   └── other/
├── media_mind.db            # SQLite database (created automatically)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file with your configuration values.

### 4. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Checks

- `GET /api/v1/health` - General health check
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### File Upload & Management

- `POST /api/v1/files/upload` - Upload a single file (PDF, audio, video)
- `POST /api/v1/files/upload/multiple` - Upload multiple files at once
- `GET /api/v1/files/list` - List all files with pagination
  - Query params: `file_type` (optional), `page`, `page_size`
- `GET /api/v1/files/{file_id}` - Get file metadata by ID
- `GET /api/v1/files/{file_id}/download` - Download a file by ID
- `DELETE /api/v1/files/{file_id}` - Delete a file and its metadata

### Documentation

- `GET /docs` - Swagger UI documentation (disabled in production)
- `GET /redoc` - ReDoc documentation (disabled in production)

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `ENVIRONMENT`: Set to `production` to disable docs and enable production settings
- `CORS_ORIGINS`: List of allowed CORS origins
- `SECRET_KEY`: Secret key for security (change in production)

## Development

The application uses:
- **FastAPI** for the web framework
- **SQLAlchemy** with async support for database operations
- **SQLite** (default) or PostgreSQL for data storage
- **Pydantic Settings** for configuration management
- **Uvicorn** as the ASGI server

## File Storage

Files are stored in the `uploads/` directory with the following structure:
- `uploads/pdfs/` - PDF documents
- `uploads/audio/` - Audio files (mp3, wav, etc.)
- `uploads/video/` - Video files (mp4, avi, etc.)
- `uploads/images/` - Image files
- `uploads/documents/` - Other document types
- `uploads/other/` - Unrecognized file types

All file metadata (filename, type, size, upload time) is stored in the database.

## Database

The application uses SQLite by default (stored in `media_mind.db`). To use PostgreSQL, set the `DATABASE_URL` environment variable:

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

The database is automatically initialized on application startup.

## Next Steps

1. Add AI/ML integration for document processing
2. Implement Q&A endpoints
3. Add user authentication
4. Add file processing pipelines
5. Implement search functionality

## License

MIT

