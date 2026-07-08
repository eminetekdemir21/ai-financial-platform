"""
Forecasting testleri.
Ilk grup (TestLinearForecast), db/HTTP gerektirmeyen saf birim
testlerdir - dogrudan forecasting_service._linear_forecast fonksiyonunu
cagirir. Ikinci grup, /forecast/{account_id} endpoint'ini farkli veri
senaryolariyla (veri yok, tek ay, iki ay) test eder.
"""
from app.domains.forecasting.forecasting_service import _linear_forecast


class TestLinearForecast:
    def test_flat_series_predicts_same_value(self):
        # Her ay ayni deger -> egim 0, tahmin de ayni deger olmali
        result = _linear_forecast([100.0, 100.0, 100.0])
        assert result == 100.0

    def test_increasing_series_predicts_higher_value(self):
        # Duzenli artan seri (100, 200, 300) -> bir sonraki 400 olmali
        result = _linear_forecast([100.0, 200.0, 300.0])
        assert result == 400.0

    def test_decreasing_series_predicts_lower_value(self):
        result = _linear_forecast([300.0, 200.0, 100.0])
        assert result == 0.0

    def test_single_value_returns_same_value(self):
        # n=1 durumunda denominator 0 olur, fallback olarak ortalama donmeli
        result = _linear_forecast([500.0])
        assert result == 500.0


class TestForecastEndpoint:
    def test_forecast_with_no_transactions_returns_insufficient_data(
        self, client, registered_user, test_account
    ):
        response = client.get(
            f"/api/v1/forecast/{test_account['id']}",
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "insufficient_data"
        assert data["confidence"] == "none"

    def test_forecast_with_one_month_uses_average_fallback(
        self, client, registered_user, test_account
    ):
        from tests.conftest import make_csv_file

        csv_file = make_csv_file(
            [
                ("2026-06-01", "Migros Market", "-450.75"),
                ("2026-06-03", "Maas Yatti", "15000.00"),
            ]
        )
        client.post(
            "/api/v1/transactions/upload/csv",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
            files={"file": ("test.csv", csv_file, "text/csv")},
        )

        response = client.get(
            f"/api/v1/forecast/{test_account['id']}",
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "average_fallback"
        assert data["confidence"] == "low"
        assert len(data["monthly_history"]) == 1

    def test_forecast_with_two_months_uses_linear_trend(
        self, client, registered_user, test_account
    ):
        from tests.conftest import make_csv_file

        csv_file = make_csv_file(
            [
                ("2026-05-01", "Migros Market", "-400.00"),
                ("2026-06-01", "Migros Market Haziran", "-500.00"),
            ]
        )
        client.post(
            "/api/v1/transactions/upload/csv",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
            files={"file": ("test.csv", csv_file, "text/csv")},
        )

        response = client.get(
            f"/api/v1/forecast/{test_account['id']}",
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "linear_trend"
        assert len(data["monthly_history"]) == 2

    def test_forecast_requires_account_ownership(self, client, test_account):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "forecast_saldirgan@example.com",
                "password": "GucluSifre123",
                "full_name": "Saldirgan",
            },
        )
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "forecast_saldirgan@example.com",
                "password": "GucluSifre123",
            },
        )
        attacker_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        response = client.get(
            f"/api/v1/forecast/{test_account['id']}", headers=attacker_headers
        )
        assert response.status_code == 404
