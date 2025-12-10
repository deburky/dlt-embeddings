#!/usr/bin/env python3
"""Test pipeline: Load conversations with embeddings into PostgreSQL with pgvector.

This script:
1. Loads conversations from JSON
2. Extracts text from messages
3. Generates embeddings using sentence-transformers
4. Stores in PostgreSQL with pgvector extension
"""

import argparse
import os
import sys

import dlt
import psycopg2


def setup_postgres_env(
    host: str = "localhost",
    port: int = 5432,
    database: str = "dlt_dev",
    username: str = "dlt_user",
    password: str = "dlt_password",
):
    """Configure PostgreSQL connection via environment variables."""
    os.environ["DESTINATION__POSTGRES__CREDENTIALS__HOST"] = host
    os.environ["DESTINATION__POSTGRES__CREDENTIALS__PORT"] = str(port)
    os.environ["DESTINATION__POSTGRES__CREDENTIALS__DATABASE"] = database
    os.environ["DESTINATION__POSTGRES__CREDENTIALS__USERNAME"] = username
    os.environ["DESTINATION__POSTGRES__CREDENTIALS__PASSWORD"] = password


def setup_pgvector(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    schema: str = "dlt_dev",
    require_pgvector: bool = True,
):  # sourcery skip: extract-method, remove-redundant-if
    """Setup pgvector extension and create necessary schema."""
    print("Setting up PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Try to create pgvector extension
        if require_pgvector:
            print("📦 Creating pgvector extension...")
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ pgvector extension ready")
            except Exception as e:
                print(f"⚠️  pgvector extension not available: {e}")
                if require_pgvector:
                    print("\n💡 To use embeddings, you need PostgreSQL with pgvector:")
                    print("cd infrastructure/localstack")
                    print("docker-compose -f docker-compose-pgvector.yml up -d")
                    cur.close()
                    conn.close()
                    return False
        else:
            print("ℹ️  Skipping pgvector setup (not required for structure test)")

        # Create schema if it doesn't exist
        print(f"📁 Creating schema '{schema}'...")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        print(f"✅ Schema '{schema}' ready")

        cur.close()
        conn.close()

        print("✅ PostgreSQL setup complete!")
        return True

    except Exception as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        return False


def create_pipeline(pipeline_name: str = "conversations_embeddings", dataset_name: str = "dlt_dev"):
    """Create a dlt pipeline with PostgreSQL destination."""
    import dlt.destinations

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.postgres(),
        dataset_name=dataset_name,
    )
    return pipeline


