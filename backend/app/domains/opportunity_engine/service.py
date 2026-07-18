"""
AI Opportunity Engine servisi.

İşlem verilerini analiz ederek:
1. Abonelik harcamalarını tespit eder ve optimize eder
2. Yüksek merchant harcamalarını bulur
3. Tekrar eden gereksiz harcamaları tespit eder
4. Somut, uygulanabilir tasarruf fırsatları üretir
"""
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.opportunity_engine.schemas import Opportunity, OpportunityReport
from app.domains.transactions.models import Transaction

# Bilinen abonelik servisleri
SUBSCRIPTION_KEYWORDS = [
    "netflix", "spotify", "youtube", "amazon prime", "evernote",
    "icloud", "dropbox", "microsoft 365", "office 365", "adobe",
    "apple tv", "disney", "blutv", "gain tv", "tod", "mubi",
    "linkedin premium", "canva", "figma", "notion", "slack",
]

# Azaltılabilir harcama kategorileri
REDUCIBLE_CATEGORIES = {
    "yemek": {"reduction": 0.25, "tip": "Haftada 1-2 gun yemek siparisi vermek yerine evde pisirin"},
    "alisveris": {"reduction": 0.20, "tip": "Aylık alışveriş listesi yaparak impuls alımları azaltın"},
    "ulasim": {"reduction": 0.15, "tip": "Toplu taşıma veya karpoling ile ulaşım maliyetini düşürün"},
    "market": {"reduction": 0.10, "tip": "İndirim günlerini takip edin ve toplu alım yapın"},
}


def analyze(db: Session, account_id: uuid.UUID) -> OpportunityReport:
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    if not transactions:
        return _empty_report()

    # Aylık veri aralığı
    dates = [t.transaction_date for t in transactions]
    days = max((max(dates) - min(dates)).days, 1)
    months = max(days / 30, 1)

    expenses = [t for t in transactions if float(t.amount) < 0]

    opportunities: list[Opportunity] = []

    # 1. Abonelik analizi
    sub_opps = _analyze_subscriptions(expenses, months)
    opportunities.extend(sub_opps)

    # 2. Yüksek harcamalı kategoriler
    cat_opps = _analyze_categories(expenses, months)
    opportunities.extend(cat_opps)

    # 3. Tekrar eden yüksek tutarlı harcamalar
    merchant_opps = _analyze_merchants(expenses, months)
    opportunities.extend(merchant_opps)

    # Önceliğe göre sırala, max 8
    priority_order = {"yuksek": 0, "orta": 1, "dusuk": 2}
    opportunities.sort(key=lambda x: priority_order.get(x.priority, 3))
    opportunities = opportunities[:8]

    total_monthly = sum(o.monthly_saving for o in opportunities)
    total_annual = total_monthly * 12

    # Abonelik toplamı
    sub_total = _get_subscription_total(expenses, months)

    # En çok harcanan merchant'lar
    top_merchants = _get_top_merchants(expenses, months)

    # Fırsat skoru (ne kadar fazla fırsat = yüksek skor)
    score = min(int(float(total_monthly) / 500 * 100), 100)
    score = max(score, 10 if opportunities else 0)

    summary = _generate_summary(opportunities, total_monthly, sub_total)

    return OpportunityReport(
        opportunity_score=score,
        total_monthly_saving=total_monthly,
        total_annual_saving=total_annual,
        opportunities=opportunities,
        summary=summary,
        subscriptions_total=sub_total,
        top_merchant_waste=top_merchants,
    )


def _analyze_subscriptions(expenses: list[Transaction], months: float) -> list[Opportunity]:
    """Abonelik harcamalarını tespit et."""
    opps = []
    sub_totals: dict[str, float] = defaultdict(float)
    sub_counts: dict[str, int] = defaultdict(int)

    for tx in expenses:
        desc = tx.description.lower()
        for keyword in SUBSCRIPTION_KEYWORDS:
            if keyword in desc:
                sub_totals[keyword] += abs(float(tx.amount)) / months
                sub_counts[keyword] += 1
                break

    # Birden fazla video aboneliği var mı?
    video_subs = {k: v for k, v in sub_totals.items() if k in ["netflix", "youtube", "blutv", "gain tv", "tod", "mubi", "apple tv", "disney"]}
    if len(video_subs) >= 2:
        total_video = sum(video_subs.values())
        cheapest = min(video_subs.values())
        saving = total_video - cheapest
        opps.append(Opportunity(
            type="abonelik",
            title="Birden fazla video platformu aboneliginiz var",
            description=f"{', '.join(video_subs.keys())} aboneliklerine toplam aylik {total_video:.0f} TL oduyorsunuz. En ucuzunu tutup digerlerini iptal etseniz {saving:.0f} TL tasarruf edersiniz.",
            monthly_saving=Decimal(str(round(saving, 2))),
            annual_saving=Decimal(str(round(saving * 12, 2))),
            priority="yuksek",
            category="abonelik",
            action=f"En az kullandiginiz platformu iptal edin. Aylik {saving:.0f} TL tasarruf.",
        ))

    # Birden fazla muzik aboneliği
    music_subs = {k: v for k, v in sub_totals.items() if k in ["spotify", "youtube"]}
    if len(music_subs) >= 2:
        saving = min(music_subs.values())
        opps.append(Opportunity(
            type="abonelik",
            title="Cakisan muzik abonelikleri",
            description=f"Hem Spotify hem YouTube Premium kullaniyorsunuz. Birini iptal ederek aylik {saving:.0f} TL tasarruf edebilirsiniz.",
            monthly_saving=Decimal(str(round(saving, 2))),
            annual_saving=Decimal(str(round(saving * 12, 2))),
            priority="orta",
            category="abonelik",
            action="YouTube Music veya Spotify'dan birini sectikten sonra digerini iptal edin.",
        ))

    # Toplam abonelik yuku fazlaysa
    total_subs = sum(sub_totals.values())
    if total_subs > 500 and len(video_subs) < 2:
        opps.append(Opportunity(
            type="abonelik",
            title="Yuksek abonelik maliyeti",
            description=f"Aylik toplam {total_subs:.0f} TL abonelik oduyorsunuz. Kullanmadiginiz servisleri iptal etmeyi dusunun.",
            monthly_saving=Decimal(str(round(total_subs * 0.3, 2))),
            annual_saving=Decimal(str(round(total_subs * 0.3 * 12, 2))),
            priority="orta",
            category="abonelik",
            action="Son 3 aydir kullanmadiginiz abonelikleri gozden gecirin ve iptal edin.",
        ))

    return opps


