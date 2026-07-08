"""
Finansal sağlık skoru hesaplama algoritması.

Her faktör 0-100 arası normalize edilir, sonra ağırlıklı
ortalamaları alınarak tek bir genel skor üretilir.

Bu yaklaşım, bankacılık sektöründe kullanılan kredi skoru
metodolojisine (FICO, KKB) benzer mantıkla çalışır:
birden fazla faktörü şeffaf, açıklanabilir ağırlıklarla
birleştirerek tek bir sayıya indirgeme.
"""
from collections import defaultdict
from decimal import Decimal
from typing import List

from app.domains.transactions.models import Transaction

# --- Faktör ağırlıkları (toplam = 1.0) ---
WEIGHTS = {
    "savings_rate": 0.35,      # Tasarruf oranı — en kritik gösterge
    "expense_diversity": 0.20, # Gider çeşitliliği — tek kategoriye bağımlılık riski
    "fraud_risk": 0.20,        # Fraud riski — şüpheli işlem oranı
    "income_stability": 0.15,  # Düzenli gelir — istikrar göstergesi
    "spending_trend": 0.10,    # Harcama trendi — artıyor mu, azalıyor mu
}


def calculate_savings_rate_score(transactions: List[Transaction]) -> tuple[float, str]:
    """
    Tasarruf oranı skoru (0-100).
    Gelirin ne kadarı tasarruf edildiğini ölçer.
    Oran >= %30: 100 puan | %20-30: 75 | %10-20: 50 | %0-10: 25 | negatif: 0
    """
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expense = abs(sum(t.amount for t in transactions if t.amount < 0))

    if total_income == 0:
        return 0.0, "Gelir verisi bulunamadı."

    net_savings = total_income - total_expense
    savings_rate = float(net_savings / total_income)

    if savings_rate >= 0.30:
        score, comment = 100.0, f"Mükemmel: gelirinizin %{savings_rate*100:.0f}'ini tasarruf ediyorsunuz."
    elif savings_rate >= 0.20:
        score, comment = 75.0, f"İyi: gelirinizin %{savings_rate*100:.0f}'ini tasarruf ediyorsunuz."
    elif savings_rate >= 0.10:
        score, comment = 50.0, f"Orta: gelirinizin yalnızca %{savings_rate*100:.0f}'ini tasarruf ediyorsunuz."
    elif savings_rate >= 0.0:
        score, comment = 25.0, f"Dikkat: gelirinizin %{savings_rate*100:.0f}'ini tasarruf ediyorsunuz."
    else:
        score, comment = 0.0, f"Kritik: giderleriniz gelirinizi aşıyor ({savings_rate*100:.0f}%)."

    return score, comment


def calculate_expense_diversity_score(transactions: List[Transaction]) -> tuple[float, str]:
    """
    Gider çeşitliliği skoru (0-100).
    Hierfindahl-Hirschman Index (HHI) mantığıyla: tek kategoriye
    aşırı bağımlılık düşük skor, dengeli dağılım yüksek skor verir.
    """
    expenses = [t for t in transactions if t.amount < 0 and t.category]
    if not expenses:
        return 50.0, "Kategorilendirme verisi yetersiz."

    total = sum(abs(t.amount) for t in expenses)
    category_totals = defaultdict(Decimal)
    for t in expenses:
        category_totals[t.category] += abs(t.amount)

    # Her kategorinin oranının karesi toplamı = konsantrasyon indeksi
    hhi = sum((float(v / total) ** 2) for v in category_totals.values())
    n = len(category_totals)

    # HHI: 1.0 = tek kategoride yoğunlaşma (kötü), 1/n = mükemmel dağılım
    if n == 1:
        score = 20.0
        comment = f"Tüm harcamalarınız tek kategoride ({list(category_totals.keys())[0]})."
    elif hhi < 0.25:
        score = 100.0
        comment = f"Mükemmel: {n} farklı kategoride dengeli harcama."
    elif hhi < 0.40:
        score = 75.0
        comment = f"İyi: {n} kategoride görece dengeli harcama."
    elif hhi < 0.60:
        score = 50.0
        comment = f"Orta: bazı kategorilerde yoğunlaşma var ({n} kategori)."
    else:
        dominant = max(category_totals, key=lambda k: category_totals[k])
        score = 25.0
        comment = f"Dikkat: harcamalarınız ağırlıklı olarak '{dominant}' kategorisinde."

    return score, comment


