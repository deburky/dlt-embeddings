# Conversations Embeddings Pipeline

This directory contains a dlt pipeline for loading conversations with embeddings into PostgreSQL with pgvector.

## Overview

The pipeline:
1. Loads conversations from `conversations.json`
2. Extracts text content from messages
3. Generates embeddings using sentence-transformers
4. Stores messages with embeddings in PostgreSQL with pgvector extension

## Quick Start

### Option 1: Using Standard PostgreSQL (No pgvector)

Test the conversation extraction and structure without embeddings:

```bash
# Start PostgreSQL
make localstack-up

# Test structure only (no embeddings)
make test-embeddings-simple
```

### Option 2: Using PostgreSQL with pgvector

For full embedding support, you need PostgreSQL with pgvector extension:

```bash
# Stop standard postgres if running
make localstack-down

# Start PostgreSQL with pgvector
cd infrastructure/localstack
docker-compose -f docker-compose-pgvector.yml up -d

# Run full embeddings test
cd ../..
make test-embeddings
```

## Manual Usage

### Test Conversations Structure (No Embeddings)

```bash
uv run python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --no-embeddings
```

### Generate Embeddings with Default Model

```bash
uv run python test_data/test_conversations_embeddings.py \
    test_data/conversations.json
```

### Use Different Embedding Model

```bash
# Smaller model (faster)
uv run python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --model sentence-transformers/paraphrase-MiniLM-L6-v2

# Larger model (better quality)
uv run python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --model sentence-transformers/all-mpnet-base-v2
```

### Custom Table and Schema

```bash
uv run python test_data/test_conversations_embeddings.py \
    test_data/conversations.json \
    --table my_conversations \
    --schema my_schema
```

## Embedding Models

The pipeline uses [sentence-transformers](https://www.sbert.net/) for generating embeddings. Popular models:

| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | Default, balanced |
| `paraphrase-MiniLM-L6-v2` | 384 | Fast | Good | Paraphrase detection |
| `all-mpnet-base-v2` | 768 | Medium | Best | High quality needed |
| `multi-qa-MiniLM-L6-cos-v1` | 384 | Fast | Good | Q&A, search |

## PostgreSQL with pgvector

### Using Docker

The easiest way to get PostgreSQL with pgvector:

```bash
# Use the provided docker-compose file
cd infrastructure/localstack
docker-compose -f docker-compose-pgvector.yml up -d
```

### Manual Installation (macOS)

```bash
# Install PostgreSQL 17 and pgvector
brew install postgresql@17 pgvector

# Start PostgreSQL
brew services start postgresql@17

# Create database and enable extension
psql postgres -c "CREATE DATABASE dlt_dev;"
psql dlt_dev -c "CREATE EXTENSION vector;"
psql dlt_dev -c "CREATE USER dlt_user WITH PASSWORD 'dlt_password';"
psql dlt_dev -c "GRANT ALL PRIVILEGES ON DATABASE dlt_dev TO dlt_user;"
```

## Pipeline Features

### Conversation Extraction

The pipeline extracts:
- `conversation_id`: Title of the conversation
- `message_id`: Unique message identifier
- `role`: Message author role (user, assistant, system)
- `text`: Message text content
- `create_time`: Message creation timestamp
- `update_time`: Message update timestamp
- `embedding`: Vector embedding (384 or 768 dimensions)

### Batch Processing

Embeddings are generated in batches for efficiency:
- Default batch size: 32
- Configurable via `--batch-size` parameter
- Progress bar shows generation status

### Device Support

The pipeline automatically detects available compute:
- **CPU**: Default, works everywhere
- **CUDA**: NVIDIA GPUs (Linux/Windows)
- **MPS**: Apple Silicon GPUs (M1/M2/M3)

Specify device manually:
```bash
--device cpu    # Force CPU
--device cuda   # Force NVIDIA GPU
--device mps    # Force Apple Silicon GPU
```

## Example Output

```
============================================================
Conversations to PostgreSQL with Embeddings
============================================================
Conversations file: test_data/conversations.json
Table: conversations
Schema: dlt_dev
PostgreSQL: localhost:5432/dlt_dev
Model: sentence-transformers/all-MiniLM-L6-v2
Batch size: 32
Device: auto
============================================================

📥 Loading model: sentence-transformers/all-MiniLM-L6-v2
✅ Model loaded successfully
📖 Reading conversations from: test_data/conversations.json
📊 Found 150 conversations
💬 Extracted 1,234 messages
🤖 Generating embeddings (batch_size=32)...
✅ Generated 1,234 embeddings with dimension 384

============================================================
✅ Pipeline completed successfully!
============================================================

============================================================
Verifying embeddings...
============================================================

✅ Total messages with embeddings: 1,234
🎯 Embedding dimension: 384

📄 Sample message with embedding:
   Conversation: Python Data Pipeline Help
   Role: user
   Text: How do I create a data pipeline with dlt?
   Embedding dim: 384

📊 Message distribution by role:
   user: 617
   assistant: 615
   system: 2

============================================================
✅ Embedding verification complete!
============================================================
```

## Similarity Search

Once embeddings are loaded, you can perform semantic similarity search:

```sql
-- Find similar messages to a query
SELECT 
    conversation_id,
    role,
    text,
    1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM conversations
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

## Troubleshooting

### pgvector Extension Not Available

If you see "pgvector extension not available":
1. Use the pgvector Docker image: `docker-compose -f docker-compose-pgvector.yml up -d`
2. Or install pgvector manually (see above)
3. Or use `--no-embeddings` to test structure only

### Out of Memory

If embedding generation runs out of memory:
1. Reduce batch size: `--batch-size 16`
2. Use a smaller model: `--model sentence-transformers/paraphrase-MiniLM-L6-v2`
3. Process fewer conversations at once

### Model Download Slow

First run downloads the model (~100MB). Subsequent runs use cached model.

To pre-download:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

## Additional Resources

For more information on vector databases and embeddings:
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [sentence-transformers Documentation](https://www.sbert.net/)
- [dlt Documentation](https://dlthub.com/docs)

