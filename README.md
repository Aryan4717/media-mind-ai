# Media Mind AI

A production-ready AI-powered document and multimedia Q&A system with FastAPI backend and React frontend.

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
- 🎯 Semantic search using OpenAI embeddings and FAISS
- 📊 Vector similarity search with ranking
- 💬 LLM-powered Q&A chatbot with RAG
- 🔍 Answers based only on uploaded document content
- 📝 Document and transcript summarization using LLM
- 🎯 Custom summarization prompts for different formats
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

### Backend Setup

1. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` file with your configuration values (especially `OPENAI_API_KEY` for Q&A and embeddings).

4. **Run the Backend**
   ```bash
   # Development mode with auto-reload
   python run.py
   # OR
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `VITE_API_URL=http://localhost:8000/api/v1`

4. **Run the Frontend**
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal).

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

### Vector Search (Semantic Search)

- `POST /api/v1/search` - Perform semantic search over document chunks
  - Body: `{"query": "search text", "top_k": 5, "file_id": null}` (optional)
- `POST /api/v1/files/{file_id}/embeddings` - Generate embeddings for all chunks of a file
  - Body: `{"model": "text-embedding-ada-002"}` (optional)
- `POST /api/v1/chunks/embeddings` - Generate embeddings for specific chunks
  - Body: `{"chunk_ids": [1, 2, 3], "model": "text-embedding-ada-002"}` (optional)
- `POST /api/v1/vector-store/rebuild` - Rebuild FAISS vector store index
- `GET /api/v1/vector-store/status` - Get vector store status

### Q&A Chatbot (RAG)

- `POST /api/v1/ask` - Ask a question and get an answer using RAG
  - Body: `{"question": "What is machine learning?", "file_id": null, "top_k": 5, "model": "gpt-4o-mini", "temperature": 0.7}` (optional)
- `POST /api/v1/ask/stream` - Ask a question with streaming response
  - Body: Same as `/ask` endpoint
- `POST /api/v1/files/{file_id}/ask` - Ask a question about a specific file
  - Body: `{"question": "What is this document about?", "top_k": 5}` (optional)

### Summarization

- `POST /api/v1/files/{file_id}/summarize` - Generate a summary of a PDF, audio transcript, or video transcript
  - Body: `{"model": "gpt-4o-mini", "temperature": 0.7, "max_length": 500}` (optional)
- `POST /api/v1/files/{file_id}/summarize/custom` - Generate a summary with a custom prompt
  - Body: `{"custom_prompt": "Summarize key points as bullet points", "model": "gpt-4o-mini", "temperature": 0.7}` (optional)

### Timestamp Extraction

- `POST /api/v1/files/{file_id}/timestamps` - Extract timestamps for text from audio/video transcript
  - Body: `{"text": "Text to find in transcript"}`
- Q&A responses automatically include timestamps for audio/video files

### Media Playback

- `GET /api/v1/files/{file_id}/playback` - Get media file URL and timestamp for playback
  - Query param: `timestamp` (optional, in seconds)
- `POST /api/v1/files/{file_id}/playback` - Get media playback info (POST method)
  - Body: `{"timestamp": 10.5}` (optional)
- `GET /api/v1/files/{file_id}/playback/from-timestamp/{start_time}` - Get playback info from specific timestamp
  - Path param: `start_time` (in seconds)

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

## Vector Search Service

The vector search service enables semantic search over document chunks using OpenAI embeddings and FAISS:

### Features
- **OpenAI Embeddings**: Uses OpenAI's embedding models (text-embedding-ada-002, text-embedding-3-small, etc.)
- **FAISS Vector Store**: Fast similarity search using Facebook's FAISS library
- **Semantic Search**: Find relevant chunks based on meaning, not just keywords
- **Batch Processing**: Efficient embedding generation for multiple chunks
- **Persistent Index**: FAISS index saved to disk for fast loading

### Setup

1. **Set OpenAI API Key**:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

2. **Install Dependencies**:
   ```bash
   pip install faiss-cpu numpy
   ```

3. **Process PDF and Generate Embeddings**:
   ```bash
   # 1. Upload and process PDF
   POST /api/v1/files/upload
   POST /api/v1/files/{file_id}/process
   
   # 2. Generate embeddings
   POST /api/v1/files/{file_id}/embeddings
   ```

4. **Perform Semantic Search**:
   ```bash
   POST /api/v1/search
   {
     "query": "What is machine learning?",
     "top_k": 5
   }
   ```

