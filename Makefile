.PHONY: help install init test clean clean-pipeline run-sagemaker build package install-local localstack-up localstack-down localstack-setup test-local test-json test-json-dir test-json-custom test-json-full setup-pgvector load-embeddings test-embeddings-quick load-embeddings-full test-embeddings test-embeddings-simple test-embeddings-full frontend-install frontend-build frontend-dev backend-dev dev dev-local docker-up docker-down docker-build sam-build sam-deploy sam-local sam-destroy sam-status cf-deploy cf-status cf-destroy docker-push-backend docker-push-frontend

help:
	@echo "Available commands:"
	@echo "install - Install dependencies using uv"
	@echo "init - Initialize dlt configuration"
	@echo "test - Run tests"
	@echo "clean - Clean up generated files"
	@echo ""
	@echo "run-sagemaker - Run SageMaker pipeline"
	@echo "run-application - Run application pipeline"
	@echo "run-s3-sagemaker - Run S3 SageMaker pipeline"
	@echo "test-s3 - Test S3 connection and credentials"
	@echo "test-s3-quick - Quick S3 connection test"
	@echo "demo-parse - Demo legacy format parsing"
	@echo "lint - Run code linting"
	@echo "format - Format code with ruff"
	@echo "format-makefile - Format Makefile with mbake"
	@echo "build - Build the package"
	@echo "package - Build and create distribution package"
	@echo "install-local - Install package locally in editable mode"
	@echo ""
	@echo "Local Testing:"
	@echo "localstack-up - Start local PostgreSQL (Redshift-compatible)"
	@echo "localstack-down - Stop local PostgreSQL"
	@echo "localstack-setup - Setup schema and system tables"
	@echo ""
	@echo "JSON to PostgreSQL Testing:"
	@echo "test-json - Test loading JSON file to PostgreSQL (uses examples/sample_data.json)"
	@echo "test-json-dir - Test loading JSON directory to PostgreSQL"
	@echo "test-json-full - Full test (start postgres + load JSON)"
	@echo ""
	@echo "Embeddings & Vector Database:"
	@echo "load-embeddings - Load conversations with embeddings (16K+ messages, 2-5 min)"
	@echo "load-embeddings-full - Full pipeline (start postgres + load embeddings)"
	@echo "setup-pgvector - Setup pgvector extension in PostgreSQL"
	@echo ""
	@echo "Full-Stack Application:"
	@echo "frontend-install - Install frontend dependencies"
	@echo "frontend-build - Build frontend for production"
	@echo "frontend-dev - Start frontend development server"
	@echo "backend-dev - Start FastAPI backend server"
	@echo "dev - Start both frontend and backend (development)"
	@echo "dev-local - Start full local environment (PostgreSQL + Backend + Frontend)"
	@echo "docker-up - Start all services with Docker Compose"
	@echo "docker-down - Stop all Docker services"
	@echo "docker-build - Build Docker images"
	@echo ""
	@echo "Production Testing:"
	@echo "test-production - Test pipeline on production Redshift"
	@echo ""
	@echo "AWS Deployment:"
	@echo "SAM (Serverless):"
	@echo "sam-build - Build SAM application"
	@echo "sam-deploy - Deploy to AWS using SAM"
	@echo "sam-local - Run API locally with SAM Local"
	@echo "sam-destroy - Destroy SAM stack"
	@echo "sam-status - Show SAM deployment status"
	@echo ""
	@echo "CloudFormation + App Runner:"
	@echo "cf-deploy - Deploy using CloudFormation + App Runner"
	@echo "cf-status - Show CloudFormation deployment status"
	@echo "cf-destroy - Destroy CloudFormation stack"
	@echo ""
	@echo "Docker Image Management:"
	@echo "docker-push-backend - Build and push backend image to ECR"
	@echo "docker-push-frontend - Build and push frontend image to ECR"

install:
	@echo "Installing dependencies..."
	uv sync
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Note: If you see a VIRTUAL_ENV warning, you're in another project's venv."
	@echo "To fix: deactivate && source .venv/bin/activate"

install-local:
	uv pip install -e .

init:
	@echo "Setting up dlt configuration..."
	@mkdir -p dlt_project/.dlt data/sagemaker data/custom data/applications
	@if [ ! -f dlt_project/.dlt/secrets.toml ]; then \
		cp dlt_project/.dlt/secrets.toml.example dlt_project/.dlt/secrets.toml; \
		echo "Created dlt_project/.dlt/secrets.toml - please update with your credentials"; \
	fi
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env - please update with your credentials"; \
	fi

