from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping=True: bağlantı havuzundaki ölü bağlantıları (örn. DB restart
# sonrası) otomatik tespit edip yeniler. Bunsuz, uzun süre boşta kalan bir
# backend production'da rastgele "connection closed" hatası verir.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tüm SQLAlchemy modellerinin miras alacağı temel sınıf."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Her HTTP request için ayrı bir DB session açar, işlem bitince kapatır.
    FastAPI route'larında Depends(get_db) ile kullanılır.

    try/finally kullanılması kritik: route içinde bir exception fırlasa
    bile session'ın kapanmaması, connection pool'un zamanla tükenmesine
    (connection leak) yol açar — production'da en sık görülen DB
    hatalarından biri budur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
