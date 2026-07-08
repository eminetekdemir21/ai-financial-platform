"""
Accounts endpoint testleri.
Ozellikle sahiplik (ownership) kontrolunun gercekten calistigini test
etmek onemli - Faz 3.5'te duzelttigimiz guvenlik acigi tam olarak
burada tekrar acilirsa fark edilmesi gereken yer.
"""


def test_create_account(client, registered_user):
    response = client.post(
        "/api/v1/transactions/accounts",
        headers=registered_user["headers"],
        json={
            "bank_name": "Pytest Bankasi",
            "account_type": "checking",
            "account_number_masked": "**** 0000",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["bank_name"] == "Pytest Bankasi"
    assert data["currency"] == "TRY"
    assert data["current_balance"] == "0.00"


def test_create_account_requires_auth(client):
    response = client.post(
        "/api/v1/transactions/accounts",
        json={
            "bank_name": "Pytest Bankasi",
            "account_type": "checking",
            "account_number_masked": "**** 0000",
        },
    )
    assert response.status_code in (401, 403)


def test_list_accounts_returns_only_own(client, registered_user, test_account):
    # Ikinci, farkli bir kullanici olustur - onun hic hesabi olmayacak
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "ikinci_kullanici@example.com",
            "password": "GucluSifre123",
            "full_name": "Ikinci Kullanici",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ikinci_kullanici@example.com", "password": "GucluSifre123"},
    )
    second_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    # Birinci kullanicinin hesabi listede gorunmeli
    first_response = client.get(
        "/api/v1/transactions/accounts", headers=registered_user["headers"]
    )
    assert any(acc["id"] == test_account["id"] for acc in first_response.json())

    # Ikinci kullanicinin listesinde birinci kullanicinin hesabi OLMAMALI
    second_response = client.get(
        "/api/v1/transactions/accounts", headers=second_headers
    )
    assert all(acc["id"] != test_account["id"] for acc in second_response.json())


def test_cannot_upload_to_another_users_account(client, test_account):
    """
    Faz 3.5 guvenlik duzeltmesinin kalici testi: baska bir kullanici,
    kendine ait olmayan bir account_id ile islem yapmaya calistiginda
    404 (bulunamadi) almali - hesabin var olup olmadigi bile sizdirilmamali.
    """
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "saldirgan@example.com",
            "password": "GucluSifre123",
            "full_name": "Saldirgan Kullanici",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "saldirgan@example.com", "password": "GucluSifre123"},
    )
    attacker_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    response = client.get(
        "/api/v1/transactions/list",
        params={"account_id": test_account["id"]},
        headers=attacker_headers,
    )
    assert response.status_code == 404


def test_delete_account_removes_it_and_its_transactions(
    client, registered_user, test_account
):
    """
    Hesap silindiginde, hem hesabin kendisi hem de ona bagli tum
    islemler (cascade sayesinde) veritabanindan kalkmali.
    """
    from tests.conftest import make_csv_file

    csv_file = make_csv_file([("2026-06-01", "Migros Market", "-450.75")])
    client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    delete_response = client.delete(
        f"/api/v1/transactions/accounts/{test_account['id']}",
        headers=registered_user["headers"],
    )
    assert delete_response.status_code == 204

    list_after_delete = client.get(
        "/api/v1/transactions/accounts", headers=registered_user["headers"]
    )
    assert all(acc["id"] != test_account["id"] for acc in list_after_delete.json())

    # Silinen hesabin islemlerine erismeye calismak artik 404 vermeli
    tx_response = client.get(
        "/api/v1/transactions/list",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
    )
    assert tx_response.status_code == 404


def test_cannot_delete_another_users_account(client, test_account):
    """Bir kullanici, baska bir kullanicinin hesabini silemez."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "saldirgan2@example.com",
            "password": "GucluSifre123",
            "full_name": "Saldirgan Kullanici 2",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "saldirgan2@example.com", "password": "GucluSifre123"},
    )
    attacker_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    response = client.delete(
        f"/api/v1/transactions/accounts/{test_account['id']}",
        headers=attacker_headers,
    )
    assert response.status_code == 404
