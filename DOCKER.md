# Docker Setup Guide

This guide explains how to run the Media Mind AI application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   cd /path/to/media-mind-ai
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.docker.example .env
   # Edit .env and add your OpenAI API key and other configuration
   ```

3. **Build and start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Check service status**:
   ```bash
   docker-compose ps
   ```

5. **View logs**:
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

6. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Services

The docker-compose setup includes:

- **postgres**: PostgreSQL 16 database
- **redis**: Redis 7 for caching
- **backend**: FastAPI application
- **frontend**: React frontend served by nginx

## Environment Variables

Key environment variables (see `.env.docker.example`):

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `SECRET_KEY`: Application secret key (change in production)

## Database Initialization

The database tables are automatically created on first startup. To manually initialize:

```bash
docker-compose exec backend python -c "from app.config.database import init_db; import asyncio; asyncio.run(init_db())"
```

## Production Deployment

For production, use the production override:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Production Considerations

1. **Change default passwords** in `.env`
2. **Set strong SECRET_KEY**
3. **Use HTTPS** (add reverse proxy like Traefik or nginx)
4. **Set resource limits** in docker-compose.prod.yml
5. **Enable logging** to external service
6. **Backup volumes** regularly
7. **Use secrets management** for sensitive data

## Volumes

Data is persisted in Docker volumes:

- `postgres_data`: Database data
- `redis_data`: Redis data
- `uploads_data`: Uploaded files
- `faiss_index_data`: FAISS vector index

## Commands

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes data)
```bash
docker-compose down -v
```

### Rebuild services
```bash
docker-compose build --no-cache
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend bash

# Database shell
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Redis CLI
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD}
```

### View resource usage
```bash
docker-compose stats
```

## Troubleshooting

### Services won't start
- Check logs: `docker-compose logs`
- Verify environment variables in `.env`
- Ensure ports are not in use

### Database connection errors
- Wait for postgres to be healthy: `docker-compose ps postgres`
- Check DATABASE_URL format in environment

### Frontend can't connect to backend
- Verify CORS_ORIGINS includes frontend URL
- Check backend health: `curl http://localhost:8000/api/v1/health`

### Out of memory
- Reduce batch sizes in environment variables
- Add resource limits in docker-compose.yml

## Development

For development with hot-reload:

1. Mount source code as volumes
2. Use development environment variables
3. Enable debug mode

See `docker-compose.dev.yml` (if created) for development overrides.