test:
	uv run pytest tests/ -v

clean:
	rm -rf dlt_project/.dlt/.sources dlt_project/.dlt/pipelines *.duckdb *.duckdb.wal
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-pipeline:
	@echo "Cleaning pipeline state and load packages..."
	rm -rf dlt_project/.dlt/pipelines dlt_project/.dlt/.sources
	@echo "✅ Pipeline state cleared"

build:
	uv build

package: clean build
	@echo "Package built successfully in dist/"
	@ls -lh dist/

run-sagemaker:
	uv run python -m dlt_project.pipelines.sagemaker_pipeline

run-application:
	uv run python -m dlt_project.pipelines.application_pipeline

run-s3-sagemaker:
	uv run python -m dlt_project.pipelines.s3_sagemaker_pipeline

test-s3:
	@echo "Testing S3 connection (this may take a moment)..."
	uv run python examples/test_s3_connection.py

test-s3-quick:
	@echo "Quick S3 connection test..."
	uv run python examples/test_s3_connection.py --quick

demo-parse:
	uv run python examples/parse_legacy_format.py

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-makefile:
	uv run mbake format Makefile

# LocalStack commands
localstack-up:
	@echo "Starting LocalStack with PostgreSQL (pgvector)..."
	cd infrastructure/localstack && docker-compose -f docker-compose-pgvector.yml up -d
	@echo "✓ PostgreSQL with pgvector is running on localhost:5432"
	@echo "Database: dlt_dev"
	@echo "User: dlt_user"
	@echo "Password: dlt_password"

localstack-down:
	@echo "Stopping LocalStack..."
	cd infrastructure/localstack && docker-compose -f docker-compose-pgvector.yml down
	@echo "✓ LocalStack stopped"

localstack-setup:
	@echo "Setting up Redshift cluster in LocalStack..."
	uv run python test_data/setup_localstack.py

test-local:
	@echo "Testing pipeline with simple data..."
	uv run python test_data/test_simple_local.py

test-local-full: localstack-up localstack-setup test-local
	@echo ""
	@echo "✅ Full local test completed!"

test-restricted:
	@echo "Testing with RESTRICTED user (schema-only permissions)..."
	uv run python test_data/test_restricted_user.py

test-restricted-full:
	@echo "Cleaning previous test state..."
	rm -rf dlt_project/.dlt/pipelines .dlt/pipelines .localstack/localstack_data
	$(MAKE) localstack-down
	@echo ""
	$(MAKE) localstack-up
	@echo ""
	@echo "Setting up restricted user..."
	uv run python test_data/setup_restricted_user.py
	@echo ""
	$(MAKE) test-restricted
	@echo ""
	@echo "✅ Restricted user test completed!"
	@echo "✅ PROOF: Pipeline works with schema-only permissions!"

test-production:
	@echo "Testing on production Redshift..."
	@echo "⚠️  This will create a test table: dlt_dev.dlt_test_simple"
	@echo ""
	uv run python test_data/test_production_redshift.py

test-date-extraction:
	@echo "Testing date extraction from S3 keys..."
	uv run python test_data/test_date_extraction.py

# JSON to PostgreSQL test pipeline
test-json:
	@echo "Testing JSON to PostgreSQL pipeline..."
	@echo "Loading: examples/sample_data.json"
	uv run python test_data/test_json_to_postgres.py examples/sample_data.json

test-json-dir:
	@echo "Testing JSON directory to PostgreSQL pipeline..."
	@echo "Loading: test_data/sagemaker (if exists)"
	@if [ -d "test_data/sagemaker" ]; then \
		uv run python test_data/test_json_to_postgres.py test_data/sagemaker --directory; \
	else \
		echo "⚠️  Directory test_data/sagemaker not found. Using examples/"; \
		uv run python test_data/test_json_to_postgres.py examples/ --directory; \
	fi

test-json-custom:
	@echo "Usage: make test-json-custom JSON_PATH=path/to/file.json [TABLE=table_name] [SCHEMA=schema_name]"
	@if [ -z "$(JSON_PATH)" ]; then \
		echo "❌ Error: JSON_PATH is required"; \
		echo "Example: make test-json-custom JSON_PATH=examples/sample_data.json TABLE=my_table"; \
		exit 1; \
	fi
	uv run python test_data/test_json_to_postgres.py $(JSON_PATH) \
		$(if $(TABLE),--table $(TABLE)) \
		$(if $(SCHEMA),--schema $(SCHEMA))

