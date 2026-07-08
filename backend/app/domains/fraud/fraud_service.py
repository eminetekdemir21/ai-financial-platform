"""
Fraud detection domain service.
Kural tabanli sinyalleri birlestirerek her islem icin bir fraud_score
(0.0 - 1.0 arasi) hesaplar. Skor FLAG_THRESHOLD'un uzerindeyse islem
is_flagged = True olarak isaretlenir.

Kategorilendirmenin aksine (sadece category IS NULL olanlar islenir),
fraud analizi hesabin TUM islemlerini her calistirmada yeniden
degerlendirir - cunku yeni bir islem eklendiginde, eskiden "normal"
gorunen bir islem artik supheli hale gelebilir (orn. ayni tutarin
kisa surede tekrarlanmasi sinyali, yeni islem eklenince degisir).
"""
import statistics
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.domains.fraud import fraud_rules as rules
from app.domains.transactions.models import Transaction

FLAG_THRESHOLD = 0.5


def _compute_score(
    tx: Transaction,
    mean: float,
    stdev: float,
    other_transactions: list[tuple[float, datetime]],
) -> tuple[float, list[str]]:
    """
    Tek bir islem icin tum sinyalleri hesaplar. Nihai skor, tetiklenen
    sinyallerin en yuksegidir (herhangi bir guclu sinyal tek basina
    islemi supheli yapmaya yeter). Aciklanabilirlik icin hangi
    sinyallerin tetiklendigi de doner.
    """
    amount = float(tx.amount)
    other_dates = [d for _, d in other_transactions]

    signals = {
        "large_amount": rules.signal_large_amount(amount, mean, stdev),
        "odd_hour": rules.signal_odd_hour(tx.transaction_date),
        "duplicate": rules.signal_duplicate(amount, tx.transaction_date, other_transactions),
        "high_frequency": rules.signal_high_frequency(tx.transaction_date, other_dates),
    }

    triggered = [name for name, score in signals.items() if score > 0]
    final_score = max(signals.values()) if signals else 0.0
    return round(final_score, 3), triggered


def run_fraud_detection(db: Session, account_id: uuid.UUID) -> dict:
    """
    Bir hesabin tum islemlerini analiz eder, fraud_score ve is_flagged
    alanlarini gunceller. Ozet istatistik dondurur.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    if not transactions:
        return {"total_analyzed": 0, "flagged_count": 0}

    amounts = [float(tx.amount) for tx in transactions]
    mean = statistics.mean(amounts)
    stdev = statistics.pstdev(amounts) if len(amounts) > 1 else 0.0

    flagged_count = 0
    for tx in transactions:
        others = [
            (float(other.amount), other.transaction_date)
            for other in transactions
            if other.id != tx.id
        ]
        score, _triggered = _compute_score(tx, mean, stdev, others)
        tx.fraud_score = score
        tx.is_flagged = score >= FLAG_THRESHOLD
        if tx.is_flagged:
            flagged_count += 1

    db.commit()
    return {"total_analyzed": len(transactions), "flagged_count": flagged_count}
