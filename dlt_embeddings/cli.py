"""CLI interface for vector similarity search."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dlt_embeddings.db import get_async_session, get_sync_session
from dlt_embeddings.query import VectorSearch

app = typer.Typer(help="Vector similarity search for conversations")
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query text"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results"),
    threshold: float = typer.Option(
        0.0, "--threshold", "-t", help="Minimum similarity threshold (0.0-1.0)"
    ),
    role: Optional[str] = typer.Option(
        None, "--role", "-r", help="Filter by role (user/assistant/tool)"
    ),
    conversation_id: Optional[str] = typer.Option(
        None, "--conversation", "-c", help="Filter by conversation ID"
    ),
    metric: str = typer.Option(
        "cosine", "--metric", "-m", help="Distance metric (cosine/l2/inner_product)"
    ),
    model: str = typer.Option(
        "sentence-transformers/all-MiniLM-L6-v2",
        "--model",
        help="Sentence transformer model name",
    ),
    async_mode: bool = typer.Option(False, "--async", help="Use async database connection"),
):
    """Search for similar conversations using vector similarity."""
    console.print(f"[bold blue]Searching for:[/bold blue] {query}")
    console.print(f"[dim]Model: {model}, Limit: {limit}, Threshold: {threshold}[/dim]\n")

    if async_mode:
        asyncio.run(_search_async(query, limit, threshold, role, conversation_id, metric, model))
    else:
        _search_sync(query, limit, threshold, role, conversation_id, metric, model)


def _search_sync(
    query: str,
    limit: int,
    threshold: float,
    role: Optional[str],
    conversation_id: Optional[str],
    metric: str,
    model: str,
):
    """Synchronous search."""
    searcher = VectorSearch(model_name=model)

    with get_sync_session() as session:
        results = searcher.search_sync(
            session=session,
            query_text=query,
            limit=limit,
            similarity_threshold=threshold,
            role_filter=role,
            conversation_id_filter=conversation_id,
            distance_metric=metric,
        )

        _display_results(results, query)


async def _search_async(
    query: str,
    limit: int,
    threshold: float,
    role: Optional[str],
    conversation_id: Optional[str],
    metric: str,
    model: str,
):
    """Asynchronous search."""
    searcher = VectorSearch(model_name=model)

    async with get_async_session() as session:
        results = await searcher.search_async(
            session=session,
            query_text=query,
            limit=limit,
            similarity_threshold=threshold,
            role_filter=role,
            conversation_id_filter=conversation_id,
            distance_metric=metric,
        )

        _display_results(results, query)


def _display_results(results, query: str):
    """Display search results in a formatted table."""
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"Search Results for: {query}")
    table.add_column("Similarity", justify="right", style="cyan")
    table.add_column("Role", style="magenta")
    table.add_column("Conversation ID", style="green")
    table.add_column("Text", style="white", overflow="fold")

    for conv in results:
        similarity = getattr(conv, "similarity", 0.0)
        text_preview = conv.text[:200] + "..." if len(conv.text) > 200 else conv.text
        table.add_row(
            f"{similarity:.4f}",
            conv.role,
            (
                conv.conversation_id[:30] + "..."
                if len(conv.conversation_id) > 30
                else conv.conversation_id
            ),
            text_preview,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} result(s)[/dim]")


@app.command()
def stats():
    """Show database statistics."""
    with get_sync_session() as session:
        from sqlalchemy import func, select
        from dlt_embeddings.models import Conversation

        # Total count
        total = session.scalar(select(func.count(Conversation.message_id)))
        console.print(f"[bold]Total messages:[/bold] {total}")

        # Count by role
        role_counts = session.execute(
            select(Conversation.role, func.count(Conversation.message_id))
            .group_by(Conversation.role)
            .order_by(func.count(Conversation.message_id).desc())
        ).all()

        table = Table(title="Messages by Role")
        table.add_column("Role", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for role, count in role_counts:
            table.add_row(role, str(count))

        console.print(table)

        # Count with embeddings
        with_embeddings = session.scalar(
            select(func.count(Conversation.message_id)).where(Conversation.embedding.isnot(None))
        )
        console.print(f"\n[bold]Messages with embeddings:[/bold] {with_embeddings}")


if __name__ == "__main__":
    app()
