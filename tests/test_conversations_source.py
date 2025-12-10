"""Tests for conversations embeddings source."""

from dlt_embeddings.sources.conversations_embeddings_source import (
    extract_conversation_text,
)


def test_extract_conversation_text(sample_conversation):
    """Test extracting text from conversation."""
    messages = extract_conversation_text(sample_conversation)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["text"] == "Hello, how are you?"
    assert messages[0]["conversation_id"] == "Test Conversation"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["text"] == "I'm doing well, thank you!"


def test_extract_conversation_text_empty():
    """Test extracting text from empty conversation."""
    conversation = {"title": "Empty", "mapping": {}}
    messages = extract_conversation_text(conversation)

    assert len(messages) == 0


def test_extract_conversation_text_no_content():
    """Test extracting text from conversation with no content."""
    conversation = {
        "title": "No Content",
        "mapping": {"node1": {"message": {"id": "msg1", "content": {}}}},
    }
    messages = extract_conversation_text(conversation)

    assert len(messages) == 0


def test_extract_conversation_text_empty_parts():
    """Test extracting text from conversation with empty parts."""
    conversation = {
        "title": "Empty Parts",
        "mapping": {
            "node1": {
                "message": {
                    "id": "msg1",
                    "author": {"role": "user"},
                    "content": {"parts": []},
                }
            }
        },
    }
    messages = extract_conversation_text(conversation)

    assert len(messages) == 0


def test_extract_conversation_text_multiple_parts():
    """Test extracting text from conversation with multiple parts."""
    conversation = {
        "title": "Multi Part",
        "mapping": {
            "node1": {
                "message": {
                    "id": "msg1",
                    "author": {"role": "user"},
                    "content": {"parts": ["Hello", "World"]},
                    "create_time": 1234567890,
                }
            }
        },
    }
    messages = extract_conversation_text(conversation)

    assert len(messages) == 1
    assert messages[0]["text"] == "Hello World"