def calculate_fraud_risk_score(transactions: List[Transaction]) -> tuple[float, str]:
    """
    Fraud riski skoru (0-100).
    Şüpheli işlem oranı düşüldükçe skor artar.
    0 şüpheli = 100 | <%5 = 75 | <%10 = 50 | <%20 = 25 | >=%20 = 0
    """
    if not transactions:
        return 100.0, "Analiz edilecek işlem bulunamadı."

    flagged = sum(1 for t in transactions if t.is_flagged)
    ratio = flagged / len(transactions)

    if flagged == 0:
        score, comment = 100.0, "Hiç şüpheli işlem tespit edilmedi."
    elif ratio < 0.05:
        score, comment = 75.0, f"{flagged} şüpheli işlem tespit edildi (işlemlerin %{ratio*100:.1f}'i)."
    elif ratio < 0.10:
        score, comment = 50.0, f"Dikkat: {flagged} şüpheli işlem var (%{ratio*100:.1f})."
    elif ratio < 0.20:
        score, comment = 25.0, f"Yüksek risk: {flagged} şüpheli işlem (%{ratio*100:.1f})."
    else:
        score, comment = 0.0, f"Kritik: işlemlerinizin %{ratio*100:.1f}'i şüpheli işaretlendi."

    return score, comment


def calculate_income_stability_score(transactions: List[Transaction]) -> tuple[float, str]:
    """
    Gelir istikrarı skoru (0-100).
    Düzenli (aylık) gelir girişleri varlığına ve tutarlılığına göre.
    """
    income_txs = [t for t in transactions if t.amount > 0 and t.category == "gelir"]

    if not income_txs:
        # Gelir kategorisi yok ama pozitif işlemler varsa
        positive = [t for t in transactions if t.amount > 0]
        if positive:
            return 40.0, "Gelir işlemleri kategorilendirilemedi, analiz kısıtlı."
        return 20.0, "Kayıtlı gelir işlemi bulunamadı."

    if len(income_txs) >= 2:
        amounts = [float(t.amount) for t in income_txs]
        avg = sum(amounts) / len(amounts)
        variance = sum((a - avg) ** 2 for a in amounts) / len(amounts)
        cv = (variance ** 0.5) / avg if avg > 0 else 1.0  # Değişim katsayısı

        if cv < 0.05:
            return 100.0, f"Mükemmel: {len(income_txs)} düzenli gelir girişi, tutarlar çok istikrarlı."
        elif cv < 0.15:
            return 75.0, f"İyi: {len(income_txs)} gelir girişi, küçük dalgalanmalar var."
        else:
            return 50.0, f"Orta: {len(income_txs)} gelir girişi ama tutarlar değişken."
    else:
        return 60.0, "Tek gelir kaydı mevcut, trend analizi için yetersiz veri."


