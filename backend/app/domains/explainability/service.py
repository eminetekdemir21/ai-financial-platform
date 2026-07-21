"""
AI Explainable Recommendation Engine.

Her AI kararinin arkasindaki nedeni aciklar:
- Fraud tespiti: hangi sinyal tetikledi?
- Kategori: hangi kural/kelime eslesti?
- Health score: hangi faktor skoru dusuruyor?
- Savings Coach: bu oneri neden yapildi?
"""
import uuid
from collections import defaultdict
from sqlalchemy.orm import Session

from app.domains.explainability.schemas import (
    FraudExplanation, CategoryExplanation,
    HealthScoreExplanation, RecommendationExplanation,
)
from app.domains.transactions.models import Transaction, Account

# Fraud sinyal esikleri
LARGE_AMOUNT_THRESHOLD = 5000
NIGHT_HOURS = list(range(0, 6)) + list(range(23, 24))

# Kategori anahtar kelimeleri (kategorilendirme modülünden yansima)
CATEGORY_KEYWORDS = {
    "market": ["migros", "bim", "a101", "carrefour", "sok", "hakmar", "macro"],
    "yemek": ["yemeksepeti", "getir", "restoran", "starbucks", "burger", "pizza", "cafe"],
    "ulasim": ["istanbulkart", "uber", "bitaksi", "shell", "opet", "otopark", "pegasus", "thy", "tren bileti", "tcdd"],
    "fatura": ["elektrik", "dogalgaz", "su faturasi", "turkcell", "turk telekom", "internet", "dask"],
    "abonelik": ["netflix", "spotify", "youtube", "amazon prime", "icloud", "dropbox"],
    "alisveris": ["trendyol", "hepsiburada", "amazon", "zara", "lcw", "boyner", "mediamarkt"],
    "saglik": ["eczane", "klinik", "hastane", "lab", "spor salonu", "optik"],
    "egitim": ["udemy", "coursera", "kitap", "dil kursu"],
    "gelir": ["maas", "yatisi", "geliri", "ucret", "odeme"],
}


def explain_fraud(db: Session, transaction_id: uuid.UUID, account_id: uuid.UUID) -> FraudExplanation:
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.account_id == account_id
    ).first()

    if not tx:
        raise ValueError("Islem bulunamadi.")

    amount = float(tx.amount)
    hour = tx.transaction_date.hour
    reasons = []
    risk_factors = []

    # Sinyal 1: Buyuk tutar
    if abs(amount) > LARGE_AMOUNT_THRESHOLD:
        reasons.append(f"Yuksek tutar: {abs(amount):,.2f} TL (esik: {LARGE_AMOUNT_THRESHOLD:,} TL)")
        risk_factors.append(3)

    # Sinyal 2: Gece saati
    if hour in NIGHT_HOURS:
        reasons.append(f"Gece saati islemi: {hour:02d}:00 (normal disarisaat)")
        risk_factors.append(2)

    # Sinyal 3: Mukerer aciklama
    similar = db.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.description == tx.description,
        Transaction.id != tx.id,
    ).count()
    if similar >= 3:
        reasons.append(f"Tekrar eden islem: Ayni aciklama {similar} kez daha gorulmus")
        risk_factors.append(2)

    # Sinyal 4: Ayni gunde yuksek frekans
    same_day = db.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.transaction_date == tx.transaction_date,
    ).count()
    if same_day >= 5:
        reasons.append(f"Yuksek gunluk frekans: Ayni gunde {same_day} islem")
        risk_factors.append(1)

    if not reasons:
        reasons.append("Otomatik ML modeli tarafindan dusuk guvenle isaretlendi")

    score = float(tx.fraud_score or 0)
    if score >= 0.8:
        risk_level = "kritik"
    elif score >= 0.6:
        risk_level = "yuksek"
    elif score >= 0.4:
        risk_level = "orta"
    else:
        risk_level = "dusuk"

    recommendation = _fraud_recommendation(risk_level, reasons)

    return FraudExplanation(
        transaction_id=str(tx.id),
        description=tx.description,
        amount=str(tx.amount),
        is_flagged=tx.is_flagged,
        fraud_score=score,
        reasons=reasons,
        risk_level=risk_level,
        recommendation=recommendation,
    )


