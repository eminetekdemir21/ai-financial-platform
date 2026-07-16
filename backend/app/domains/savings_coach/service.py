"""
AI Savings Coach servisi.

Kullanıcının harcama geçmişini analiz eder, kategorilere göre
trend tespit eder ve kişiselleştirilmiş tasarruf önerileri üretir.
"""
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.savings_coach.schemas import (
    SavingTip,
    SavingsCoachReport,
    SpendingTrend,
)
from app.domains.transactions.models import Transaction

TARGET_SAVINGS_RATE = 20.0  # Hedef tasarruf oranı %20


def analyze(db: Session, account_id: uuid.UUID) -> SavingsCoachReport:
    """
    Hesabın tüm işlemlerini analiz edip kişiselleştirilmiş
    tasarruf raporu üretir.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .order_by(Transaction.transaction_date)
        .all()
    )

    if not transactions:
        return _empty_report()

    # Veri aralığını belirle
    dates = [t.transaction_date for t in transactions]
    total_days = max((max(dates) - min(dates)).days, 1)
    months = max(total_days / 30, 1)

    # Genel gelir/gider
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)
    monthly_income = Decimal(str(round(total_income / months, 2)))
    monthly_expense = Decimal(str(round(total_expense / months, 2)))

    # Tasarruf oranı
    savings_rate = float((monthly_income - monthly_expense) / monthly_income * 100) if float(monthly_income) > 0 else 0
    monthly_savings_gap = max(
        monthly_income * Decimal(str(TARGET_SAVINGS_RATE / 100)) - (monthly_income - monthly_expense),
        Decimal("0")
    )

    # İlk yarı vs ikinci yarı karşılaştırması (trend tespiti)
    mid_date = min(dates) + (max(dates) - min(dates)) / 2
    first_half = [t for t in transactions if t.transaction_date <= mid_date]
    second_half = [t for t in transactions if t.transaction_date > mid_date]

    first_months = max(total_days / 2 / 30, 1)
    second_months = max(total_days / 2 / 30, 1)

    first_cat: dict[str, float] = defaultdict(float)
    second_cat: dict[str, float] = defaultdict(float)

    for t in first_half:
        if float(t.amount) < 0 and t.category:
            first_cat[t.category] += abs(float(t.amount)) / first_months

    for t in second_half:
        if float(t.amount) < 0 and t.category:
            second_cat[t.category] += abs(float(t.amount)) / second_months

    all_categories = set(list(first_cat.keys()) + list(second_cat.keys()))

    spending_trends = []
    for cat in all_categories:
        prev = first_cat.get(cat, 0)
        curr = second_cat.get(cat, 0)
        if prev > 0:
            change_pct = round((curr - prev) / prev * 100, 1)
        elif curr > 0:
            change_pct = 100.0
        else:
            change_pct = 0.0

        if change_pct > 5:
            trend = "artiyor"
        elif change_pct < -5:
            trend = "azaliyor"
        else:
            trend = "stabil"

        spending_trends.append(SpendingTrend(
            category=cat,
            current_monthly=Decimal(str(round(curr, 2))),
            previous_monthly=Decimal(str(round(prev, 2))),
            change_pct=change_pct,
            trend=trend,
        ))

    # Kategorilere göre aylık ortalama harcama
    all_cat_totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        if float(t.amount) < 0 and t.category:
            all_cat_totals[t.category] += abs(float(t.amount)) / months

    # Tasarruf önerileri üret
    tips = _generate_tips(
        spending_trends=spending_trends,
        cat_totals=all_cat_totals,
        monthly_income=float(monthly_income),
        savings_rate=savings_rate,
    )

    potential_annual = sum(tip.monthly_saving_potential for tip in tips) * 12

    coach_message = _generate_coach_message(
        savings_rate=savings_rate,
        tips=tips,
        spending_trends=spending_trends,
    )

    return SavingsCoachReport(
        total_monthly_income=monthly_income,
        total_monthly_expense=monthly_expense,
        current_savings_rate=round(savings_rate, 1),
        target_savings_rate=TARGET_SAVINGS_RATE,
        monthly_savings_gap=monthly_savings_gap,
        spending_trends=sorted(spending_trends, key=lambda x: abs(x.change_pct), reverse=True),
        tips=tips,
        coach_message=coach_message,
        potential_annual_savings=potential_annual,
    )


def _generate_tips(
    spending_trends: list[SpendingTrend],
    cat_totals: dict[str, float],
    monthly_income: float,
    savings_rate: float,
) -> list[SavingTip]:
    tips = []

    # Artan kategoriler için öneri
    for trend in spending_trends:
        if trend.trend == "artiyor" and float(trend.current_monthly) > 100:
            saving_10 = Decimal(str(round(float(trend.current_monthly) * 0.10, 2)))
            saving_20 = Decimal(str(round(float(trend.current_monthly) * 0.20, 2)))

            difficulty = "kolay" if float(trend.current_monthly) < 500 else "orta"
            priority = "yuksek" if trend.change_pct > 20 else "orta"

            tips.append(SavingTip(
                category=trend.category,
                title=f"{trend.category.capitalize()} harcamanızı azaltın",
                description=(
                    f"{trend.category.capitalize()} harcamanız son dönemde "
                    f"%{abs(trend.change_pct):.0f} arttı "
                    f"({float(trend.previous_monthly):.0f} → {float(trend.current_monthly):.0f} TL/ay). "
                    f"%20 azaltırsanız aylık {float(saving_20):.0f} TL tasarruf edersiniz."
                ),
                monthly_saving_potential=saving_20,
                annual_saving_potential=saving_20 * 12,
                difficulty=difficulty,
                priority=priority,
            ))

    # Yüksek harcamalı kategoriler için genel öneri
    high_spend_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    for cat, amount in high_spend_cats:
        if amount > monthly_income * 0.15:  # Gelirin %15'inden fazlası
            already_tip = any(t.category == cat for t in tips)
            if not already_tip:
                saving = Decimal(str(round(amount * 0.15, 2)))
                tips.append(SavingTip(
                    category=cat,
                    title=f"{cat.capitalize()} bütçenizi optimize edin",
                    description=(
                        f"{cat.capitalize()} kategorisi aylık gelirinizin önemli bir kısmını "
                        f"oluşturuyor ({amount:.0f} TL/ay). "
                        f"%15 azaltma ile aylık {float(saving):.0f} TL tasarruf mümkün."
                    ),
                    monthly_saving_potential=saving,
                    annual_saving_potential=saving * 12,
                    difficulty="orta",
                    priority="orta",
                ))

    # Genel tasarruf önerisi (tasarruf oranı düşükse)
    if savings_rate < TARGET_SAVINGS_RATE:
        tips.append(SavingTip(
            category="genel",
            title="Otomatik tasarruf planı oluşturun",
            description=(
                f"Mevcut tasarruf oranınız %{savings_rate:.0f} — "
                f"hedef oran %{TARGET_SAVINGS_RATE:.0f}. "
                "Her maaş günü gelirinizin %10'unu otomatik olarak "
                "ayrı bir birikime aktarın."
            ),
            monthly_saving_potential=Decimal(str(round(monthly_income * 0.05, 2))),
            annual_saving_potential=Decimal(str(round(monthly_income * 0.05 * 12, 2))),
            difficulty="kolay",
            priority="yuksek",
        ))

    return tips[:5]  # En fazla 5 öneri


def _generate_coach_message(
    savings_rate: float,
    tips: list[SavingTip],
    spending_trends: list[SpendingTrend],
) -> str:
    if savings_rate >= 30:
        intro = "Harika! Gelirinizin %{:.0f}'ini tasarruf ediyorsunuz — bu gerçekten etkileyici.".format(savings_rate)
    elif savings_rate >= 20:
        intro = "İyi gidiyorsunuz! %{:.0f} tasarruf oranınız sağlıklı bir seviyede.".format(savings_rate)
    elif savings_rate >= 10:
        intro = "Tasarruf oranınız (%{:.0f}) geliştirilebilir — küçük değişiklikler büyük fark yaratır.".format(savings_rate)
    else:
        intro = "Dikkat: Tasarruf oranınız (%{:.0f}) oldukça düşük. Birkaç basit adımla bunu iyileştirebilirsiniz.".format(savings_rate)

    rising = [t for t in spending_trends if t.trend == "artiyor"]
    if rising:
        cats = ", ".join([t.category for t in rising[:2]])
        intro += f" {cats.capitalize()} harcamalarınızda artış var — bunları kontrol altına almak iyi bir başlangıç olur."

    if tips:
        saving = sum(float(t.monthly_saving_potential) for t in tips)
        intro += f" Aşağıdaki önerileri uygularsanız aylık ortalama {saving:.0f} TL tasarruf edebilirsiniz."

    return intro


def _empty_report() -> SavingsCoachReport:
    return SavingsCoachReport(
        total_monthly_income=Decimal("0"),
        total_monthly_expense=Decimal("0"),
        current_savings_rate=0.0,
        target_savings_rate=TARGET_SAVINGS_RATE,
        monthly_savings_gap=Decimal("0"),
        spending_trends=[],
        tips=[],
        coach_message="Analiz için yeterli veri bulunamadı. Lütfen önce işlem yükleyin.",
        potential_annual_savings=Decimal("0"),
    )
