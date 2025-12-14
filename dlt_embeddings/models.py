"""SQLAlchemy models for conversations with vector embeddings."""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Conversation(Base):
    """SQLAlchemy model for conversations table with vector embeddings."""

    __tablename__ = "conversations"
    __table_args__ = {"schema": "dlt_dev"}

    # Primary key - using message_id as unique identifier
    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String, index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector(384), nullable=True)
    create_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    update_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        """String representation of the conversation."""
        return (
            f"<Conversation(message_id='{self.message_id}', "
            f"conversation_id='{self.conversation_id}', role='{self.role}')>"
        )

    @property
    def created_at(self) -> Optional[datetime]:
        """Convert create_time to datetime."""
        if self.create_time:
            return datetime.fromtimestamp(self.create_time)
        return None

    @property
    def updated_at(self) -> Optional[datetime]:
        """Convert update_time to datetime."""
        if self.update_time:
            return datetime.fromtimestamp(self.update_time)
        return None