def verify_embeddings(pipeline: dlt.Pipeline, table_name: str, has_embeddings: bool = True):
    # sourcery skip: extract-duplicate-method, use-fstring-for-concatenation
    """Verify that data was stored correctly."""
    print("Verifying loaded data...")

    try:
        with pipeline.sql_client() as client:
            # Get row count
            with client.execute_query(f"SELECT COUNT(*) as count FROM {table_name}") as cursor:
                result = cursor.fetchone()
                row_count = result[0] if result else 0
                if has_embeddings:
                    print(f"\n✅ Total messages with embeddings: {row_count}")
                else:
                    print(f"\n✅ Total messages loaded: {row_count}")

            if row_count == 0:
                print("⚠️  Warning: No data was loaded!")
                return

            # Check embedding dimension (only if embeddings were generated)
            if has_embeddings:
                try:
                    with client.execute_query(
                        f"SELECT array_length(embedding, 1) as dim FROM {table_name} LIMIT 1"
                    ) as cursor:
                        if result := cursor.fetchone():
                            dim = result[0]
                            print(f"🎯 Embedding dimension: {dim}")
                except Exception:
                    print("⚠️  No embedding column found (expected for --no-embeddings mode)")

            # Get sample message
            print("\n📄 Sample message:")
            if has_embeddings:
                # Check if embedding column exists and get its dimension
                try:
                    query = (
                        f"SELECT conversation_id, role, text, array_length(embedding, 1) as dim "
                        f"FROM {table_name} LIMIT 1"
                    )
                    with client.execute_query(query) as cursor:
                        if row := cursor.fetchone():
                            conv_id, role, text, dim = row
                            text_preview = text[:100] + "..." if len(text) > 100 else text
                            print(f"Conversation: {conv_id}")
                            print(f"Role: {role}")
                            print(f"Text: {text_preview}")
                            print(f"Embedding dim: {dim}")
                except Exception:
                    # Fallback if embedding column doesn't exist
                    query = f"SELECT conversation_id, role, text FROM {table_name} LIMIT 1"
                    with client.execute_query(query) as cursor:
                        if row := cursor.fetchone():
                            conv_id, role, text = row
                            text_preview = text[:100] + "..." if len(text) > 100 else text
                            print(f"Conversation: {conv_id}")
                            print(f"Role: {role}")
                            print(f"Text: {text_preview}")
            else:
                query = f"SELECT conversation_id, role, text FROM {table_name} LIMIT 1"
                with client.execute_query(query) as cursor:
                    if row := cursor.fetchone():
                        conv_id, role, text = row
                        text_preview = text[:100] + "..." if len(text) > 100 else text
                        print(f"Conversation: {conv_id}")
                        print(f"Role: {role}")
                        print(f"Text: {text_preview}")

            # Show role distribution
            print("\n📊 Message distribution by role:")
            with client.execute_query(
                f"SELECT role, COUNT(*) as count FROM {table_name} GROUP BY role ORDER BY count DESC"
            ) as cursor:
                rows = cursor.fetchall()
                for row in rows:
                    role, count = row
                    print(f"{role}: {count}")

            print("✅ Data verification complete!")

    except Exception as e:
        print(f"\n❌ Error verifying data: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main function to run the test pipeline."""
    parser = argparse.ArgumentParser(
        description="Test pipeline: Load conversations with embeddings into PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load conversations with embeddings
  python test_conversations_embeddings.py test_data/conversations.json

  # Use different model
  python test_conversations_embeddings.py test_data/conversations.json --model sentence-transformers/paraphrase-MiniLM-L6-v2

  # Custom table and schema
  python test_conversations_embeddings.py test_data/conversations.json --table my_conversations --schema my_schema

  # Without embeddings (structure test only)
  python test_conversations_embeddings.py test_data/conversations.json --no-embeddings
        """,
    )

    parser.add_argument(
        "conversations_file",
        type=str,
        help="Path to conversations.json file",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="conversations",
        help="Target table name (default: conversations)",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="dlt_dev",
        help="Target schema/dataset name (default: dlt_dev)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Sentence-transformers model name (default: all-MiniLM-L6-v2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for embedding generation (default: 32)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device for model ('cpu', 'cuda', 'mps', default: auto)",
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Load conversations without generating embeddings (for quick structure testing only)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="PostgreSQL host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5432,
        help="PostgreSQL port (default: 5432)",
    )
    parser.add_argument(
        "--database",
        type=str,
        default="dlt_dev",
        help="PostgreSQL database name (default: dlt_dev)",
    )
    parser.add_argument(
        "--username",
        type=str,
        default="dlt_user",
        help="PostgreSQL username (default: dlt_user)",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="dlt_password",
        help="PostgreSQL password (default: dlt_password)",
    )

    args = parser.parse_args()

    print("Conversations to PostgreSQL with Embeddings")
    print(f"Conversations file: {args.conversations_file}")
    print(f"Table: {args.table}")
    print(f"Schema: {args.schema}")
    print(f"PostgreSQL: {args.host}:{args.port}/{args.database}")
    if not args.no_embeddings:
        print(f"Model: {args.model}")
        print(f"Batch size: {args.batch_size}")
        print(f"Device: {args.device or 'auto'}")
    else:
        print("Mode: Structure test (no embeddings)")
    print()

    try:
        # Setup PostgreSQL connection
        setup_postgres_env(
            host=args.host,
            port=args.port,
            database=args.database,
            username=args.username,
            password=args.password,
        )

        # Setup pgvector extension (only required if generating embeddings)
        if not setup_pgvector(
            host=args.host,
            port=args.port,
            database=args.database,
            username=args.username,
            password=args.password,
            schema=args.schema,
            require_pgvector=not args.no_embeddings,
        ):
            return 1

        # Create pipeline
        pipeline = create_pipeline(
            pipeline_name="conversations_embeddings",
            dataset_name=args.schema,
        )

        # Load conversations
        if args.no_embeddings:
            from dlt_embeddings.sources.conversations_embeddings_source import conversations_simple

            print("\nLoading conversations without embeddings...")
            source = conversations_simple(
                file_path=args.conversations_file,
                table_name=args.table,
            )
        else:
            from dlt_embeddings.sources.conversations_embeddings_source import (
                conversations_with_embeddings,
            )

            print("\nLoading conversations with embeddings...")
            source = conversations_with_embeddings(
                file_path=args.conversations_file,
                model_name=args.model,
                table_name=args.table,
                batch_size=args.batch_size,
                device=args.device,
            )

        print("\nRunning pipeline...")
        load_info = pipeline.run(source)

        print("✅ Pipeline completed successfully!")
        print(f"Load ID: {load_info.loads_ids[0] if load_info.loads_ids else 'N/A'}")

        # Convert embedding column to vector type if embeddings were generated
        if not args.no_embeddings:
            print("\n🔄 Converting embedding column to vector type...")
            with pipeline.sql_client() as client:
                # First, get the dimension of the embeddings
                with client.execute_query(
                    f"SELECT embedding FROM {args.table} WHERE embedding IS NOT NULL LIMIT 1"
                ) as cursor:
                    row = cursor.fetchone()
                    if row and row[0]:
                        # Count the dimension from the string format [val1,val2,...]
                        embedding_str = row[0]
                        dim = len(embedding_str.strip("[]").split(","))
                        print(f"Detected embedding dimension: {dim}")

                        # Add a new vector column
                        client.execute_sql(
                            f"ALTER TABLE {args.table} ADD COLUMN IF NOT EXISTS embedding_vector vector({dim})"
                        )

                        # Convert text to vector
                        client.execute_sql(
                            f"UPDATE {args.table} SET embedding_vector = embedding::vector WHERE embedding IS NOT NULL"
                        )

                        # Drop the old text column and rename vector column
                        client.execute_sql(
                            f"ALTER TABLE {args.table} DROP COLUMN IF EXISTS embedding"
                        )
                        client.execute_sql(
                            f"ALTER TABLE {args.table} RENAME COLUMN embedding_vector TO embedding"
                        )

                        print(" ✅ Embedding column converted to vector type")

        # Verify data
        verify_embeddings(pipeline, args.table, has_embeddings=not args.no_embeddings)

        print("\n✅ Test pipeline completed successfully!")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