def _analyze_categories(expenses: list[Transaction], months: float) -> list[Opportunity]:
    """Yüksek harcamalı kategorileri analiz et."""
    opps = []
    cat_totals: dict[str, float] = defaultdict(float)

    for tx in expenses:
        cat = tx.category or "kategorisiz"
        cat_totals[cat] += abs(float(tx.amount)) / months

    for cat, monthly_spend in cat_totals.items():
        if cat in REDUCIBLE_CATEGORIES and monthly_spend > 300:
            reduction_pct = REDUCIBLE_CATEGORIES[cat]["reduction"]
            tip = REDUCIBLE_CATEGORIES[cat]["tip"]
            saving = monthly_spend * reduction_pct

            opps.append(Opportunity(
                type="yuksek_harcama",
                title=f"{cat.capitalize()} harcamanizi optimize edin",
                description=f"Aylik ortalama {monthly_spend:.0f} TL {cat} harciyorsunuz. %{int(reduction_pct*100)} azaltmayla aylik {saving:.0f} TL tasarruf mumkun.",
                monthly_saving=Decimal(str(round(saving, 2))),
                annual_saving=Decimal(str(round(saving * 12, 2))),
                priority="orta" if monthly_spend < 1000 else "yuksek",
                category=cat,
                action=tip,
            ))

    return opps[:3]


def _analyze_merchants(expenses: list[Transaction], months: float) -> list[Opportunity]:
    """Tekrar eden yüksek harcamalı merchant'ları analiz et."""
    opps = []
    merchant_totals: dict[str, float] = defaultdict(float)
    merchant_counts: dict[str, int] = defaultdict(int)

    for tx in expenses:
        desc = tx.description.lower()
        # Abonelik olmayanları al
        is_sub = any(kw in desc for kw in SUBSCRIPTION_KEYWORDS)
        if not is_sub:
            merchant_totals[tx.description] += abs(float(tx.amount)) / months
            merchant_counts[tx.description] += 1

    # Ayda 3+ kez gidilen yerler
    frequent = {k: v for k, v in merchant_totals.items() if merchant_counts[k] >= 3 and v > 200}
    for merchant, monthly in sorted(frequent.items(), key=lambda x: x[1], reverse=True)[:2]:
        saving = monthly * 0.20
        opps.append(Opportunity(
            type="tekrar_eden",
            title=f"Sik tekrar eden: {merchant}",
            description=f"'{merchant}' icin ayda {merchant_counts[merchant]} kez, toplam {monthly:.0f} TL oduyorsunuz. Sikligi azaltarak tasarruf edebilirsiniz.",
            monthly_saving=Decimal(str(round(saving, 2))),
            annual_saving=Decimal(str(round(saving * 12, 2))),
            priority="dusuk",
            category="tekrar_eden",
            action=f"Ayda {max(merchant_counts[merchant]-1, 1)} kez ile sinirlandirin.",
        ))

    return opps


def _get_subscription_total(expenses: list[Transaction], months: float) -> Decimal:
    total = 0.0
    for tx in expenses:
        desc = tx.description.lower()
        if any(kw in desc for kw in SUBSCRIPTION_KEYWORDS) or (tx.category == "abonelik"):
            total += abs(float(tx.amount)) / months
    return Decimal(str(round(total, 2)))


def _get_top_merchants(expenses: list[Transaction], months: float) -> list[dict]:
    merchant_totals: dict[str, float] = defaultdict(float)
    for tx in expenses:
        merchant_totals[tx.description] += abs(float(tx.amount)) / months

    top = sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    return [{"merchant": k, "monthly": round(v, 2)} for k, v in top]


def _generate_summary(opportunities: list[Opportunity], total_monthly: Decimal, sub_total: Decimal) -> str:
    if not opportunities:
        return "Harcamalariniz oldukca optimize gorunuyor. Buyuk bir tasarruf firsati tespit edilmedi."

    count = len(opportunities)
    high_priority = sum(1 for o in opportunities if o.priority == "yuksek")

    summary = f"{count} tasarruf firsati tespit edildi."
    if float(total_monthly) > 0:
        summary += f" Bu onerileri uygularsaniz aylik {float(total_monthly):.0f} TL, yillik {float(total_monthly)*12:.0f} TL tasarruf edebilirsiniz."
    if high_priority > 0:
        summary += f" {high_priority} tanesi yuksek oncelikli."
    if float(sub_total) > 300:
        summary += f" Abonelik harcamaniz aylik {float(sub_total):.0f} TL — gozden gecirmenizi oneririz."

    return summary


def _empty_report() -> OpportunityReport:
    return OpportunityReport(
        opportunity_score=0,
        total_monthly_saving=Decimal("0"),
        total_annual_saving=Decimal("0"),
        opportunities=[],
        summary="Analiz icin yeterli veri bulunamadi.",
        subscriptions_total=Decimal("0"),
        top_merchant_waste=[],
    )
