import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """
    Otomatik artan integer id (1, 2, 3...) yerine UUID kullanıyoruz.
    Neden: integer id'ler tahmin edilebilir (örn. /transactions/5 yazıp
    başkasının verisine erişmeye çalışmak — IDOR güvenlik açığı).
    Bankacılık verisinde bu risk kabul edilemez, UUID tahmin edilemez.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """
    created_at: kayıt ilk oluşturulduğunda otomatik dolar, bir daha değişmez.
    updated_at: her UPDATE işleminde otomatik güncellenir.

    Bu alanlar audit (denetim) amaçlı kritik — "bu kayıt ne zaman
    oluşturuldu/değişti" sorusu bankacılık sistemlerinde sürekli sorulur.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
