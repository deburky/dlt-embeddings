"""Example: Using SQLAlchemy to query vectors with pgvector.

This example demonstrates:
1. Sync vector similarity search
2. Async vector similarity search
3. Filtering by role and conversation_id
4. Different distance metrics
"""

import asyncio

from dlt_embeddings.db import get_async_session, get_sync_session
from dlt_embeddings.query import VectorSearch, search_conversations_async, search_conversations_sync


def example_sync_search():
    """Example of synchronous vector search."""
    print("=" * 60)
    print("Example 1: Synchronous Vector Search")
    print("=" * 60)

    query_text = "How do I install Python packages?"

    with get_sync_session() as session:
        # Simple search
        results = search_conversations_sync(
            session=session,
            query_text=query_text,
            limit=5,
            similarity_threshold=0.3,
        )

        print(f"\nFound {len(results)} results for: '{query_text}'\n")
        for i, conv in enumerate(results, 1):
            similarity = getattr(conv, "similarity", 0.0)
            print(f"{i}. [Similarity: {similarity:.4f}] {conv.role}")
            print(f"   Conversation: {conv.conversation_id}")
            print(f"   Text: {conv.text[:150]}...")
            print()

        # Search with filters
        print("\n" + "-" * 60)
        print("Example 2: Search with Role Filter (assistant only)")
        print("-" * 60)

        results = search_conversations_sync(
            session=session,
            query_text=query_text,
            limit=3,
            role_filter="assistant",
            similarity_threshold=0.3,
        )

        print(f"\nFound {len(results)} assistant responses:\n")
        for i, conv in enumerate(results, 1):
            similarity = getattr(conv, "similarity", 0.0)
            print(f"{i}. [Similarity: {similarity:.4f}]")
            print(f"   {conv.text[:200]}...")
            print()


async def example_async_search():
    """Example of asynchronous vector search."""
    print("=" * 60)
    print("Example 3: Asynchronous Vector Search")
    print("=" * 60)

    query_text = "database connection error"

    async with get_async_session() as session:
        # Using the convenience function
        results = await search_conversations_async(
            session=session,
            query_text=query_text,
            limit=5,
            similarity_threshold=0.3,
        )

        print(f"\nFound {len(results)} results for: '{query_text}'\n")
        for i, conv in enumerate(results, 1):
            similarity = getattr(conv, "similarity", 0.0)
            print(f"{i}. [Similarity: {similarity:.4f}] {conv.role}")
            print(f"   {conv.text[:150]}...")
            print()

        # Using VectorSearch class directly
        print("\n" + "-" * 60)
        print("Example 4: Using VectorSearch Class with L2 Distance")
        print("-" * 60)

        searcher = VectorSearch(model_name="sentence-transformers/all-MiniLM-L6-v2")
        results = await searcher.search_async(
            session=session,
            query_text=query_text,
            limit=3,
            distance_metric="l2",
            similarity_threshold=0.0,
        )

        print(f"\nFound {len(results)} results using L2 distance:\n")
        for i, conv in enumerate(results, 1):
            similarity = getattr(conv, "similarity", 0.0)
            print(f"{i}. [Score: {similarity:.4f}] {conv.role}")
            print(f"   {conv.text[:150]}...")
            print()


def example_conversation_context():
    """Example of searching within a specific conversation."""
    print("=" * 60)
    print("Example 5: Search Within Specific Conversation")
    print("=" * 60)

    # First, find a conversation_id
    with get_sync_session() as session:
        from sqlalchemy import select
        from dlt_embeddings.models import Conversation

        # Get a random conversation_id
        result = session.execute(select(Conversation.conversation_id).distinct().limit(1)).first()

        if result:
            conversation_id = result[0]
            print(f"\nSearching within conversation: {conversation_id}\n")

            query_text = "error"
            results = search_conversations_sync(
                session=session,
                query_text=query_text,
                limit=5,
                conversation_id_filter=conversation_id,
                similarity_threshold=0.2,
            )

            print(f"Found {len(results)} messages about '{query_text}':\n")
            for i, conv in enumerate(results, 1):
                similarity = getattr(conv, "similarity", 0.0)
                print(f"{i}. [{conv.role}] [Similarity: {similarity:.4f}]")
                print(f"   {conv.text[:200]}...")
                print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Vector Similarity Search Examples")
    print("=" * 60 + "\n")

    # Sync examples
    example_sync_search()
    example_conversation_context()

    # Async examples
    asyncio.run(example_async_search())

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