def explain_category(db: Session, transaction_id: uuid.UUID, account_id: uuid.UUID) -> CategoryExplanation:
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.account_id == account_id
    ).first()

    if not tx:
        raise ValueError("Islem bulunamadi.")

    desc_lower = tx.description.lower()
    matched_keyword = None
    method = "fallback"
    alternatives = []

    # Hangi kelime eslesti?
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                if cat == tx.category:
                    matched_keyword = kw
                    method = "kural"
                else:
                    alternatives.append(cat)
                break

    confidence = float(tx.category_confidence or 0.5)
    if confidence >= 0.9:
        method = "kural"
    elif confidence >= 0.6:
        method = "embedding"

    explanation = _category_explanation(tx.description, tx.category, matched_keyword, method, confidence)

    return CategoryExplanation(
        transaction_id=str(tx.id),
        description=tx.description,
        category=tx.category or "kategorisiz",
        method=method,
        matched_keyword=matched_keyword,
        confidence=confidence,
        alternative_categories=list(set(alternatives))[:3],
        explanation=explanation,
    )


def explain_health_score(db: Session, account_id: uuid.UUID) -> HealthScoreExplanation:
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).all()

    if not transactions:
        return HealthScoreExplanation(
            score=0, grade="F",
            factors=[],
            improvement_tips=["Hesaba islem yukleyin ve AI analizini calistirin."],
            explanation="Yeterli veri yok.",
        )

    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
    savings_rate = (total_income - total_expense) / total_income * 100 if total_income > 0 else 0
    flagged = sum(1 for t in transactions if t.is_flagged)
    categories = set(t.category for t in transactions if t.category)

    factors = []
    tips = []

    # Tasarruf oranı
    sav_score = min(int(savings_rate * 3.33), 100)
    factors.append({
        "name": "Tasarruf Orani",
        "score": sav_score,
        "weight": "35%",
        "detail": f"Gelirinizin %{savings_rate:.1f}'ini tasarruf ediyorsunuz.",
        "reason": "Yuksek tasarruf orani finansal sagligin en onemli gostergesidir.",
    })
    if savings_rate < 20:
        tips.append("Tasarruf oraninizi artirmak icin aylik harcama butcesi belirleyin.")

    # Gider çeşitliliği
    div_score = min(len(categories) * 12, 100)
    factors.append({
        "name": "Gider Cesitliligi",
        "score": div_score,
        "weight": "20%",
        "detail": f"{len(categories)} farkli kategoride harcama yapiyorsunuz.",
        "reason": "Dengeli harcama dagilimlari finansal risk azaltir.",
    })

    # Fraud riski
    fraud_pct = flagged / len(transactions) * 100
    fraud_score = max(100 - int(fraud_pct * 10), 0)
    factors.append({
        "name": "Fraud Riski",
        "score": fraud_score,
        "weight": "20%",
        "detail": f"{flagged} supheli islem var (%{fraud_pct:.1f}).",
        "reason": "Supheli islem orani ne kadar dusukse risk o kadar azdir.",
    })
    if flagged > 0:
        tips.append(f"{flagged} supheli islemi inceleyip banka ile iletisime gecin.")

    # Genel skor
    total_score = int(sav_score * 0.35 + div_score * 0.20 + fraud_score * 0.20 + 50 * 0.25)
    grade = "A" if total_score >= 85 else "B" if total_score >= 70 else "C" if total_score >= 55 else "D"

    explanation = (
        f"Finansal saglik skoRunuz {total_score}/100 ({grade}). "
        f"En guclu yonunuz: tasarruf orani (%{savings_rate:.1f}). "
    )
    if flagged > 0:
        explanation += f"Dikkat edilmesi gereken: {flagged} supheli islem. "
    if not tips:
        explanation += "Genel olarak finansal durumunuz saglikli gorunuyor."

    return HealthScoreExplanation(
        score=total_score,
        grade=grade,
        factors=factors,
        improvement_tips=tips or ["Mevcut tasarruf aliskanliklarinizi koruyun."],
        explanation=explanation,
    )


