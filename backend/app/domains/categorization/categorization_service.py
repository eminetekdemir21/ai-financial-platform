"""
Categorization domain service.
Hibrit mantik: once kural tabanli eslesme denenir (hizli, kesin).
Bulunamazsa embedding/benzerlik siniflandiricisi devreye girer.
Hicbiri yeterince eminse "diger" olarak isaretlenir.
"""

import uuid

from sqlalchemy.orm import Session

from app.domains.categorization import similarity_classifier
from app.domains.categorization.rules import match_rule
from app.domains.transactions.models import Transaction

FALLBACK_CATEGORY = "diger"


def categorize_transaction(description: str, merchant: str | None = None) -> tuple[str, str, float]:
    """
    Tek bir islemi kategorilendirir.
    Doner: (kategori, kullanilan_yontem, guven_skoru)
    kullanilan_yontem: "rule" | "embedding" | "fallback"
    """
    rule_match = match_rule(description, merchant)
    if rule_match:
        return rule_match, "rule", 1.0

    embedding_match, score = similarity_classifier.classify(description, merchant)
    if embedding_match:
        return embedding_match, "embedding", round(score, 3)

    return FALLBACK_CATEGORY, "fallback", round(score, 3)


def categorize_account_transactions(db: Session, account_id: uuid.UUID) -> dict:
    """
    Bir hesabin henuz kategorisi olmayan (category IS NULL) tum
    islemlerini kategorilendirir ve veritabanina yazar.
    Ozet istatistik dondurur (kac islem, hangi yontemle kategorilendi).
    """
    uncategorized = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id, Transaction.category.is_(None))
        .all()
    )

    stats = {"rule": 0, "embedding": 0, "fallback": 0}
    for tx in uncategorized:
        category, method, _score = categorize_transaction(tx.description, tx.merchant)
        tx.category = category
        stats[method] += 1

    db.commit()

    return {
        "total_categorized": len(uncategorized),
        "by_method": stats,
    }
