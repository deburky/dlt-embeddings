# Docker Configuration

This directory contains Docker configuration files for the vector search application.

## Files

- `Dockerfile.backend` - Backend (FastAPI) Docker image
- `docker-compose.yml` - Docker Compose configuration for all services

## Structure

```
infrastructure/docker/
  ├── Dockerfile.backend    # Backend service Dockerfile
  └── docker-compose.yml    # Full-stack Docker Compose configuration

frontend/
  └── Dockerfile            # Frontend service Dockerfile
```

## Usage

Run from the project root:

```bash
# Start all services
make docker-up

# Stop all services
make docker-down

# Build images
make docker-build
```

Or directly:

```bash
cd infrastructure/docker
docker-compose up -d
```

The `docker-compose.yml` references:
- `Dockerfile.backend` in this directory
- `frontend/Dockerfile` in the frontend directory
- Build context is set to project root for proper file access

