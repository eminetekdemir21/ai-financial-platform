"""CSV yukleme ve islem listeleme endpoint testleri."""
import io

from tests.conftest import make_csv_file


def test_upload_csv_creates_transactions(client, registered_user, test_account):
    csv_file = make_csv_file(
        [
            ("2026-06-01", "Migros Market", "-450.75"),
            ("2026-06-02", "Elektrik Faturasi", "-320.00"),
            ("2026-06-03", "Maas Yatti", "15000.00"),
        ]
    )

    response = client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", csv_file, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 3


def test_list_transactions_returns_uploaded_rows(client, registered_user, test_account):
    csv_file = make_csv_file([("2026-06-10", "Netflix Abonelik", "-99.90")])
    client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", csv_file, "text/csv")},
    )

    response = client.get(
        "/api/v1/transactions/list",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
    )
    assert response.status_code == 200
    descriptions = [tx["description"] for tx in response.json()]
    assert "Netflix Abonelik" in descriptions


def test_list_transactions_empty_account_returns_empty_list(
    client, registered_user, test_account
):
    response = client.get(
        "/api/v1/transactions/list",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
    )
    assert response.status_code == 200
    assert response.json() == []


def test_upload_csv_with_unrecognized_columns_returns_400(
    client, registered_user, test_account
):
    """
    Taninmayan sutun basliklarina sahip bir CSV yuklendiginde, sistem
    500 Internal Server Error DEGIL, anlamli bir mesajla 400 Bad Request
    dondurmeli - bu bir kullanici hatasidir, sunucu hatasi degil.
    """
    bad_csv = io.BytesIO(b"kolon1,kolon2,kolon3\nx,y,z\n")
    response = client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("bozuk.csv", bad_csv, "text/csv")},
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_uploading_same_csv_twice_skips_duplicates(
    client, registered_user, test_account
):
    """
    10. Gun'de canli olarak gozlemlenen senaryonun kalici testi: ayni
    CSV dosyasi yanlislikla iki kez yuklenirse, ikinci yuklemede hicbir
    yeni islem eklenmemeli - hepsi mukerrer olarak atlanmali.
    """
    rows = [
        ("2026-06-01", "Migros Market", "-450.75"),
        ("2026-06-02", "Elektrik Faturasi", "-320.00"),
    ]

    first_upload = client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", make_csv_file(rows), "text/csv")},
    )
    assert first_upload.json()["imported_count"] == 2
    assert first_upload.json()["skipped_duplicates"] == 0

    second_upload = client.post(
        "/api/v1/transactions/upload/csv",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
        files={"file": ("test.csv", make_csv_file(rows), "text/csv")},
    )
    assert second_upload.json()["imported_count"] == 0
    assert second_upload.json()["skipped_duplicates"] == 2

    list_response = client.get(
        "/api/v1/transactions/list",
        params={"account_id": test_account["id"]},
        headers=registered_user["headers"],
    )
    assert len(list_response.json()) == 2
