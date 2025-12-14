"""Vector similarity search functions using SQLAlchemy."""

from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from dlt_embeddings.models import Conversation


class VectorSearch:
    """Vector similarity search using SQLAlchemy and pgvector."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """Initialize vector search with a sentence transformer model.

        Args:
            model_name: Name of the sentence transformer model
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto)
        """
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name

    def encode_query(self, query_text: str) -> np.ndarray:
        """Encode a query text into an embedding vector.

        Args:
            query_text: Text to encode

        Returns:
            Numpy array of the embedding vector
        """
        return self.model.encode(query_text, convert_to_numpy=True)

    def search_sync(
        self,
        session: Session,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.0,
        role_filter: Optional[str] = None,
        conversation_id_filter: Optional[str] = None,
        distance_metric: str = "cosine",
    ) -> List[Conversation]:
        """Search for similar conversations using sync session.

        Args:
            session: SQLAlchemy sync session
            query_text: Query text to search for
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            role_filter: Filter by role (e.g., 'user', 'assistant')
            conversation_id_filter: Filter by conversation_id
            distance_metric: Distance metric ('cosine', 'l2', or 'inner_product')

        Returns:
            List of Conversation objects sorted by similarity (most similar first)
        """
        # Encode query
        query_embedding = self.encode_query(query_text)

        # Build query
        query = select(Conversation)

        # Apply filters
        if role_filter:
            query = query.where(Conversation.role == role_filter)
        if conversation_id_filter:
            query = query.where(Conversation.conversation_id == conversation_id_filter)

        # Add vector similarity search
        if distance_metric == "cosine":
            # Cosine distance: 1 - cosine similarity
            # We want high similarity, so we order by distance ASC
            distance_expr = Conversation.embedding.cosine_distance(query_embedding)
            similarity_expr = 1 - distance_expr  # Convert distance to similarity
        elif distance_metric == "l2":
            # L2 distance: lower is better
            distance_expr = Conversation.embedding.l2_distance(query_embedding)
            # For L2, we'll use negative distance as similarity proxy
            similarity_expr = -distance_expr
        elif distance_metric == "inner_product":
            # Inner product: higher is better
            similarity_expr = Conversation.embedding.max_inner_product(query_embedding)
        else:
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        # Build subquery with similarity calculation
        subquery = select(Conversation.message_id, similarity_expr.label("similarity")).where(
            Conversation.embedding.isnot(None)
        )

        # Apply role and conversation_id filters to subquery
        if role_filter:
            subquery = subquery.where(Conversation.role == role_filter)
        if conversation_id_filter:
            subquery = subquery.where(Conversation.conversation_id == conversation_id_filter)

        # Create subquery alias
        subquery_alias = subquery.subquery()

        # Main query: join Conversation with subquery and filter by similarity threshold
        main_query = (
            select(Conversation, subquery_alias.c.similarity)
            .join(subquery_alias, Conversation.message_id == subquery_alias.c.message_id)
            .where(subquery_alias.c.similarity >= similarity_threshold)
            .order_by(subquery_alias.c.similarity.desc())
            .limit(limit)
        )

        # Execute query
        results = session.execute(main_query).all()

        # Extract conversations and add similarity scores
        conversations = []
        for row in results:
            conv = row[0]  # Conversation object
            similarity = float(row[1])  # Similarity score
            conv.similarity = similarity  # Add similarity as attribute
            conversations.append(conv)

        return conversations

    async def search_async(
        self,
        session: AsyncSession,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.0,
        role_filter: Optional[str] = None,
        conversation_id_filter: Optional[str] = None,
        distance_metric: str = "cosine",
    ) -> List[Conversation]:
        """Search for similar conversations using async session.

        Args:
            session: SQLAlchemy async session
            query_text: Query text to search for
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            role_filter: Filter by role (e.g., 'user', 'assistant')
            conversation_id_filter: Filter by conversation_id
            distance_metric: Distance metric ('cosine', 'l2', or 'inner_product')

        Returns:
            List of Conversation objects sorted by similarity (most similar first)
        """
        # Encode query
        query_embedding = self.encode_query(query_text)

        # Build query
        query = select(Conversation)

        # Apply filters
        if role_filter:
            query = query.where(Conversation.role == role_filter)
        if conversation_id_filter:
            query = query.where(Conversation.conversation_id == conversation_id_filter)

        # Add vector similarity search
        if distance_metric == "cosine":
            distance_expr = Conversation.embedding.cosine_distance(query_embedding)
            similarity_expr = 1 - distance_expr
        elif distance_metric == "l2":
            distance_expr = Conversation.embedding.l2_distance(query_embedding)
            similarity_expr = -distance_expr
        elif distance_metric == "inner_product":
            similarity_expr = Conversation.embedding.max_inner_product(query_embedding)
        else:
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        # Build subquery with similarity calculation
        subquery = select(Conversation.message_id, similarity_expr.label("similarity")).where(
            Conversation.embedding.isnot(None)
        )

        # Apply role and conversation_id filters to subquery
        if role_filter:
            subquery = subquery.where(Conversation.role == role_filter)
        if conversation_id_filter:
            subquery = subquery.where(Conversation.conversation_id == conversation_id_filter)

        # Create subquery alias
        subquery_alias = subquery.subquery()

        # Main query: join Conversation with subquery and filter by similarity threshold
        main_query = (
            select(Conversation, subquery_alias.c.similarity)
            .join(subquery_alias, Conversation.message_id == subquery_alias.c.message_id)
            .where(subquery_alias.c.similarity >= similarity_threshold)
            .order_by(subquery_alias.c.similarity.desc())
            .limit(limit)
        )

        # Execute query
        result = await session.execute(main_query)
        rows = result.all()

        # Extract conversations and add similarity scores
        conversations = []
        for row in rows:
            conv = row[0]
            similarity = float(row[1])
            conv.similarity = similarity
            conversations.append(conv)

        return conversations


def search_conversations_sync(
    session: Session,
    query_text: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    limit: int = 10,
    similarity_threshold: float = 0.0,
    role_filter: Optional[str] = None,
    conversation_id_filter: Optional[str] = None,
    distance_metric: str = "cosine",
) -> List[Conversation]:
    """Convenience function for sync vector search.

    Args:
        session: SQLAlchemy sync session
        query_text: Query text to search for
        model_name: Sentence transformer model name
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score
        role_filter: Filter by role
        conversation_id_filter: Filter by conversation_id
        distance_metric: Distance metric ('cosine', 'l2', or 'inner_product')

    Returns:
        List of Conversation objects sorted by similarity
    """
    searcher = VectorSearch(model_name=model_name)
    return searcher.search_sync(
        session=session,
        query_text=query_text,
        limit=limit,
        similarity_threshold=similarity_threshold,
        role_filter=role_filter,
        conversation_id_filter=conversation_id_filter,
        distance_metric=distance_metric,
    )


async def search_conversations_async(
    session: AsyncSession,
    query_text: str,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    limit: int = 10,
    similarity_threshold: float = 0.0,
    role_filter: Optional[str] = None,
    conversation_id_filter: Optional[str] = None,
    distance_metric: str = "cosine",
) -> List[Conversation]:
    """Convenience function for async vector search.

    Args:
        session: SQLAlchemy async session
        query_text: Query text to search for
        model_name: Sentence transformer model name
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score
        role_filter: Filter by role
        conversation_id_filter: Filter by conversation_id
        distance_metric: Distance metric ('cosine', 'l2', or 'inner_product')

    Returns:
        List of Conversation objects sorted by similarity
    """
    searcher = VectorSearch(model_name=model_name)
    return await searcher.search_async(
        session=session,
        query_text=query_text,
        limit=limit,
        similarity_threshold=similarity_threshold,
        role_filter=role_filter,
        conversation_id_filter=conversation_id_filter,
        distance_metric=distance_metric,
    )
