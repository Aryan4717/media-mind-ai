# Media Mind AI - Backend API

A production-ready FastAPI backend for an AI-powered document and multimedia Q&A system.

## Features

- 🚀 FastAPI with async support
- 📁 Modular architecture (routes, services, models, schemas, config)
- 🔐 Environment variable configuration
- 🏥 Health check endpoints (health, readiness, liveness)
- 📤 File upload system (PDF, audio, video) with metadata storage
- 🎙️ Audio/Video transcription using OpenAI Whisper (API or local)
- 📝 Timestamped transcription segments with full text
- 📄 PDF text extraction and intelligent chunking
- 🔍 Document chunks ready for embedding and search
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

### Transcription Service

- `POST /api/v1/files/{file_id}/transcribe` - Transcribe an audio/video file (synchronous)
  - Body: `{"language": "en", "task": "transcribe"}` (optional)
- `POST /api/v1/files/{file_id}/transcribe/async` - Start transcription in background (asynchronous)
- `GET /api/v1/files/{file_id}/transcription` - Get transcription for a file
- `GET /api/v1/transcriptions/{transcription_id}` - Get transcription by ID
- `DELETE /api/v1/transcriptions/{transcription_id}` - Delete a transcription

### Document Processing (PDF)

- `POST /api/v1/files/{file_id}/process` - Extract text from PDF and split into chunks
  - Body: `{"chunk_size": 1000, "chunk_overlap": 200, "strategy": "sentence"}` (optional)
- `GET /api/v1/files/{file_id}/chunks` - Get all chunks for a PDF file
  - Query params: `limit`, `offset` (for pagination)
- `GET /api/v1/chunks/{chunk_id}` - Get a specific chunk by ID
- `DELETE /api/v1/files/{file_id}/chunks` - Delete all chunks for a file

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
- **OpenAI Whisper** for audio/video transcription (local or API)
- **Pydantic Settings** for configuration management
- **Uvicorn** as the ASGI server

## Transcription Service

The transcription service supports both OpenAI Whisper API and local Whisper models:

### Using OpenAI Whisper API
1. Set `OPENAI_API_KEY` in your `.env` file
2. Set `USE_OPENAI_WHISPER_API=true`
3. Upload audio/video files and transcribe them

### Using Local Whisper
1. Install dependencies: `pip install openai-whisper ffmpeg-python`
2. Install FFmpeg (required for audio processing):
   - macOS: `brew install ffmpeg`
   - Ubuntu: `sudo apt-get install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
3. Set `USE_OPENAI_WHISPER_API=false` (default)
4. Choose Whisper model: `WHISPER_MODEL=base` (options: tiny, base, small, medium, large)

### Transcription Features
- **Full text extraction** from audio/video files
- **Timestamped segments** with start/end times
- **Language detection** (auto-detect or specify)
- **Translation support** (translate to English)
- **Linked to files** in database for easy retrieval

## PDF Processing Service

The PDF processing service extracts text from PDFs and splits it into chunks for embedding and search:

### Features
- **Text extraction** from PDF files using pdfplumber
- **Intelligent chunking** with multiple strategies:
  - **Fixed size**: Split into fixed character chunks
  - **Sentence-based**: Split at sentence boundaries
  - **Paragraph-based**: Split at paragraph boundaries
- **Overlap support** to maintain context between chunks
- **Token counting** for embedding preparation
- **Metadata tracking** (page numbers, character positions)

### Chunking Strategies

1. **Fixed** (default): Splits text into fixed-size chunks with word boundary awareness
2. **Sentence**: Splits at sentence boundaries, maintaining semantic coherence
3. **Paragraph**: Splits at paragraph boundaries, preserving document structure

### Configuration

Set in `.env`:
- `CHUNK_SIZE`: Characters per chunk (default: 1000)
- `CHUNK_OVERLAP`: Character overlap between chunks (default: 200)
- `CHUNKING_STRATEGY`: Strategy to use (default: "fixed")

### Usage Example

```bash
# 1. Upload a PDF file
POST /api/v1/files/upload

# 2. Process the PDF into chunks
POST /api/v1/files/{file_id}/process
{
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "strategy": "sentence"
}

# 3. Retrieve chunks for embedding/search
GET /api/v1/files/{file_id}/chunks
```

The chunks are stored in the database and ready for:
- **Embedding generation** (using OpenAI or other embedding models)
- **Vector search** (semantic search across documents)
- **RAG (Retrieval-Augmented Generation)** applications

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

