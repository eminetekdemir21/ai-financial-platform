import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.shared.models.base import TimestampMixin, UUIDMixin


class Account(Base, UUIDMixin, TimestampMixin):
    """
    Kullanıcının banka hesabı. Bir kullanıcının birden fazla hesabı
    olabilir (vadesiz, kredi kartı, yatırım vb).
    """

    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY", nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=0, nullable=False
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account {self.bank_name} {self.account_number_masked}>"


class Transaction(Base, UUIDMixin, TimestampMixin):
    """
    Tek bir banka işlemi. CSV/Excel'den yüklenir veya manuel girilir.
    Kategorilendirme ve fraud detection bu tablodaki verilerle çalışır.
    """

    __tablename__ = "transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Kategorilendirme sonucu (Faz 4'te NLP ile doldurulacak)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category_confidence: Mapped[float | None] = mapped_column(nullable=True)

    # Fraud skoru (Faz 5'te ML ile doldurulacak)
    fraud_score: Mapped[float | None] = mapped_column(nullable=True)
    is_flagged: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Verinin nereden geldiği (csv, excel, manual)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.amount} {self.description[:30]}>"
