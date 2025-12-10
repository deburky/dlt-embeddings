.PHONY: help install init test clean clean-pipeline run-sagemaker build package install-local localstack-up localstack-down localstack-setup test-local test-json test-json-dir test-json-custom test-json-full setup-pgvector load-embeddings test-embeddings-quick load-embeddings-full test-embeddings test-embeddings-simple test-embeddings-full

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies using uv"
	@echo "  make init          - Initialize dlt configuration"
	@echo "  make test          - Run tests"
	@echo "  make clean         - Clean up generated files"
	@echo ""
	@echo "  make run-sagemaker    - Run SageMaker pipeline"
	@echo "  make run-application  - Run application pipeline"
	@echo "  make run-s3-sagemaker - Run S3 SageMaker pipeline"
	@echo "  make test-s3          - Test S3 connection and credentials"
	@echo "  make test-s3-quick    - Quick S3 connection test"
	@echo "  make demo-parse       - Demo legacy format parsing"
	@echo "  make lint             - Run code linting"
	@echo "  make format           - Format code with ruff"
	@echo "  make format-makefile  - Format Makefile with mbake"
	@echo "  make build            - Build the package"
	@echo "  make package          - Build and create distribution package"
	@echo "  make install-local    - Install package locally in editable mode"
	@echo ""
	@echo "Local Testing:"
	@echo "  make localstack-up       - Start local PostgreSQL (Redshift-compatible)"
	@echo "  make localstack-down     - Stop local PostgreSQL"
	@echo "  make localstack-setup    - Setup schema and system tables"
	@echo ""
	@echo "JSON to PostgreSQL Testing:"
	@echo "  make test-json           - Test loading JSON file to PostgreSQL (uses examples/sample_data.json)"
	@echo "  make test-json-dir       - Test loading JSON directory to PostgreSQL"
	@echo "  make test-json-full      - Full test (start postgres + load JSON)"
	@echo ""
	@echo "Embeddings & Vector Database:"
	@echo "  make load-embeddings     - Load conversations with embeddings (16K+ messages, 2-5 min)"
	@echo "  make load-embeddings-full - Full pipeline (start postgres + load embeddings)"
	@echo "  make setup-pgvector      - Setup pgvector extension in PostgreSQL"
	@echo ""
	@echo "Production Testing:"
	@echo "  make test-production     - Test pipeline on production Redshift"

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
	@echo "  Database: dlt_dev"
	@echo "  User: dlt_user"
	@echo "  Password: dlt_password"

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
	@docker exec dlt-postgres psql -U dlt_user -d dlt_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" || \
		echo "⚠️  Note: pgvector extension not available in standard PostgreSQL image"
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