test-json-full: localstack-up
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5
	@echo "Loading JSON data..."
	$(MAKE) test-json
	@echo ""
	@echo "✅ Full JSON test completed!"
	@echo ""
	@echo "To stop PostgreSQL: make localstack-down"

# Embeddings and vector database
setup-pgvector:
	@echo "Setting up pgvector extension in PostgreSQL..."
	@docker exec dlt-postgres-pgvector psql -U dlt_user -d dlt_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" || \
		docker exec vector-search-postgres psql -U dlt_user -d dlt_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" || \
		echo "⚠️  Note: pgvector extension not available or container not running"
	@echo "✅ pgvector setup attempted"

load-embeddings: clean-pipeline
	@echo "Loading conversations with embeddings..."
	@echo "📊 Source: test_data/conversations.json (72 conversations, 16,140 messages)"
	@echo "⏱️  Estimated time: 2-5 minutes for embedding generation"
	@echo ""
	uv run python test_data/test_conversations_embeddings.py test_data/conversations.json

test-embeddings-quick:
	@echo "Quick structure test (no embeddings)..."
	uv run python test_data/test_conversations_embeddings.py test_data/conversations.json --no-embeddings

load-embeddings-full: localstack-up
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5
	@echo "Setting up pgvector..."
	-$(MAKE) setup-pgvector
	@echo "Loading conversations with embeddings..."
	$(MAKE) load-embeddings
	@echo ""
	@echo "✅ Full embeddings pipeline completed!"
	@echo ""
	@echo "To stop PostgreSQL: make localstack-down"

# Full-Stack Application
frontend-install:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

frontend-build:
	@echo "Building frontend for production..."
	cd frontend && npm run build
	@echo "✅ Frontend built successfully"

frontend-dev:
	@echo "Starting frontend development server..."
	@echo "📍 Frontend will be available at http://localhost:3000"
	cd frontend && npm run dev

backend-dev:
	@echo "Starting FastAPI backend server..."
	@echo "📍 Backend API: http://localhost:8000"
	@echo "📍 API Docs: http://localhost:8000/docs"
	uv run uvicorn dlt_embeddings.api:app --reload --host 0.0.0.0 --port 8000

dev:
	@echo ""
	@echo "🚀 Starting full-stack application..."
	@echo "📍 Frontend: http://localhost:3000"
	@echo "📍 Backend API: http://localhost:8000"
	@echo "📍 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Starting backend and frontend in parallel..."
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@trap 'kill 0' EXIT; \
	$(MAKE) backend-dev & \
	cd frontend && npm install > /dev/null 2>&1 && npm run dev & \
	wait

dev-full: load-embeddings-full
	@echo ""
	@echo "🚀 Starting full-stack application with data loading..."
	@echo "📍 Frontend: http://localhost:3000"
	@echo "📍 Backend API: http://localhost:8000"
	@echo "📍 API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Starting backend and frontend in parallel..."
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@trap 'kill 0' EXIT; \
	$(MAKE) backend-dev & \
	cd frontend && npm install > /dev/null 2>&1 && npm run dev & \
	wait

dev-local:
	@echo "🚀 Starting local development environment..."
	@echo "📍 Frontend: http://localhost:3000"
	@echo "📍 Backend API: http://localhost:8000"
	@echo "📍 API Docs: http://localhost:8000/docs"
	@echo "📍 PostgreSQL: localhost:5432"
	@echo ""
	@echo "This will start PostgreSQL, backend, and frontend..."
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@if ! docker ps | grep -q vector-search-postgres; then \
		echo "Starting PostgreSQL..."; \
		$(MAKE) localstack-up; \
		sleep 5; \
		$(MAKE) setup-pgvector; \
	fi
	@echo "Starting backend and frontend..."
	@trap 'kill 0' EXIT; \
	$(MAKE) backend-dev & \
	cd frontend && npm install > /dev/null 2>&1 && npm run dev & \
	wait

docker-build:
	@echo "Building Docker images..."
	cd infrastructure/docker && docker-compose build
	@echo "✅ Docker images built"

