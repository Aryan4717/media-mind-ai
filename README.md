# Media Mind AI - Backend API

A production-ready FastAPI backend for an AI-powered document and multimedia Q&A system.

## Features

- 🚀 FastAPI with async support
- 📁 Modular architecture (routes, services, models, schemas, config)
- 🔐 Environment variable configuration
- 🏥 Health check endpoints (health, readiness, liveness)
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
│   │   └── settings.py      # Environment configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   ├── services/
│   │   └── __init__.py      # Business logic layer
│   ├── models/
│   │   └── __init__.py      # Database models
│   └── schemas/
│       └── __init__.py      # Pydantic schemas
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
- **Pydantic Settings** for configuration management
- **Uvicorn** as the ASGI server

## Next Steps

1. Add database models in `app/models/`
2. Create API schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add new routes in `app/routes/`
5. Configure database connection in `app/config/settings.py`

## License

MIT

