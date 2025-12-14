"""FastAPI application for vector similarity search."""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dlt_embeddings.db import get_async_session
from dlt_embeddings.models import Conversation
from dlt_embeddings.query import VectorSearch

app = FastAPI(
    title="Vector Search API",
    description="API for semantic search over conversation embeddings",
    version="1.0.0",
)

# CORS middleware - allow all origins in development
# In production, configure specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global vector search instance
_vector_searcher: Optional[VectorSearch] = None


def get_vector_searcher() -> VectorSearch:
    """Get or create vector search instance."""
    global _vector_searcher
    if _vector_searcher is None:
        _vector_searcher = VectorSearch()
    return _vector_searcher


# Pydantic models for request/response
class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query text", min_length=1)
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    role: Optional[str] = Field(None, description="Filter by role (user/assistant/tool)")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation ID")
    metric: str = Field("cosine", description="Distance metric (cosine/l2/inner_product)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "query": "How do I install Python packages?",
                "limit": 10,
                "threshold": 0.3,
                "role": "assistant",
                "metric": "cosine",
            }
        }


class ConversationResponse(BaseModel):
    """Conversation response model."""

    message_id: str
    conversation_id: str
    role: str
    text: str
    similarity: float
    create_time: Optional[float] = None
    update_time: Optional[float] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class SearchResponse(BaseModel):
    """Search response model."""

    query: str
    results: List[ConversationResponse]
    total: int
    limit: int
    threshold: float


class StatsResponse(BaseModel):
    """Database statistics response model."""

    total_messages: int
    messages_with_embeddings: int
    role_distribution: dict[str, int]


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {"message": "Vector Search API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search(request: SearchRequest):
    """Search for similar conversations using vector similarity.

    Args:
        request: Search request with query and filters

    Returns:
        Search results with conversations and similarity scores
    """
    try:
        searcher = get_vector_searcher()

        async with get_async_session() as session:
            results = await searcher.search_async(
                session=session,
                query_text=request.query,
                limit=request.limit,
                similarity_threshold=request.threshold,
                role_filter=request.role,
                conversation_id_filter=request.conversation_id,
                distance_metric=request.metric,
            )

            # Convert to response models
            conversation_responses = []
            for conv in results:
                similarity = getattr(conv, "similarity", 0.0)
                conversation_responses.append(
                    ConversationResponse(
                        message_id=conv.message_id,
                        conversation_id=conv.conversation_id,
                        role=conv.role,
                        text=conv.text,
                        similarity=float(similarity),
                        create_time=conv.create_time,
                        update_time=conv.update_time,
                    )
                )

            return SearchResponse(
                query=request.query,
                results=conversation_responses,
                total=len(conversation_responses),
                limit=request.limit,
                threshold=request.threshold,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_get(
    query: str = Query(..., description="Search query text", min_length=1),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    threshold: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
    role: Optional[str] = Query(None, description="Filter by role (user/assistant/tool)"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    metric: str = Query("cosine", description="Distance metric (cosine/l2/inner_product)"),
):
    """Search for similar conversations (GET endpoint).

    Args:
        query: Search query text
        limit: Maximum number of results
        threshold: Minimum similarity threshold
        role: Filter by role
        conversation_id: Filter by conversation ID
        metric: Distance metric

    Returns:
        Search results
    """
    request = SearchRequest(
        query=query,
        limit=limit,
        threshold=threshold,
        role=role,
        conversation_id=conversation_id,
        metric=metric,
    )
    return await search(request)


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats():
    """Get database statistics.

    Returns:
        Database statistics including total messages and role distribution
    """
    try:
        from sqlalchemy import func, select

        async with get_async_session() as session:
            # Total count
            total_result = await session.execute(select(func.count(Conversation.message_id)))
            total = total_result.scalar() or 0

            # Count with embeddings
            embeddings_result = await session.execute(
                select(func.count(Conversation.message_id)).where(
                    Conversation.embedding.isnot(None)
                )
            )
            with_embeddings = embeddings_result.scalar() or 0

            # Role distribution
            role_result = await session.execute(
                select(Conversation.role, func.count(Conversation.message_id))
                .group_by(Conversation.role)
                .order_by(func.count(Conversation.message_id).desc())
            )
            role_distribution = {role: count for role, count in role_result.all()}

            return StatsResponse(
                total_messages=total,
                messages_with_embeddings=with_embeddings,
                role_distribution=role_distribution,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
