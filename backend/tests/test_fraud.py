"""
Fraud detection testleri.
Ilk grup (TestFraudSignals), db/HTTP gerektirmeyen saf birim testlerdir -
dogrudan fraud_rules.py fonksiyonlarini cagirir.
Ikinci grup, /fraud/run endpoint'ini gercek bir "mukerrer islem"
senaryosuyla test eder (10. Gun'de manuel olarak yaptigimiz testin
otomatik/kalici versiyonu).
"""
from datetime import datetime, timedelta

from app.domains.fraud import fraud_rules as rules


class TestFraudSignals:
    def test_large_amount_no_signal_when_close_to_mean(self):
        # amount, ortalamaya cok yakinsa (z-score dusuk) sinyal 0 olmali
        score = rules.signal_large_amount(amount=105, mean=100, stdev=20)
        assert score == 0.0

    def test_large_amount_signal_triggers_on_outlier(self):
        # amount, ortalamadan 5 standart sapma uzaktaysa yuksek skor beklenir
        score = rules.signal_large_amount(amount=1100, mean=100, stdev=200)
        assert score > 0.0

    def test_large_amount_handles_zero_stdev(self):
        # Tum islemler ayni tutardaysa (stdev=0), sifira bolme hatasi olmamali
        score = rules.signal_large_amount(amount=500, mean=500, stdev=0)
        assert score == 0.0

    def test_odd_hour_triggers_before_5am(self):
        dt = datetime(2026, 6, 1, 3, 0, 0)
        assert rules.signal_odd_hour(dt) > 0.0

    def test_odd_hour_no_trigger_during_day(self):
        dt = datetime(2026, 6, 1, 14, 0, 0)
        assert rules.signal_odd_hour(dt) == 0.0

    def test_duplicate_detects_same_amount_within_window(self):
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        other_time = base_time + timedelta(minutes=2)
        score = rules.signal_duplicate(
            amount=250.0,
            transaction_date=base_time,
            other_transactions=[(250.0, other_time)],
        )
        assert score > 0.0

    def test_duplicate_no_match_outside_window(self):
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        far_time = base_time + timedelta(hours=2)
        score = rules.signal_duplicate(
            amount=250.0,
            transaction_date=base_time,
            other_transactions=[(250.0, far_time)],
        )
        assert score == 0.0

    def test_duplicate_no_match_different_amount(self):
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        other_time = base_time + timedelta(minutes=1)
        score = rules.signal_duplicate(
            amount=250.0,
            transaction_date=base_time,
            other_transactions=[(99.0, other_time)],
        )
        assert score == 0.0

    def test_high_frequency_triggers_with_many_transactions(self):
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        other_dates = [base_time + timedelta(minutes=i) for i in range(6)]
        score = rules.signal_high_frequency(base_time, other_dates)
        assert score > 0.0

    def test_high_frequency_no_trigger_with_few_transactions(self):
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        other_dates = [base_time + timedelta(minutes=1)]
        score = rules.signal_high_frequency(base_time, other_dates)
        assert score == 0.0


class TestFraudEndpoint:
    def test_run_flags_duplicate_transactions(self, client, registered_user, test_account, db_session):
        import uuid
        from app.domains.transactions.models import Transaction

        # Ayni tutarda, 2 dakika arayla iki islem elle ekleniyor - tipik
        # "mukerrer odeme" senaryosu (10. Gun'de manuel test ettigimizle ayni).
        base_time = datetime(2026, 7, 2, 10, 0, 0)
        tx1 = Transaction(
            id=uuid.uuid4(),
            account_id=test_account["id"],
            amount=250.00,
            description="Test Odeme 1",
            transaction_date=base_time,
            source="manual",
        )
        tx2 = Transaction(
            id=uuid.uuid4(),
            account_id=test_account["id"],
            amount=250.00,
            description="Test Odeme 2",
            transaction_date=base_time + timedelta(minutes=2),
            source="manual",
        )
        db_session.add_all([tx1, tx2])
        db_session.commit()

        response = client.post(
            "/api/v1/fraud/run",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_analyzed"] == 2
        assert data["flagged_count"] == 2

    def test_run_does_not_flag_normal_transaction(
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
            "/api/v1/fraud/run",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["flagged_count"] == 0

    def test_run_on_empty_account_returns_zero(self, client, registered_user, test_account):
        response = client.post(
            "/api/v1/fraud/run",
            params={"account_id": test_account["id"]},
            headers=registered_user["headers"],
        )
        assert response.status_code == 200
        assert response.json() == {"total_analyzed": 0, "flagged_count": 0}
