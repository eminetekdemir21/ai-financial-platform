"""
pytest fixture'lari.

Test izolasyon stratejisi:
Her test, veritabani baglantisi uzerinde bir transaction acar, test
bitince bu transaction ROLLBACK edilir. Boylece:
  - Ayri bir "test veritabani" kurmaya gerek kalmaz, gercek gelistirme
    veritabani (docker-compose ile ayaga kaldirdigimiz Postgres) kullanilir.
  - Testler birbirinden ve gercek gelistirme verisinden (dashboard'da
    gordugumuz 5 islem gibi) tamamen izole calisir - testler ne kadar
    veri eklerse eklesin, test bitince hicbir iz kalmaz.
  - Uygulama kodu icinde gecen db.commit() cagrilari (orn. AuthService,
    categorization_service) bir SAVEPOINT'i kapatir; asagidaki event
    listener bunu farkedip otomatik yeni bir SAVEPOINT acar, boylece
    en disaridaki transaction hep acik kalir ve en sonda rollback edilir.
"""
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

engine = create_engine(settings.DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _ensure_tables():
    """Tablolarin var oldugunu garanti eder (zaten Alembic ile olusturulmus
    olsa bile, testlerin bagimsiz calisabilmesi icin no-op olarak calisir)."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """Testler icin hazir, giris yapmis bir kullanici + auth header'i doner."""
    payload = {
        "email": "pytest_user@example.com",
        "password": "TestSifre123",
        "full_name": "Pytest Kullanici",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    data = response.json()
    return {
        "email": payload["email"],
        "password": payload["password"],
        "token": data["access_token"],
        "user": data["user"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


@pytest.fixture()
def test_account(client, registered_user):
    """registered_user icin bir hesap olusturur, hesap bilgisini doner."""
    response = client.post(
        "/api/v1/transactions/accounts",
        headers=registered_user["headers"],
        json={
            "bank_name": "Pytest Bankasi",
            "account_type": "checking",
            "account_number_masked": "**** 0000",
        },
    )
    return response.json()


def make_csv_file(rows: list[tuple[str, str, str]]) -> io.BytesIO:
    """
    Basit bir CSV dosyasi (tarih, aciklama, tutar sutunlariyla) uretir,
    upload endpoint'ine multipart dosya olarak gonderilmeye hazir halde
    bir BytesIO nesnesi doner.
    """
    header = "tarih,aciklama,tutar\n"
    body = "\n".join(f"{tarih},{aciklama},{tutar}" for tarih, aciklama, tutar in rows)
    content = (header + body).encode("utf-8")
    return io.BytesIO(content)
