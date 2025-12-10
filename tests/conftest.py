"""Pytest configuration for dlt-embeddings tests."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_conversation():
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "mapping": {
            "node1": {
                "message": {
                    "id": "msg1",
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello, how are you?"]},
                    "create_time": 1234567890,
                    "update_time": 1234567890,
                }
            },
            "node2": {
                "message": {
                    "id": "msg2",
                    "author": {"role": "assistant"},
                    "content": {"parts": ["I'm doing well, thank you!"]},
                    "create_time": 1234567891,
                    "update_time": 1234567891,
                }
            },
        },
    }
