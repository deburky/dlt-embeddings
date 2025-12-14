# Vector Query Examples

This directory contains examples of using SQLAlchemy to query vector embeddings stored in PostgreSQL with pgvector.

## Features

- ✅ **SQLAlchemy ORM** - Type-safe database models
- ✅ **Async Support** - Use asyncpg for async queries
- ✅ **Vector Similarity Search** - Cosine, L2, and inner product distances
- ✅ **Flexible Filtering** - Filter by role, conversation_id, similarity threshold
- ✅ **CLI Interface** - Command-line tool for quick searches

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Run the Example

```bash
uv run python examples/vector_search_example.py
```

### 3. Use the CLI

```bash
# Search for similar conversations
dlt-embeddings-search "How do I install Python?"

# Search with filters
dlt-embeddings-search "database error" --role assistant --limit 5

# Use async mode
dlt-embeddings-search "Python tutorial" --async

# Show database statistics
dlt-embeddings-search stats
```

## Code Examples

### Sync Search

```python
from dlt_embeddings.db import get_sync_session
from dlt_embeddings.query import search_conversations_sync

with get_sync_session() as session:
    results = search_conversations_sync(
        session=session,
        query_text="How do I use SQLAlchemy?",
        limit=10,
        similarity_threshold=0.3,
        role_filter="assistant",
    )

    for conv in results:
        print(f"Similarity: {conv.similarity:.4f}")
        print(f"Text: {conv.text}")
```

### Async Search

```python
import asyncio
from dlt_embeddings.db import get_async_session
from dlt_embeddings.query import search_conversations_async

async def search():
    async with get_async_session() as session:
        results = await search_conversations_async(
            session=session,
            query_text="Python async programming",
            limit=10,
        )
        return results

results = asyncio.run(search())
```

### Using VectorSearch Class

```python
from dlt_embeddings.query import VectorSearch
from dlt_embeddings.db import get_sync_session

searcher = VectorSearch(model_name="sentence-transformers/all-MiniLM-L6-v2")

with get_sync_session() as session:
    results = searcher.search_sync(
        session=session,
        query_text="machine learning",
        limit=5,
        distance_metric="cosine",  # or "l2" or "inner_product"
        similarity_threshold=0.5,
    )
```

### Direct SQLAlchemy Query

```python
from sqlalchemy import select
from pgvector.sqlalchemy import Vector
from dlt_embeddings.db import get_sync_session
from dlt_embeddings.models import Conversation
import numpy as np

# Encode your query
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
query_embedding = model.encode("your query text")

with get_sync_session() as session:
    # Cosine similarity search
    query = (
        select(Conversation)
        .add_columns(
            (1 - Conversation.embedding.cosine_distance(query_embedding)).label("similarity")
        )
        .where(Conversation.embedding.isnot(None))
        .order_by("similarity".desc())
        .limit(10)
    )

    results = session.execute(query).all()
    for row in results:
        conv, similarity = row
        print(f"Similarity: {similarity:.4f}, Text: {conv.text[:100]}")
```

## Distance Metrics

- **cosine** (default): Cosine distance/similarity. Best for semantic similarity.
- **l2**: Euclidean distance. Lower values = more similar.
- **inner_product**: Inner product. Higher values = more similar.

## Environment Variables

The database connection can be configured via environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DATABASE=dlt_dev
export POSTGRES_USER=dlt_user
export POSTGRES_PASSWORD=dlt_password
```

Or pass them directly to `get_database_url()`.

## Performance Tips

1. **Use async for concurrent queries** - Better for multiple simultaneous searches
2. **Index your embeddings** - pgvector automatically creates indexes for vector columns
3. **Adjust similarity threshold** - Higher thresholds = faster queries (fewer results)
4. **Use role/conversation filters** - Reduces search space significantly



