"""
Faz 15 - AI Explainability testleri.
"""
import pytest
import uuid
from unittest.mock import MagicMock
from datetime import datetime
from app.domains.explainability import service


def make_transaction(desc, amount, category=None, is_flagged=False, fraud_score=0.0, hour=12):
    tx = MagicMock()
    tx.id = uuid.uuid4()
    tx.description = desc
    tx.amount = str(amount)
    tx.category = category
    tx.is_flagged = is_flagged
    tx.fraud_score = fraud_score
    tx.category_confidence = 0.9
    tx.transaction_date = datetime(2026, 3, 15, hour, 0)
    return tx


class TestFraudExplanation:
    def test_large_amount_flagged(self):
        tx = make_transaction("Elektronik Magaza", -14500, is_flagged=True, fraud_score=0.8)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx
        db.query.return_value.filter.return_value.count.return_value = 1

        result = service.explain_fraud(db, tx.id, uuid.uuid4())
        assert "Yuksek tutar" in " ".join(result.reasons)
        assert result.risk_level in ["yuksek", "kritik"]

    def test_night_transaction_flagged(self):
        tx = make_transaction("ATM Para Cekme", -500, is_flagged=True, fraud_score=0.5, hour=2)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx
        db.query.return_value.filter.return_value.count.return_value = 1

        result = service.explain_fraud(db, tx.id, uuid.uuid4())
        assert "Gece saati" in " ".join(result.reasons)

    def test_low_risk_transaction(self):
        tx = make_transaction("Migros Market", -150, is_flagged=False, fraud_score=0.1, hour=14)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx
        db.query.return_value.filter.return_value.count.return_value = 1

        result = service.explain_fraud(db, tx.id, uuid.uuid4())
        assert result.risk_level == "dusuk"

    def test_fraud_explanation_structure(self):
        tx = make_transaction("Test Islem", -1000, fraud_score=0.5)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx
        db.query.return_value.filter.return_value.count.return_value = 0

        result = service.explain_fraud(db, tx.id, uuid.uuid4())
        assert isinstance(result.reasons, list)
        assert isinstance(result.recommendation, str)
        assert result.risk_level in ["dusuk", "orta", "yuksek", "kritik"]


class TestCategoryExplanation:
    def test_known_keyword_match(self):
        tx = make_transaction("Migros Market Satin Alim", -250, category="market")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx

        result = service.explain_category(db, tx.id, uuid.uuid4())
        assert result.category == "market"
        assert isinstance(result.explanation, str)

    def test_category_explanation_structure(self):
        tx = make_transaction("Netflix Abonelik", -150, category="abonelik")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = tx

        result = service.explain_category(db, tx.id, uuid.uuid4())
        assert result.category == "abonelik"
        assert 0 <= result.confidence <= 1
        assert isinstance(result.alternative_categories, list)


class TestHealthScoreExplanation:
    def test_empty_account(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = service.explain_health_score(db, uuid.uuid4())
        assert result.score == 0
        assert result.grade == "F"

    def test_healthy_account(self):
        txs = []
        for i in range(10):
            tx = make_transaction(f"Gelir {i}", 10000, "gelir")
            txs.append(tx)
        for i in range(5):
            tx = make_transaction(f"Harcama {i}", -500, "market")
            txs.append(tx)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.explain_health_score(db, uuid.uuid4())
        assert result.score > 0
        assert result.grade in ["A", "B", "C", "D", "F"]
        assert len(result.factors) > 0

    def test_improvement_tips(self):
        txs = []
        for i in range(5):
            tx = make_transaction(f"Harcama {i}", -5000, "alisveris")
            txs.append(tx)
        tx_gelir = make_transaction("Maas", 6000, "gelir")
        txs.append(tx_gelir)

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = txs
        result = service.explain_health_score(db, uuid.uuid4())
        assert isinstance(result.improvement_tips, list)
        assert len(result.improvement_tips) > 0
