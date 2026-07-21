"""
Faz 12 - AI Opportunity Engine testleri.
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.domains.opportunity_engine import service
from app.domains.opportunity_engine.schemas import OpportunityReport


def make_tx(description, amount, category=None, is_flagged=False):
    tx = MagicMock()
    tx.description = description
    tx.amount = str(amount)
    tx.category = category
    tx.is_flagged = is_flagged
    from datetime import datetime
    tx.transaction_date = datetime(2026, 3, 15, 12, 0)
    return tx


class TestOpportunityEngine:
    def test_empty_transactions(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.analyze(db, "test-account-id")
        assert result.opportunity_score == 0
        assert result.total_monthly_saving == Decimal("0")

    def test_subscription_detection(self):
        txs = [
            make_tx("Netflix Abonelik", -150, "abonelik"),
            make_tx("YouTube Premium", -120, "abonelik"),
            make_tx("Spotify", -90, "abonelik"),
            make_tx("Maas Yatisi", 15000, "gelir"),
        ]
        from datetime import datetime
        txs[0].transaction_date = datetime(2026, 1, 1)
        txs[1].transaction_date = datetime(2026, 2, 1)
        txs[2].transaction_date = datetime(2026, 3, 1)
        txs[3].transaction_date = datetime(2026, 1, 15)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.analyze(db, "test-account-id")
        assert len(result.opportunities) > 0

    def test_high_spending_category(self):
        txs = []
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        for i in range(20):
            tx = make_tx(f"Yemeksepeti {i}", -500, "yemek")
            tx.transaction_date = base + timedelta(days=i)
            txs.append(tx)
        tx_gelir = make_tx("Maas", 20000, "gelir")
        tx_gelir.transaction_date = base
        txs.append(tx_gelir)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.analyze(db, "test-account-id")
        yemek_opps = [o for o in result.opportunities if o.category == "yemek"]
        assert len(yemek_opps) > 0

    def test_report_structure(self):
        txs = [make_tx("Netflix", -150, "abonelik")]
        txs[0].transaction_date = __import__("datetime").datetime(2026, 1, 1)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.analyze(db, "test-account-id")
        assert isinstance(result, OpportunityReport)
        assert result.opportunity_score >= 0
        assert result.opportunity_score <= 100
        assert isinstance(result.opportunities, list)
        assert isinstance(result.summary, str)

    def test_total_saving_calculation(self):
        txs = []
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        for i in range(10):
            tx = make_tx("Restoran", -800, "yemek")
            tx.transaction_date = base + timedelta(days=i*3)
            txs.append(tx)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.analyze(db, "test-account-id")
        assert result.total_monthly_saving >= Decimal("0")
        assert result.total_annual_saving == result.total_monthly_saving * 12
