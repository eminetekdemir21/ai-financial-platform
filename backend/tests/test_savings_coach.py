"""
AI Savings Coach testleri.
Veritabani gerektirmeyen saf birim testleri.
"""
from decimal import Decimal
from unittest.mock import MagicMock
from datetime import datetime, timezone


def make_tx(amount, category=None, days_ago=0):
    """Test işlemi oluşturmak için yardımcı fonksiyon."""
    tx = MagicMock()
    tx.amount = Decimal(str(amount))
    tx.category = category
    base_date = datetime(2026, 6, 1, tzinfo=timezone.utc)
    from datetime import timedelta
    tx.transaction_date = base_date - timedelta(days=days_ago)
    return tx


class TestSavingsCoachService:
    """Savings Coach servis testleri."""

    def test_bos_islem_listesi_empty_report_doner(self):
        """İşlem yoksa boş rapor dönmeli."""
        from app.domains.savings_coach.service import _empty_report
        report = _empty_report()
        assert float(report.total_monthly_income) == 0
        assert report.tips == []
        assert report.spending_trends == []

    def test_tasarruf_orani_hesaplama(self):
        """Tasarruf oranı doğru hesaplanmalı."""
        from app.domains.savings_coach.service import TARGET_SAVINGS_RATE
        # Hedef %20 olmalı
        assert TARGET_SAVINGS_RATE == 20.0

    def test_tip_uretimi_artan_kategori(self):
        """Artan harcama kategorisi için öneri üretilmeli."""
        from app.domains.savings_coach.schemas import SpendingTrend
        from app.domains.savings_coach.service import _generate_tips

        trends = [
            SpendingTrend(
                category="yemek",
                current_monthly=Decimal("1500"),
                previous_monthly=Decimal("800"),
                change_pct=87.5,
                trend="artiyor",
            )
        ]
        cat_totals = {"yemek": 1500.0}
        tips = _generate_tips(
            spending_trends=trends,
            cat_totals=cat_totals,
            monthly_income=15000.0,
            savings_rate=15.0,
        )
        assert len(tips) > 0
        yemek_tip = next((t for t in tips if t.category == "yemek"), None)
        assert yemek_tip is not None
        assert float(yemek_tip.monthly_saving_potential) > 0

    def test_tasarruf_orani_dusukse_genel_oneri_gelir(self):
        """Tasarruf oranı düşükse genel öneri üretilmeli."""
        from app.domains.savings_coach.service import _generate_tips

        tips = _generate_tips(
            spending_trends=[],
            cat_totals={},
            monthly_income=15000.0,
            savings_rate=5.0,  # Çok düşük
        )
        genel_tip = next((t for t in tips if t.category == "genel"), None)
        assert genel_tip is not None

    def test_coach_message_yuksek_tasarruf(self):
        """Yüksek tasarruf oranında pozitif mesaj üretilmeli."""
        from app.domains.savings_coach.service import _generate_coach_message

        message = _generate_coach_message(
            savings_rate=35.0,
            tips=[],
            spending_trends=[],
        )
        assert "Harika" in message or "etkileyici" in message

    def test_coach_message_dusuk_tasarruf(self):
        """Düşük tasarruf oranında uyarı mesajı üretilmeli."""
        from app.domains.savings_coach.service import _generate_coach_message

        message = _generate_coach_message(
            savings_rate=3.0,
            tips=[],
            spending_trends=[],
        )
        assert "Dikkat" in message or "düşük" in message

    def test_tip_sayisi_max_5(self):
        """En fazla 5 öneri üretilmeli."""
        from app.domains.savings_coach.schemas import SpendingTrend
        from app.domains.savings_coach.service import _generate_tips

        # Çok sayıda artan kategori
        trends = []
        cat_totals = {}
        for cat in ["yemek", "market", "ulasim", "alisveris", "saglik", "egitim", "abonelik"]:
            trends.append(SpendingTrend(
                category=cat,
                current_monthly=Decimal("1000"),
                previous_monthly=Decimal("500"),
                change_pct=100.0,
                trend="artiyor",
            ))
            cat_totals[cat] = 1000.0

        tips = _generate_tips(
            spending_trends=trends,
            cat_totals=cat_totals,
            monthly_income=20000.0,
            savings_rate=10.0,
        )
        assert len(tips) <= 5
