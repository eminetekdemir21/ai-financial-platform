import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import TimestampMixin, UUIDMixin


class FinancialGoal(Base, UUIDMixin, TimestampMixin):
    """
    Kullanıcının finansal hedefi.
    Örnek: 8 ay içinde 80.000 TL bilgisayar almak.
    """

    __tablename__ = "financial_goals"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False
    )  # low, medium, high
    current_savings: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=0, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active, completed, cancelled

    def __repr__(self) -> str:
        return f"<FinancialGoal {self.name} {self.target_amount}>"
