"""
dlt-embeddings: Data loading pipelines with embeddings support.

This package provides pipelines for loading conversations with embeddings
into PostgreSQL with pgvector support.
"""

from typing import Any

import dlt

# Conversations with embeddings
from dlt_embeddings.sources.conversations_embeddings_source import (
    conversations_with_embeddings,
    conversations_simple,
)

__version__ = "0.1.0"


def config() -> Any:
    """
    Get the current dlt configuration.

    Returns:
        Configuration object with current profile and settings
    """
    return dlt.config


def runner() -> Any:
    """
    Get the pipeline runner for executing dlt pipelines.

    Returns:
        Runner object for pipeline execution
    """
    return dlt.pipeline


def catalog() -> Any:
    """
    Get the data catalog for accessing loaded datasets.

    Returns:
        Catalog object for dataset access
    """

    # This would integrate with dlt's catalog functionality
    # For now, return a simple accessor
    class Catalog:
        def dataset(self, name: str):
            """Get a dataset by name."""
            return dlt.pipeline(pipeline_name=name)

    return Catalog()


def create_pipeline(
    pipeline_name: str, destination: str = "redshift", dataset_name: str = "stg", **kwargs
) -> dlt.Pipeline:
    """
    Create a dlt pipeline with standard configuration.

    Args:
        pipeline_name: Name of the pipeline
        destination: Destination type (default: redshift)
        dataset_name: Target schema/dataset name (default: stg)
        **kwargs: Additional pipeline configuration

    Returns:
        Configured dlt Pipeline object
    """
    return dlt.pipeline(
        pipeline_name=pipeline_name, destination=destination, dataset_name=dataset_name, **kwargs
    )


__all__ = [
    "config",
    "runner",
    "catalog",
    "create_pipeline",
    "conversations_with_embeddings",
    "conversations_simple",
]
