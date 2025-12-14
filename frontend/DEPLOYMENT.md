# Deployment Guide

Complete guide for deploying the Vector Search full-stack application.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│              (TypeScript + Vite)                         │
│                    Port: 3000                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/REST
                     │
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│              (Python + SQLAlchemy)                       │
│                    Port: 8000                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ SQL (asyncpg)
                     │
┌────────────────────▼────────────────────────────────────┐
│              PostgreSQL + pgvector                       │
│                    Port: 5432                            │
└─────────────────────────────────────────────────────────┘
```

## Local Development

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- uv (Python package manager)

### 1. Start PostgreSQL

```bash
make localstack-up
# Or
cd infrastructure/localstack
docker-compose -f docker-compose-pgvector.yml up -d
```

### 2. Load Data

```bash
make load-embeddings
```

### 3. Start Backend

```bash
# Install dependencies
uv sync

# Run FastAPI server
uv run uvicorn dlt_embeddings.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 4. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000

### 5. Using Docker Compose (All-in-One)

```bash
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- Backend API on port 8000
- Frontend on port 3000

## Production Deployment

### Option 1: AWS App Runner (Recommended)

#### Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- Docker

#### Steps

1. **Configure Terraform**

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

2. **Deploy Infrastructure**

```bash
terraform init
terraform plan
terraform apply
```

3. **Build and Push Docker Images**

```bash
# Get outputs
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(terraform output -raw aws_region)
BACKEND_REPO=$(terraform output -raw backend_ecr_repository)
FRONTEND_REPO=$(terraform output -raw frontend_ecr_repository)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
docker build -t vector-search-backend .
docker tag vector-search-backend:latest $BACKEND_REPO:latest
docker push $BACKEND_REPO:latest

# Build and push frontend
cd ../../frontend
docker build -t vector-search-frontend .
docker tag vector-search-frontend:latest $FRONTEND_REPO:latest
docker push $FRONTEND_REPO:latest
```

4. **Access Your Application**

```bash
# Get URLs
terraform output frontend_url
terraform output backend_url
```

### Option 2: Docker Compose on EC2/ECS

1. **Deploy to EC2**

```bash
# On your EC2 instance
git clone <your-repo>
cd dlt-embeddings
docker-compose up -d
```

2. **Deploy to ECS**

Use the provided Dockerfiles with ECS task definitions.

### Option 3: Kubernetes

Create Kubernetes manifests using the Docker images:

```yaml
# Example deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vector-search-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vector-search-backend
  template:
    metadata:
      labels:
        app: vector-search-backend
    spec:
      containers:
      - name: backend
        image: <your-registry>/vector-search-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_HOST
          value: "postgres-service"
        # ... other env vars
```

## Environment Variables

### Backend

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=dlt_dev
POSTGRES_USER=dlt_user
POSTGRES_PASSWORD=dlt_password
```

### Frontend

```bash
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## Testing with LocalStack

LocalStack allows you to test AWS services locally:

```bash
# Start LocalStack
cd infrastructure/localstack
docker-compose -f docker-compose-localstack.yml up -d

# Configure AWS CLI for LocalStack
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_ENDPOINT_URL=http://localhost:4566

# Use Terraform with LocalStack
cd ../terraform
terraform init
terraform apply
```

## Monitoring & Logging

### Backend Logs

```bash
# Docker
docker logs vector-search-backend

# App Runner
aws apprunner describe-service --service-arn <service-arn>
```

### Health Checks

- Backend: `GET /health`
- Frontend: `GET /`

## Scaling

### App Runner Auto-Scaling

App Runner automatically scales based on:
- Request volume
- CPU utilization
- Memory usage

Configure in `terraform/main.tf`:

```hcl
auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.example.arn
```

### Manual Scaling

```bash
aws apprunner update-service \
  --service-arn <service-arn> \
  --instance-configuration Cpu=2048,Memory=4096
```

## Security

### Production Checklist

- [ ] Use AWS Secrets Manager for database credentials
- [ ] Enable HTTPS (App Runner provides this automatically)
- [ ] Configure CORS properly (update `allow_origins` in `api.py`)
- [ ] Use VPC for database (not public)
- [ ] Enable database encryption at rest
- [ ] Use IAM roles instead of access keys
- [ ] Enable CloudWatch logging
- [ ] Set up WAF for DDoS protection

### Update CORS

In `dlt_embeddings/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Backend won't start

```bash
# Check database connection
docker exec -it vector-search-postgres psql -U dlt_user -d dlt_dev -c "SELECT 1;"

# Check logs
docker logs vector-search-backend
```

### Frontend can't connect to backend

- Check `VITE_API_URL` environment variable
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS configuration

### Vector search returns no results

- Verify embeddings are loaded: `dlt-embeddings-search stats`
- Check similarity threshold (try lowering it)
- Verify pgvector extension: `docker exec -it postgres psql -U dlt_user -d dlt_dev -c "SELECT * FROM pg_extension WHERE extname='vector';"`

## Cost Optimization

- Use App Runner's auto-scaling to scale down during low traffic
- Use RDS Reserved Instances for predictable workloads
- Enable RDS automated backups with 7-day retention
- Use CloudWatch alarms to monitor costs

## Support

For issues or questions:
1. Check the logs
2. Review the API documentation at `/docs`
3. Check GitHub issues

