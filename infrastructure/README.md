# Infrastructure & Deployment

## Quick Start - Local Development

```bash
# Start everything (PostgreSQL + Backend + Frontend)
make dev-local
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## AWS Deployment

### Option 1: SAM (Serverless) - ~$21-43/month

```bash
# 1. Deploy infrastructure
make sam-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password

# 2. Build and push images (get ECR URLs from make sam-status)
docker build -f infrastructure/docker/Dockerfile.backend -t vector-search-backend .
docker tag vector-search-backend:latest <BACKEND_ECR_URL>:latest
docker push <BACKEND_ECR_URL>:latest

# 3. Deploy frontend to S3
make frontend-build
aws s3 sync frontend/dist/ s3://<BUCKET_NAME>/ --delete
```

### Option 2: CloudFormation + App Runner - ~$50-80/month

```bash
# 1. Deploy infrastructure
make cf-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password

# 2. Build and push images (auto-deploys)
make docker-push-backend ECR_REPO=<backend-ecr-url>
make docker-push-frontend ECR_REPO=<frontend-ecr-url>
```

## Prerequisites

- **Local**: Docker, Python 3.9+, Node.js 18+, `uv`
- **AWS**: AWS CLI, SAM CLI (Option 1), Docker, RDS PostgreSQL with pgvector

## Environment Variables

**Backend:**
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=dlt_dev
POSTGRES_USER=dlt_user
POSTGRES_PASSWORD=dlt_password
```

**Frontend:**
```
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

**Frontend can't connect:**
- Check backend: `curl http://localhost:8000/health`
- Verify `VITE_API_URL`

**PostgreSQL errors:**
- Check running: `docker ps | grep postgres`
- Verify connection: `docker exec -it vector-search-postgres psql -U dlt_user -d dlt_dev`

**No search results:**
- Load embeddings: `make load-embeddings`
- Lower similarity threshold
- Verify pgvector: `docker exec -it postgres psql -U dlt_user -d dlt_dev -c "SELECT * FROM pg_extension WHERE extname='vector';"`

## Structure

- `sam/` - SAM templates for serverless deployment
- `cloudformation/` - CloudFormation templates for App Runner
- `docker/` - Docker Compose configuration
- `localstack/` - LocalStack for local AWS testing
