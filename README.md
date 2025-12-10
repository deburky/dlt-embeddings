# dlt-embeddings

<img src="https://cdn.sanity.io/images/nsq559ov/production/7f85e56e715b847c5519848b7198db73f793448d-82x25.svg?w=2000&auto=format"><br>

A pip-installable [dlt](https://dlthub.com/) (data load tool) package for loading conversations with embeddings into PostgreSQL with pgvector support. This package provides efficient pipelines for processing conversation data, generating embeddings using sentence-transformers, and storing them in a vector database.

## Features

- 🤖 **Automatic Embedding Generation** - Uses sentence-transformers to generate embeddings for conversation messages
- 🗄️ **Vector Database Support** - Stores embeddings in PostgreSQL with pgvector extension
- 📊 **Conversation Processing** - Extracts and processes messages from ChatGPT-style conversation exports
- 🚀 **Production Ready** - Built on dlt with proper state management and incremental loading
- 🔄 **Flexible Loading** - Supports both full replacement and incremental append modes

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Docker (for local PostgreSQL with pgvector)
- PostgreSQL with pgvector extension (for production)

## Installation

### Development Installation

```bash
# Clone the repository
git git@github.com:deburky/dlt-embeddings.git
cd dlt-embeddings

# Install dependencies using uv
uv sync

# Install the package in editable mode
uv pip install -e .
```

### From PyPI (when published)

```bash
pip install dlt-embeddings
```

## Quick Start

### 1. Start Local PostgreSQL with pgvector

```bash
make localstack-up
```

This starts a PostgreSQL container with pgvector extension on `localhost:5432`.

### 2. Load Conversations with Embeddings

```bash
make load-embeddings
```

This will:
- Load conversations from `test_data/conversations.json`
- Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Store 16,140+ messages with 384-dimensional embeddings in PostgreSQL
- Takes approximately 2-5 minutes

### 3. Verify the Data

The pipeline automatically verifies the loaded data and shows:
- Total messages loaded
- Embedding dimensions
- Sample messages
- Distribution by role (user/assistant/tool)

## Usage

### Using the Makefile

```bash
# Start PostgreSQL with pgvector
make localstack-up

# Load conversations with embeddings (full pipeline)
make load-embeddings

# Load without embeddings (structure test only)
make test-embeddings-quick

# Full pipeline (start DB + load data)
make load-embeddings-full

# Stop PostgreSQL
make localstack-down
```

### Using Python API

```python
import dlt
from dlt_embeddings.sources.conversations_embeddings_source import conversations_with_embeddings

# Create pipeline
pipeline = dlt.pipeline(
    pipeline_name="conversations_embeddings",
    destination=dlt.destinations.postgres(),
    dataset_name="vector_db"
)

# Load conversations with embeddings
source = conversations_with_embeddings(
    file_path="test_data/conversations.json",
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    table_name="conversations",
    batch_size=32
)

# Run the pipeline
load_info = pipeline.run(source)
print(f"Loaded {len(load_info.loads_ids)} batches")
```

### Command Line Options

```bash
# Use a different model
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --model sentence-transformers/paraphrase-MiniLM-L6-v2

# Custom table and schema
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --table my_conversations \
    --schema my_schema

# Load without embeddings (quick test)
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --no-embeddings

# Custom PostgreSQL connection
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --host localhost \
    --port 5432 \
    --database dlt_dev \
    --username dlt_user \
    --password dlt_password
```

## Configuration

### PostgreSQL with pgvector

The pipeline expects PostgreSQL with the pgvector extension. For local development:

```bash
cd infrastructure/localstack
docker-compose -f docker-compose-pgvector.yml up -d
```

Default connection settings:
- Host: `localhost`
- Port: `5432`
- Database: `dlt_dev`
- Username: `dlt_user`
- Password: `dlt_password`

### Environment Variables

The pipeline uses dlt's configuration system. You can configure via environment variables:

```bash
export DESTINATION__POSTGRES__CREDENTIALS__HOST=localhost
export DESTINATION__POSTGRES__CREDENTIALS__PORT=5432
export DESTINATION__POSTGRES__CREDENTIALS__DATABASE=dlt_dev
export DESTINATION__POSTGRES__CREDENTIALS__USERNAME=dlt_user
export DESTINATION__POSTGRES__CREDENTIALS__PASSWORD=dlt_password
```

## Data Format

### Input Format

The pipeline expects conversation data in ChatGPT export format:

```json
[
  {
    "title": "Conversation Title",
    "mapping": {
      "node_id": {
        "message": {
          "id": "msg_id",
          "author": {"role": "user"},
          "content": {"parts": ["Message text"]},
          "create_time": 1234567890,
          "update_time": 1234567890
        }
      }
    }
  }
]
```

### Output Schema

The pipeline creates a table with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `conversation_id` | text | Conversation title/ID |
| `message_id` | text | Unique message ID |
| `role` | text | Message role (user/assistant/tool) |
| `text` | text | Message content |
| `embedding` | vector(384) | Embedding vector (pgvector type) |
| `create_time` | float | Message creation timestamp |

## Development

### Running Tests

```bash
# Run all tests
make test

# Or using pytest directly
uv run pytest tests/ -v
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Or using ruff directly
uv run ruff format .
uv run ruff check .
```

### Building the Package

```bash
# Build distribution
make build

# This creates both wheel and source distribution in dist/
```

## Troubleshooting

### PostgreSQL Not Running

If you get connection errors:

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Start PostgreSQL
make localstack-up

# Check logs
docker logs dlt-postgres-pgvector
```

### pgvector Extension Not Available

If you get pgvector errors:

```bash
# Ensure you're using the pgvector-enabled image
cd infrastructure/localstack
docker-compose -f docker-compose-pgvector.yml up -d

# Verify extension
docker exec dlt-postgres-pgvector psql -U dlt_user -d dlt_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Out of Memory During Embedding Generation

If you run out of memory:

```bash
# Reduce batch size
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --batch-size 16

# Or use CPU instead of GPU
python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --device cpu
```

### Clean Pipeline State

If you need to reset the pipeline:

```bash
# Clean pipeline state
make clean-pipeline

# Drop the table and reload
docker exec dlt-postgres-pgvector psql -U dlt_user -d dlt_dev -c "DROP TABLE IF EXISTS conversations CASCADE;"
make load-embeddings
```

## Performance

### Embedding Generation

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (default)
- **Dimension**: 384
- **Speed**: ~8-9 batches/second on CPU
- **Time**: ~2-5 minutes for 16,140 messages

### Optimization Tips

1. **Increase batch size** for faster embedding generation (default: 32)
2. **Use GPU** if available (`--device cuda` or `--device mps` for Mac)
3. **Use smaller models** for faster processing (e.g., `paraphrase-MiniLM-L3-v2`)

## Resources

- [dlt Documentation](https://dlthub.com/docs)
- [dlt PostgreSQL Destination](https://dlthub.com/docs/dlt-ecosystem/destinations/postgres)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [sentence-transformers](https://www.sbert.net/)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
