"""Source for loading conversations with embeddings generation.

This source loads conversations from JSON, extracts text content from messages,
generates embeddings using sentence-transformers, and prepares data for PostgreSQL with pgvector.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import dlt
from sentence_transformers import SentenceTransformer


def extract_conversation_text(conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract text content from conversation messages.
    
    Args:
        conversation: Conversation object with title, mapping, etc.
        
    Returns:
        List of message dictionaries with extracted text
    """
    messages = []
    mapping = conversation.get("mapping", {})
    
    for node_id, node in mapping.items():
        message = node.get("message")
        if not message:
            continue
            
        # Extract message content
        content = message.get("content", {})
        if not content:
            continue
            
        # Get text parts
        parts = content.get("parts", [])
        if not parts:
            continue
            
        # Combine all text parts
        text = " ".join(str(part) for part in parts if part)
        if not text or text.strip() == "":
            continue
            
        # Extract metadata
        author = message.get("author", {})
        role = author.get("role", "unknown")
        
        messages.append({
            "conversation_id": conversation.get("title", "unknown"),
            "message_id": message.get("id", node_id),
            "role": role,
            "text": text.strip(),
            "create_time": message.get("create_time"),
            "update_time": message.get("update_time"),
        })
    
    return messages


@dlt.source
def conversations_with_embeddings(
    file_path: Union[str, Path],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    table_name: str = "conversations",
    write_disposition: str = "replace",
    batch_size: int = 32,
    device: Optional[str] = None,
) -> Any:
    """
    Load conversations from JSON and generate embeddings for message text.
    
    Args:
        file_path: Path to conversations.json file
        model_name: Sentence-transformers model to use for embeddings
        table_name: Target table name
        write_disposition: Write disposition ('replace' or 'append')
        batch_size: Batch size for embedding generation
        device: Device to use ('cpu', 'cuda', 'mps', or None for auto)
        
    Returns:
        dlt source that yields conversation messages with embeddings
        
    Example:
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
            table_name="conversations"
        )
        
        pipeline.run(source)
        ```
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Conversations file not found: {file_path}")
    
    # Load the sentence-transformers model
    print(f"📥 Loading model: {model_name}")
    model = SentenceTransformer(model_name, device=device)
    print(f"✅ Model loaded successfully")
    
    @dlt.resource(
        name=table_name, 
        write_disposition=write_disposition,
        columns={
            "embedding": {
                "data_type": "text",  # Will be converted to vector type
                "nullable": True
            }
        },
        max_table_nesting=0  # Prevent creation of child tables
    )
    def load_conversations() -> Iterator[Dict[str, Any]]:
        """Load conversations and generate embeddings."""
        print(f"📖 Reading conversations from: {file_path}")
        
        # Read the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            # Handle both array and newline-delimited JSON
            content = f.read().strip()
            if content.startswith("["):
                # JSON array
                conversations = json.loads(content)
            else:
                # Newline-delimited JSON
                conversations = [json.loads(line) for line in content.split("\n") if line.strip()]
        
        print(f"📊 Found {len(conversations)} conversations")
        
        # Extract all messages from all conversations
        all_messages = []
        for conversation in conversations:
            messages = extract_conversation_text(conversation)
            all_messages.extend(messages)
        
        print(f"💬 Extracted {len(all_messages)} messages")
        
        if not all_messages:
            print("⚠️  No messages found in conversations")
            return
        
        # Generate embeddings in batches
        print(f"🤖 Generating embeddings (batch_size={batch_size})...")
        texts = [msg["text"] for msg in all_messages]
        
        # Generate embeddings for all texts
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        embedding_dim = embeddings.shape[1]
        print(f"✅ Generated {len(embeddings)} embeddings with dimension {embedding_dim}")
        
        # Yield messages with embeddings in pgvector format
        for message, embedding in zip(all_messages, embeddings):
            # Convert to pgvector format: [val1,val2,val3]
            embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
            record = {
                **message,
                "embedding": embedding_str,  # pgvector format
            }
            yield record
    
    return load_conversations


@dlt.source
def conversations_simple(
    file_path: Union[str, Path],
    table_name: str = "conversations_raw",
    write_disposition: str = "replace",
) -> Any:
    """
    Load conversations from JSON without embeddings (for testing structure).
    
    Args:
        file_path: Path to conversations.json file
        table_name: Target table name
        write_disposition: Write disposition ('replace' or 'append')
        
    Returns:
        dlt source that yields conversation messages without embeddings
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Conversations file not found: {file_path}")
    
    @dlt.resource(name=table_name, write_disposition=write_disposition)
    def load_conversations() -> Iterator[Dict[str, Any]]:
        """Load conversations without embeddings."""
        print(f"📖 Reading conversations from: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("["):
                conversations = json.loads(content)
            else:
                conversations = [json.loads(line) for line in content.split("\n") if line.strip()]
        
        print(f"📊 Found {len(conversations)} conversations")
        
        # Extract all messages
        all_messages = []
        for conversation in conversations:
            messages = extract_conversation_text(conversation)
            all_messages.extend(messages)
        
        print(f"💬 Extracted {len(all_messages)} messages")
        
        # Yield messages without embeddings
        for message in all_messages:
            yield message
    
    return load_conversations


