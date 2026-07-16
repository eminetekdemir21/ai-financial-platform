import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.shared.models.base import TimestampMixin, UUIDMixin


class SavedScenario(Base, UUIDMixin, TimestampMixin):
    """
    Kullanicinin kaydettigi What-If senaryosu.

    Hem gonderilen istek (request_payload) hem de o an hesaplanan sonuc
    (result_snapshot) JSONB olarak saklanir; boylece gecmisteki bir
    senaryo, sonradan islemler degisse bile hesaplandigi haliyle
    goruntulenebilir.
    """

    __tablename__ = "saved_scenarios"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<SavedScenario {self.name}>"