docker-up:
	@echo "Starting all services with Docker Compose..."
	@echo "📍 Frontend: http://localhost:3000"
	@echo "📍 Backend API: http://localhost:8000"
	@echo "📍 PostgreSQL: localhost:5432"
	cd infrastructure/docker && docker-compose up -d
	@echo "✅ All services started"
	@echo ""
	@echo "View logs: cd infrastructure/docker && docker-compose logs -f"
	@echo "Stop services: make docker-down"

docker-down:
	@echo "Stopping all Docker services..."
	cd infrastructure/docker && docker-compose down
	@echo "✅ All services stopped"

# AWS Deployment (SAM)
AWS_STACK_NAME ?= vector-search-production
AWS_REGION ?= us-east-1
SAM_TEMPLATE = infrastructure/sam/template.yaml
SAM_BUILD_DIR = .aws-sam

sam-build:
	@echo "🏗️  Building SAM application..."
	@if ! command -v sam &> /dev/null; then \
		echo "❌ Error: SAM CLI is not installed"; \
		echo "Install it: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"; \
		exit 1; \
	fi
	sam build --template-file $(SAM_TEMPLATE) --build-dir $(SAM_BUILD_DIR)
	@echo "✅ SAM application built"

sam-deploy:
	@if [ -z "$(POSTGRES_HOST)" ]; then \
		echo "❌ Error: POSTGRES_HOST is required"; \
		echo "Usage: make sam-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password"; \
		exit 1; \
	fi
	@if [ -z "$(POSTGRES_PASSWORD)" ]; then \
		echo "❌ Error: POSTGRES_PASSWORD is required"; \
		echo "Usage: make sam-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password"; \
		exit 1; \
	fi
	@echo "🚀 Deploying to AWS using SAM..."
	@echo "Stack: $(AWS_STACK_NAME)"
	@echo "Region: $(AWS_REGION)"
	@if [ ! -d "$(SAM_BUILD_DIR)" ]; then \
		$(MAKE) sam-build; \
	fi
	sam deploy \
		--stack-name $(AWS_STACK_NAME) \
		--region $(AWS_REGION) \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides \
			ProjectName=vector-search \
			Environment=production \
			PostgresHost=$(POSTGRES_HOST) \
			PostgresPort=$(POSTGRES_PORT) \
			PostgresDatabase=$(POSTGRES_DATABASE) \
			PostgresUser=$(POSTGRES_USER) \
			PostgresPassword=$(POSTGRES_PASSWORD) \
		--confirm-changeset
	@echo "✅ SAM stack deployed"
	@echo ""
	@echo "Next: Run 'make sam-build-push' to build and push Docker images"

sam-local:
	@echo "🚀 Starting SAM Local API..."
	@echo "📍 API will be available at http://localhost:3000"
	@echo ""
	@if ! command -v sam &> /dev/null; then \
		echo "❌ Error: SAM CLI is not installed"; \
		exit 1; \
	fi
	@if [ ! -d "$(SAM_BUILD_DIR)" ]; then \
		$(MAKE) sam-build; \
	fi
	@echo "Note: For full local development, use 'make dev-local' instead"
	sam local start-api \
		--template $(SAM_BUILD_DIR)/template.yaml \
		--port 3000 \
		--env-vars env.json 2>/dev/null || \
		sam local start-api \
			--template $(SAM_BUILD_DIR)/template.yaml \
			--port 3000

sam-destroy:
	@echo "⚠️  This will delete the SAM stack: $(AWS_STACK_NAME)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "Deleting stack..."
	aws cloudformation delete-stack \
		--stack-name $(AWS_STACK_NAME) \
		--region $(AWS_REGION)
	@echo "Waiting for stack deletion..."
	aws cloudformation wait stack-delete-complete \
		--stack-name $(AWS_STACK_NAME) \
		--region $(AWS_REGION)
	@echo "✅ Stack deleted successfully"

sam-status:
	@echo "📊 SAM Deployment Status"
	@echo ""
	@aws cloudformation describe-stacks \
		--stack-name $(AWS_STACK_NAME) \
		--query "Stacks[0].{Status:StackStatus,BackendURL:Outputs[?OutputKey=='BackendApiUrl'].OutputValue|[0],FrontendURL:Outputs[?OutputKey=='FrontendUrl'].OutputValue|[0]}" \
		--output table \
		--region $(AWS_REGION) 2>/dev/null || \
		echo "❌ Stack not found. Run 'make sam-deploy' first"