### Configuration

Set in `.env`:
- `EMBEDDING_MODEL`: OpenAI embedding model (default: "text-embedding-ada-002")
- `FAISS_INDEX_PATH`: Path to store FAISS index (default: "faiss_index")
- `SEARCH_TOP_K`: Number of results to return (default: 5)
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding generation (default: 100)

### Usage Example

```bash
# 1. Upload and process a PDF
POST /api/v1/files/upload
POST /api/v1/files/1/process

# 2. Generate embeddings for all chunks
POST /api/v1/files/1/embeddings

# 3. Search for relevant chunks
POST /api/v1/search
{
  "query": "explain neural networks",
  "top_k": 3
}

# Response includes chunks ranked by similarity with scores
```

### How It Works

1. **Text Extraction**: PDFs are processed into text chunks
2. **Embedding Generation**: Chunks are converted to vector embeddings using OpenAI
3. **Index Building**: Embeddings are stored in FAISS for fast similarity search
4. **Semantic Search**: Query text is embedded and compared against all chunks
5. **Ranking**: Results are ranked by similarity score (cosine similarity via L2 distance)

The system enables powerful semantic search capabilities for building RAG applications and intelligent document Q&A systems.

## Q&A Chatbot (RAG)

The Q&A chatbot uses Retrieval-Augmented Generation (RAG) to answer questions based only on uploaded document content:

### Features
- **RAG Architecture**: Combines semantic search with LLM generation
- **Context-Aware Answers**: Uses retrieved document chunks as context
- **Source Attribution**: Provides sources for each answer
- **Confidence Scoring**: Returns confidence scores based on search relevance
- **Streaming Support**: Optional streaming responses for real-time answers
- **File-Specific Q&A**: Ask questions about specific files

### How RAG Works

1. **Question Processing**: User asks a question
2. **Semantic Search**: System retrieves relevant document chunks using vector search
3. **Context Building**: Retrieved chunks are formatted as context
4. **LLM Generation**: LLM generates answer based only on the provided context
5. **Response**: Answer is returned with source citations and confidence score

### Setup

1. **Set OpenAI API Key** (required):
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

2. **Configure LLM Model** (optional):
   ```bash
   LLM_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo, etc.
   LLM_TEMPERATURE=0.7
   RAG_CONTEXT_CHUNKS=5
   ```

3. **Process Documents and Generate Embeddings**:
   ```bash
   # Upload and process PDF
   POST /api/v1/files/upload
   POST /api/v1/files/{file_id}/process
   
   # Generate embeddings
   POST /api/v1/files/{file_id}/embeddings
   ```

4. **Ask Questions**:
   ```bash
   POST /api/v1/ask
   {
     "question": "What is machine learning?",
     "file_id": null,  # or specific file ID
     "top_k": 5
   }
   ```

### Usage Example

```bash
# 1. Upload and process a PDF
POST /api/v1/files/upload
POST /api/v1/files/1/process

# 2. Generate embeddings
POST /api/v1/files/1/embeddings

# 3. Ask a question
POST /api/v1/ask
{
  "question": "Explain the main concepts discussed in this document",
  "top_k": 5
}

# Response includes:
# - Answer based on document content
# - Source chunks with scores
# - Confidence score
# - Number of chunks used
```

### Configuration

Set in `.env`:
- `OPENAI_API_KEY`: Required for Q&A
- `LLM_MODEL`: LLM model to use (default: "gpt-4o-mini")
- `LLM_TEMPERATURE`: Temperature for generation (default: 0.7)
- `RAG_CONTEXT_CHUNKS`: Number of chunks to use as context (default: 5)
- `RAG_MAX_CONTEXT_LENGTH`: Maximum context length in tokens (default: 4000)

### Important Notes

- **Document-Only Answers**: The system is configured to answer ONLY based on uploaded documents
- **No External Knowledge**: If the context doesn't contain enough information, the system will say so
- **Source Citations**: Each answer includes source chunks with scores for transparency
- **Confidence Scores**: Higher scores indicate more relevant retrieved chunks

The Q&A chatbot provides intelligent, context-aware answers while ensuring responses are grounded in your uploaded content.

## Summarization Service

The summarization service generates concise summaries of PDFs, audio transcripts, and video transcripts using LLM:

