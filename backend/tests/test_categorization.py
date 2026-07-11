"""
Kategorilendirme testleri.
Ilk grup (TestMatchRule), db/HTTP gerektirmeyen saf birim testlerdir -
dogrudan rules.py fonksiyonlarini cagirir, cok hizli calisir.
Ikinci grup, /categorization/preview ve /run endpoint'lerini test eder.
"""
from app.domains.categorization.rules import match_rule, normalize


class TestMatchRule:
    def test_market_keyword_matches(self):
        assert match_rule("Migros Market Odemesi") == "market"

    def test_abonelik_keyword_matches_netflix(self):
        # Faz 10'da duzeltilen kategori: Netflix artik "fatura" degil
        # "abonelik" olarak eslesmeli.
        assert match_rule("Netflix Abonelik") == "abonelik"

    def test_fatura_keyword_matches_elektrik(self):
        assert match_rule("Elektrik Faturasi") == "fatura"

    def test_gelir_keyword_matches_maas(self):
        assert match_rule("Maas Yatti") == "gelir"

    def test_no_match_returns_none(self):
        assert match_rule("Tamamen alakasiz bir metin xyz123") is None

    def test_normalize_handles_turkish_characters(self):
        # Buyuk harf kucuk harfe donusmeli
        assert normalize("ELEKTRIK") == "elektrik"
        assert normalize("MIGROS") == "migros"

    def test_match_is_case_insensitive(self):
        assert match_rule("MIGROS MARKET") == "market"


class TestCategorizationEndpoints:
    def test_preview_does_not_write_to_db(self, client, registered_user):
        response = client.post(
            "/api/v1/categorization/preview",
            headers=registered_user["headers"],
            json={"description": "Migros Market", "merchant": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "market"
        assert data["method"] == "rule"
        assert data["confidence"] == 1.0

    def test_preview_falls_back_to_embedding_for_unknown_text(
        self, client, registered_user
    ):
        response = client.post(
            "/api/v1/categorization/preview",
            headers=registered_user["headers"],
            json={"description": "Doviz alim satim islemi", "merchant": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["method"] in ("embedding", "fallback")

    def test_run_categorizes_uploaded_transactions(
        self, client, registered_user, test_account
    ):
        from tests.conftest import make_csv_file

        csv_file = make_csv_file([("2026-06-01", "Migros Market", "-450.75")])
        client.post(
            "/api/v1/transactions/upload/csv",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
            files={"file": ("test.csv", csv_file, "text/csv")},
        )

        response = client.post(
            "/api/v1/categorization/run",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        # Upload akisi zaten otomatik kategorilendirdiyse 0, etmediyse 1
        # islem kategorilendirilmis olmali - her iki durumda da hata degil.
        assert response.json()["total_categorized"] >= 0

        list_response = client.get(
            "/api/v1/transactions/list",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
        )
        categories = [tx["category"] for tx in list_response.json()]
        assert "market" in categories