def calculate_spending_trend_score(transactions: List[Transaction]) -> tuple[float, str]:
    """
    Harcama trendi skoru (0-100).
    İşlemleri tarihe göre ikiye böler: ilk yarı vs ikinci yarı.
    Giderler azalıyorsa yüksek skor, artıyorsa düşük skor.
    """
    expenses = sorted(
        [t for t in transactions if t.amount < 0],
        key=lambda t: t.transaction_date,
    )

    if len(expenses) < 4:
        return 50.0, "Trend analizi için yetersiz işlem sayısı (en az 4 gider gerekli)."

    mid = len(expenses) // 2
    first_half = sum(abs(t.amount) for t in expenses[:mid])
    second_half = sum(abs(t.amount) for t in expenses[mid:])

    if first_half == 0:
        return 50.0, "Trend hesaplanamadı."

    change = float((second_half - first_half) / first_half)

    if change <= -0.10:
        return 100.0, f"Mükemmel: harcamalarınız %{abs(change)*100:.0f} azaldı."
    elif change <= 0.0:
        return 75.0, "İyi: harcamalarınız stabil veya hafif azalıyor."
    elif change <= 0.10:
        return 50.0, f"Dikkat: harcamalarınız %{change*100:.0f} arttı."
    elif change <= 0.25:
        return 25.0, f"Uyarı: harcamalarınız %{change*100:.0f} arttı."
    else:
        return 0.0, f"Kritik: harcamalarınız %{change*100:.0f} arttı."


def calculate_health_score(transactions: List[Transaction]) -> dict:
    """
    Ana fonksiyon: tüm faktörleri hesaplayıp ağırlıklı skor döndürür.
    """
    if not transactions:
        return {
            "score": 0,
            "grade": "N/A",
            "breakdown": {},
            "summary": "Skor hesaplamak için yeterli işlem verisi yok.",
        }

    savings_score, savings_comment = calculate_savings_rate_score(transactions)
    diversity_score, diversity_comment = calculate_expense_diversity_score(transactions)
    fraud_score, fraud_comment = calculate_fraud_risk_score(transactions)
    stability_score, stability_comment = calculate_income_stability_score(transactions)
    trend_score, trend_comment = calculate_spending_trend_score(transactions)

    total_score = (
        savings_score * WEIGHTS["savings_rate"]
        + diversity_score * WEIGHTS["expense_diversity"]
        + fraud_score * WEIGHTS["fraud_risk"]
        + stability_score * WEIGHTS["income_stability"]
        + trend_score * WEIGHTS["spending_trend"]
    )
    total_score = round(total_score, 1)

    if total_score >= 80:
        grade = "A"
    elif total_score >= 65:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    elif total_score >= 35:
        grade = "D"
    else:
        grade = "F"

    return {
        "score": total_score,
        "grade": grade,
        "breakdown": {
            "savings_rate": {
                "score": savings_score,
                "weight": WEIGHTS["savings_rate"],
                "comment": savings_comment,
                "label": "Tasarruf Oranı",
            },
            "expense_diversity": {
                "score": diversity_score,
                "weight": WEIGHTS["expense_diversity"],
                "comment": diversity_comment,
                "label": "Gider Çeşitliliği",
            },
            "fraud_risk": {
                "score": fraud_score,
                "weight": WEIGHTS["fraud_risk"],
                "comment": fraud_comment,
                "label": "Fraud Riski",
            },
            "income_stability": {
                "score": stability_score,
                "weight": WEIGHTS["income_stability"],
                "comment": stability_comment,
                "label": "Gelir İstikrarı",
            },
            "spending_trend": {
                "score": trend_score,
                "weight": WEIGHTS["spending_trend"],
                "comment": trend_comment,
                "label": "Harcama Trendi",
            },
        },
        "summary": _generate_summary(total_score, grade),
    }


def _generate_summary(score: float, grade: str) -> str:
    summaries = {
        "A": "Finansal durumunuz mükemmel. Tasarruf alışkanlıklarınızı koruyun.",
        "B": "Finansal durumunuz iyi. Birkaç alanda iyileştirme yapabilirsiniz.",
        "C": "Finansal durumunuz orta seviyede. Harcama alışkanlıklarınızı gözden geçirin.",
        "D": "Finansal durumunuz dikkat gerektiriyor. Acil önlemler almanız önerilir.",
        "F": "Finansal durumunuz kritik. Bir finansal danışmanla görüşmenizi öneririz.",
    }
    return summaries.get(grade, "")
