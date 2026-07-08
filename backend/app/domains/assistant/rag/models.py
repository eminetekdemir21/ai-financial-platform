import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import TimestampMixin, UUIDMixin


class TransactionEmbedding(Base, UUIDMixin, TimestampMixin):
    """
    Her işlemin TF-IDF embedding vektörünü saklar.
    pgvector'ın Vector tipi, cosine similarity sorguları için
    gerekli indekslemeyi sağlar.

    model_name sütunu: hangi embedding modeliyle üretildiğini saklar.
    İleride farklı bir modele geçilirse eski vektörler korunur,
    sadece yeni model_name ile yeniden indexlenir.
    """

    __tablename__ = "transaction_embeddings"
    __table_args__ = (
        UniqueConstraint("transaction_id", "model_name", name="uq_tx_embedding_model"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 384 boyutlu vektör — TF-IDF/sentence-transformers ile uyumlu boyut
    embedding: Mapped[list] = mapped_column(Vector(384), nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="tfidf-v1"
    )

    def __repr__(self) -> str:
        return f"<TransactionEmbedding tx={self.transaction_id}>"