def explain_recommendation(
    db: Session,
    account_id: uuid.UUID,
    recommendation_type: str,
) -> RecommendationExplanation:
    transactions = db.query(Transaction).filter(Transaction.account_id == account_id).all()

    dates = [t.transaction_date for t in transactions]
    months = max((max(dates) - min(dates)).days / 30, 1) if dates else 1

    cat_totals: dict[str, float] = defaultdict(float)
    cat_counts: dict[str, int] = defaultdict(int)
    for t in transactions:
        if float(t.amount) < 0 and t.category:
            cat_totals[t.category] += abs(float(t.amount)) / months
            cat_counts[t.category] += 1

    if recommendation_type == "yemek_azalt":
        monthly = cat_totals.get("yemek", 0)
        return RecommendationExplanation(
            recommendation_type="yemek_azalt",
            title="Yemek harcamalarinizi azaltin",
            reasoning=[
                f"Aylik ortalama {monthly:.0f} TL yemek harciyorsunuz",
                f"Bu, ayda {cat_counts.get('yemek', 0)} yemek siparisi/dis yemek demek",
                "Finansal sagligi yuksek bireylerin yemek harcamasi genellikle gelirin %10'u altinda",
            ],
            data_points=[
                {"label": "Aylik yemek harcamasi", "value": f"{monthly:.0f} TL"},
                {"label": "Potansiyel tasarruf (%25)", "value": f"{monthly*0.25:.0f} TL/ay"},
                {"label": "Yillik tasarruf", "value": f"{monthly*0.25*12:.0f} TL"},
            ],
            confidence="yuksek" if monthly > 500 else "orta",
            explanation=f"Aylik {monthly:.0f} TL yemek harcamaniz toplam giderinizin onemli bir kismini olusturuyor. Haftada 2-3 gun evde yemek pisirerek bu tutari kolayca azaltabilirsiniz.",
        )

    elif recommendation_type == "abonelik_optimize":
        sub_monthly = sum(v for k, v in cat_totals.items() if k == "abonelik")
        return RecommendationExplanation(
            recommendation_type="abonelik_optimize",
            title="Aboneliklerinizi optimize edin",
            reasoning=[
                f"Aylik {sub_monthly:.0f} TL abonelik oduyorsunuz",
                "Birden fazla video/muzik platformuna abone olabilirsiniz",
                "Kullanilmayan abonelikler sessizce para tuketur",
            ],
            data_points=[
                {"label": "Aylik abonelik toplami", "value": f"{sub_monthly:.0f} TL"},
                {"label": "Optimize sonrasi tasarruf", "value": f"{sub_monthly*0.3:.0f} TL/ay"},
            ],
            confidence="orta",
            explanation=f"Abonelik harcamaniz aylik {sub_monthly:.0f} TL. Son 3 ayda hangi platformlari aktif kullandiginizi gozden gecirerek gereksizleri iptal edin.",
        )

    return RecommendationExplanation(
        recommendation_type=recommendation_type,
        title="Genel tasarruf onerisi",
        reasoning=["Harcama verilerinize gore olusturuldu"],
        data_points=[],
        confidence="orta",
        explanation="Harcama verinize dayanarak genel bir tasarruf onerisi.",
    )


def _fraud_recommendation(risk_level: str, reasons: list[str]) -> str:
    if risk_level == "kritik":
        return "Bu islemi hemen bankanizla dogrulayin. Yetkisiz islem olabilir, kartinizi gecici olarak dondurmayi dusunun."
    elif risk_level == "yuksek":
        return "Bu islemi taniyor musunuz? Tanimiyorsaniz bankanizi arayin."
    elif risk_level == "orta":
        return "Bu islem bazi risk sinyalleri tasiyor. Kaydinizdaki bilgilerle karsilastirin."
    return "Dusuk risk. Yine de tanimadiginiz islemler icin bankanizi arayin."


def _category_explanation(desc: str, category: str, keyword: str, method: str, confidence: float) -> str:
    if method == "kural" and keyword:
        return f"'{desc}' aciklamasinda '{keyword}' anahtar kelimesi bulundu. Bu kelime '{category}' kategorisiyle eslestirildi. (Guven: %{confidence*100:.0f})"
    elif method == "embedding":
        return f"'{desc}' aciklamasi, '{category}' kategorisindeki islemlerle metin benzerligi analizi ile eslestirildi. (Guven: %{confidence*100:.0f})"
    return f"'{desc}' aciklamasi hicbir kuralla eslesmedi, varsayilan kategori atandi."