### Features
- **Multi-format Support**: Summarize PDFs, audio transcripts, and video transcripts
- **LLM-powered**: Uses OpenAI models for high-quality summaries
- **Custom Prompts**: Support for custom summarization styles (bullet points, structured format, etc.)
- **Configurable Length**: Optional maximum summary length
- **Comprehensive Summaries**: Focuses on main topics, key points, and important details

### Supported File Types
- **PDFs**: Requires processing first (`/api/v1/files/{file_id}/process`)
- **Audio Files**: Requires transcription first (`/api/v1/files/{file_id}/transcribe`)
- **Video Files**: Requires transcription first (`/api/v1/files/{file_id}/transcribe`)

### Usage Example

```bash
# 1. For PDFs: Upload and process
POST /api/v1/files/upload
POST /api/v1/files/1/process

# 2. For Audio/Video: Upload and transcribe
POST /api/v1/files/upload
POST /api/v1/files/2/transcribe

# 3. Generate summary
POST /api/v1/files/1/summarize
{
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_length": 500
}

# 4. Custom summary with specific format
POST /api/v1/files/1/summarize/custom
{
  "custom_prompt": "Summarize the key technical concepts and provide a bullet-point list of main topics.",
  "model": "gpt-4o-mini"
}
```

### Configuration

Uses the same LLM settings as Q&A:
- `OPENAI_API_KEY`: Required for summarization
- `LLM_MODEL`: LLM model to use (default: "gpt-4o-mini")
- `LLM_TEMPERATURE`: Temperature for generation (default: 0.7)

### Custom Summarization

You can customize the summarization style using custom prompts:
- **Bullet Points**: "Summarize as a bullet-point list"
- **Structured Format**: "Provide a summary with sections: Overview, Key Points, Conclusions"
- **Technical Focus**: "Summarize focusing on technical concepts and methodologies"
- **Executive Summary**: "Create an executive summary highlighting main decisions and recommendations"

The summarization service provides intelligent, concise summaries that capture the essence of your documents and transcripts.

## Media Playback API

The media playback API provides endpoints to get media file URLs and timestamps for frontend media player integration:

### Features
- **File URL Generation**: Returns URLs to access media files
- **Timestamp Support**: Includes start timestamp for playback positioning
- **Formatted Timestamps**: Returns both seconds and formatted time (HH:MM:SS.mmm)
- **Multiple Endpoints**: GET and POST methods for flexibility
- **Path-based Timestamp**: Convenient endpoint with timestamp in path

### Usage Example

```bash
# 1. Get playback info without timestamp (starts at beginning)
GET /api/v1/files/1/playback

# 2. Get playback info with timestamp (query parameter)
GET /api/v1/files/1/playback?timestamp=10.5

# 3. Get playback info with timestamp (POST method)
POST /api/v1/files/1/playback
{
  "timestamp": 10.5
}

# 4. Get playback info from specific timestamp (path parameter)
GET /api/v1/files/1/playback/from-timestamp/10.5

# Response:
{
  "file_id": 1,
  "file_name": "video.mp4",
  "file_type": "video",
  "file_url": "/api/v1/files/1/download",
  "timestamp": 10.5,
  "formatted_timestamp": "00:10.500",
  "mime_type": "video/mp4",
  "file_size_mb": 25.5
}
```

### Frontend Integration

The playback API is designed for easy frontend integration:

```javascript
// Example: Get playback info and start media player
const response = await fetch('/api/v1/files/1/playback?timestamp=10.5');
const playbackInfo = await response.json();

// Use in HTML5 video/audio player
const video = document.getElementById('video-player');
video.src = playbackInfo.file_url;
video.currentTime = playbackInfo.timestamp;
video.play();
```

### Integration with Q&A

Combine with Q&A responses for seamless navigation:

```bash
# 1. Ask a question about audio/video
POST /api/v1/ask
{
  "question": "What was discussed?",
  "file_id": 1
}

# Response includes timestamps:
{
  "answer": "...",
  "timestamps": [
    {
      "start": 10.5,
      "end": 25.3,
      "formatted_start": "00:10.500",
      "formatted_end": "00:25.300"
    }
  ]
}

# 2. Get playback info for the timestamp
GET /api/v1/files/1/playback?timestamp=10.5

# 3. Frontend can now start playback at the relevant time
```

The media playback API enables frontend applications to easily integrate media players with timestamp-based navigation, creating a seamless experience for users to jump to relevant sections in audio/video content.

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


## License

MIT