# CloudFormation + App Runner Deployment
CF_STACK_NAME ?= vector-search-apprunner
CF_TEMPLATE = infrastructure/cloudformation/apprunner-template.yaml

cf-deploy:
	@if [ -z "$(POSTGRES_HOST)" ]; then \
		echo "❌ Error: POSTGRES_HOST is required"; \
		echo "Usage: make cf-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password"; \
		exit 1; \
	fi
	@if [ -z "$(POSTGRES_PASSWORD)" ]; then \
		echo "❌ Error: POSTGRES_PASSWORD is required"; \
		echo "Usage: make cf-deploy POSTGRES_HOST=your-rds-endpoint POSTGRES_PASSWORD=your-password"; \
		exit 1; \
	fi
	@echo "🚀 Deploying to AWS using CloudFormation + App Runner..."
	@echo "Stack: $(CF_STACK_NAME)"
	@echo "Region: $(AWS_REGION)"
	aws cloudformation create-stack \
		--stack-name $(CF_STACK_NAME) \
		--template-body file://$(CF_TEMPLATE) \
		--parameters \
			ParameterKey=PostgresHost,ParameterValue=$(POSTGRES_HOST) \
			ParameterKey=PostgresPort,ParameterValue=$(POSTGRES_PORT) \
			ParameterKey=PostgresDatabase,ParameterValue=$(POSTGRES_DATABASE) \
			ParameterKey=PostgresUser,ParameterValue=$(POSTGRES_USER) \
			ParameterKey=PostgresPassword,ParameterValue=$(POSTGRES_PASSWORD) \
		--capabilities CAPABILITY_NAMED_IAM \
		--region $(AWS_REGION)
	@echo "⏳ Waiting for stack creation..."
	aws cloudformation wait stack-create-complete \
		--stack-name $(CF_STACK_NAME) \
		--region $(AWS_REGION)
	@echo "✅ CloudFormation stack deployed"
	@echo ""
	@echo "Next: Build and push Docker images (see infrastructure/AWS_DEPLOYMENT.md)"

cf-status:
	@echo "📊 CloudFormation Deployment Status"
	@echo ""
	@aws cloudformation describe-stacks \
		--stack-name $(CF_STACK_NAME) \
		--query "Stacks[0].{Status:StackStatus,BackendURL:Outputs[?OutputKey=='BackendURL'].OutputValue|[0],FrontendURL:Outputs[?OutputKey=='FrontendURL'].OutputValue|[0]}" \
		--output table \
		--region $(AWS_REGION) 2>/dev/null || \
		echo "❌ Stack not found. Run 'make cf-deploy' first"

cf-destroy:
	@echo "⚠️  This will delete the CloudFormation stack: $(CF_STACK_NAME)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "Deleting stack..."
	aws cloudformation delete-stack \
		--stack-name $(CF_STACK_NAME) \
		--region $(AWS_REGION)
	@echo "Waiting for stack deletion..."
	aws cloudformation wait stack-delete-complete \
		--stack-name $(CF_STACK_NAME) \
		--region $(AWS_REGION)
	@echo "✅ Stack deleted successfully"

# Docker image build and push helpers
docker-push-backend:
	@echo "🐳 Building and pushing backend image..."
	@if [ -z "$(ECR_REPO)" ]; then \
		echo "❌ Error: ECR_REPO is required"; \
		echo "Usage: make docker-push-backend ECR_REPO=123456789.dkr.ecr.us-east-1.amazonaws.com/vector-search-backend"; \
		exit 1; \
	fi
	docker build -f infrastructure/docker/Dockerfile.backend -t vector-search-backend .
	docker tag vector-search-backend:latest $(ECR_REPO):latest
	docker push $(ECR_REPO):latest
	@echo "✅ Backend image pushed"

docker-push-frontend:
	@echo "🐳 Building and pushing frontend image..."
	@if [ -z "$(ECR_REPO)" ]; then \
		echo "❌ Error: ECR_REPO is required"; \
		echo "Usage: make docker-push-frontend ECR_REPO=123456789.dkr.ecr.us-east-1.amazonaws.com/vector-search-frontend"; \
		exit 1; \
	fi
	cd frontend && docker build -t vector-search-frontend .
	docker tag vector-search-frontend:latest $(ECR_REPO):latest
	docker push $(ECR_REPO):latest
	@echo "✅ Frontend image pushed"