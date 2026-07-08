"""
RAG embedding servisi.

İşlemleri metne çevirip TF-IDF vektörüne dönüştürür,
pgvector'a kaydeder ve semantik arama yapar.

Neden TF-IDF (sentence-transformers değil):
- Harici model indirme gerektirmez (offline çalışır)
- Docker image boyutunu şişirmez
- Türkçe finansal metinlerde kelime eşleşmesi yeterince iyi çalışır
- sentence-transformers'a geçiş sadece bu dosyadaki _vectorize
  fonksiyonunu değiştirmeyi gerektirir — mimari aynı kalır
"""
import uuid
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domains.assistant.rag.models import TransactionEmbedding
from app.domains.transactions.models import Transaction

MODEL_NAME = "tfidf-v1"
VECTOR_DIM = 384


def _transaction_to_text(tx: Transaction) -> str:
    """
    İşlemi embedding için metne çevirir.
    Açıklama + kategori + tutar yönü birleştirilerek
    anlamlı bir temsil oluşturulur.
    """
    direction = "gelir" if float(tx.amount) > 0 else "gider"
    category = tx.category or "kategorisiz"
    return f"{tx.description} {category} {direction}".lower()


def _vectorize(texts: list[str]) -> np.ndarray:
    """
    Metinleri 384 boyutlu TF-IDF vektörlerine çevirir.
    Boyut 384'e padding/truncation ile normalize edilir.
    """
    vectorizer = TfidfVectorizer(max_features=VECTOR_DIM, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(texts).toarray()

    # Boyutu tam olarak 384'e getir (padding veya kırpma)
    if matrix.shape[1] < VECTOR_DIM:
        pad = VECTOR_DIM - matrix.shape[1]
        matrix = np.pad(matrix, ((0, 0), (0, pad)))
    else:
        matrix = matrix[:, :VECTOR_DIM]

    return matrix.astype(np.float32)


def index_account_transactions(db: Session, account_id: uuid.UUID) -> int:
    """
    Hesabın tüm işlemlerini embedding'e çevirip pgvector'a kaydeder.
    Zaten indexlenmiş işlemler güncellenir (upsert mantığı).
    Kaydedilen işlem sayısını döner.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    if not transactions:
        return 0

    texts = [_transaction_to_text(tx) for tx in transactions]
    vectors = _vectorize(texts)

    saved = 0
    for tx, vec in zip(transactions, vectors):
        # Varsa güncelle, yoksa ekle
        existing = (
            db.query(TransactionEmbedding)
            .filter(
                TransactionEmbedding.transaction_id == tx.id,
                TransactionEmbedding.model_name == MODEL_NAME,
            )
            .first()
        )
        if existing:
            existing.embedding = vec.tolist()
        else:
            db.add(
                TransactionEmbedding(
                    transaction_id=tx.id,
                    embedding=vec.tolist(),
                    model_name=MODEL_NAME,
                )
            )
        saved += 1

    db.commit()
    return saved


def retrieve_similar(
    db: Session,
    account_id: uuid.UUID,
    query: str,
    top_k: int = 5,
) -> List[Transaction]:
    """
    Kullanıcının sorusunu vektöre çevirip pgvector cosine similarity
    ile en alakalı işlemleri bulur.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    if not transactions:
        return []

    # Sorguyu da aynı vektör uzayına çevir
    all_texts = [_transaction_to_text(tx) for tx in transactions] + [query.lower()]
    vectors = _vectorize(all_texts)
    query_vec = vectors[-1]  # Son vektör sorgu vektörü

    # pgvector cosine similarity sorgusu
    embeddings = (
        db.query(TransactionEmbedding)
        .filter(
            TransactionEmbedding.transaction_id.in_([tx.id for tx in transactions]),
            TransactionEmbedding.model_name == MODEL_NAME,
        )
        .all()
    )

    if not embeddings:
        # Embedding yoksa en son işlemleri döndür (fallback)
        return transactions[:top_k]

    # Cosine similarity hesapla
    tx_map = {tx.id: tx for tx in transactions}
    scored = []
    qv = np.array(query_vec, dtype=np.float32)
    qnorm = np.linalg.norm(qv)

    for emb in embeddings:
        ev = np.array(emb.embedding, dtype=np.float32)
        enorm = np.linalg.norm(ev)
        if qnorm > 0 and enorm > 0:
            score = float(np.dot(qv, ev) / (qnorm * enorm))
        else:
            score = 0.0
        if emb.transaction_id in tx_map:
            scored.append((score, tx_map[emb.transaction_id]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [tx for _, tx in scored[:top_k]]
