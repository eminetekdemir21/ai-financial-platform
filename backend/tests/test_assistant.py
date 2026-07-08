"""
AI Financial Assistant testleri.
LLM_API_KEY .env dosyasinda tanimli olmadigi surece (varsayilan durum),
gercek bir Anthropic API cagrisi yapilmaz - bu yuzden testler LLM
cagrisi olmadan test edilebilecek iki kritik alana odaklanir:
1. build_context fonksiyonu (saf, db'ye bagli ama LLM'e bagli degil)
2. "yapilandirilmamis" (503) ve sahiplik kontrolu (404) davranislari
"""
import uuid

from app.domains.assistant import assistant_service


def test_build_context_includes_transaction_summary(
    client, registered_user, test_account, db_session
):
    from app.domains.transactions.models import Account
    from tests.conftest import make_csv_file

    csv_file = make_csv_file([("2026-06-01", "Migros Market", "-450.75")])
    client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    account = (
        db_session.query(Account)
        .filter(Account.id == uuid.UUID(test_account["id"]))
        .first()
    )
    context = assistant_service.build_context(db_session, account)

    assert "Migros Market" in context
    assert "450.75" in context
    assert test_account["bank_name"] in context


def test_build_context_handles_empty_account(client, registered_user, test_account, db_session):
    from app.domains.transactions.models import Account

    account = (
        db_session.query(Account)
        .filter(Account.id == uuid.UUID(test_account["id"]))
        .first()
    )
    context = assistant_service.build_context(db_session, account)
    assert "henuz hic islem yok" in context


def test_chat_returns_503_when_llm_not_configured(
    client, registered_user, test_account, monkeypatch
):
    monkeypatch.setattr(assistant_service.settings, "LLM_API_KEY", "")

    response = client.post(
        "/api/v1/assistant/chat",
        headers=registered_user["headers"],
        json={"account_id": test_account["id"], "message": "Bu ay ne kadar harcadim?"},
    )
    assert response.status_code == 503


def test_chat_requires_account_ownership(client, test_account):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "assistant_saldirgan@example.com",
            "password": "GucluSifre123",
            "full_name": "Saldirgan",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "assistant_saldirgan@example.com",
            "password": "GucluSifre123",
        },
    )
    attacker_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        headers=attacker_headers,
        json={"account_id": test_account["id"], "message": "test"},
    )
    # Sahiplik kontrolu LLM'e hic ulasmadan once calismali - attacker
    # 503 (yapilandirilmamis) degil, 404 (bulunamadi) almali.
    assert response.status_code == 404
