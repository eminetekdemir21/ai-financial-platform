"""
What-If Simulation Engine.

Kullanicinin tanimladigi senaryoyu mevcut gelir/gider verisine uygular,
secilen sureye gore bir projeksiyon uretir ve AI yorumu ekler.
Ayrica senaryolarin kaydedilmesini ve gecmisinin listelenmesini saglar.
"""
import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.simulation.models import SavedScenario
from app.domains.simulation.schemas import (
    MonthlyProjection,
    SavedScenarioDetail,
    SavedScenarioSummary,
    SimulationRequest,
    SimulationResult,
)
from app.domains.transactions.models import Transaction


def run_simulation(
    db: Session,
    account_id: uuid.UUID,
    request: SimulationRequest,
) -> SimulationResult:
    """
    Senaryoyu calistirir:
    1. Mevcut aylik ortalama gelir/gider hesaplanir
    2. Senaryo degisiklikleri uygulanir
    3. Secilen sureye (horizon_months) gore projeksiyon uretilir
    4. AI yorumu eklenir
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    # Mevcut aylik ortalamalar
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)

    if transactions:
        dates = [t.transaction_date for t in transactions]
        days = max((max(dates) - min(dates)).days, 1)
        months = max(days / 30, 1)
    else:
        months = 1

    monthly_income = Decimal(str(round(total_income / months, 2)))
    monthly_expense = Decimal(str(round(total_expense / months, 2)))
    monthly_savings = monthly_income - monthly_expense

    # Kategori bazli mevcut giderler
    category_totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        if float(t.amount) < 0 and t.category:
            category_totals[t.category] += abs(float(t.amount)) / months

    # Simule edilmis gelir
    sim_income = monthly_income + request.income_change

    # Simule edilmis gider - kategori degisikliklerini uygula
    sim_expense = monthly_expense
    for category, change in request.category_changes.items():
        cat_spend = Decimal(str(category_totals.get(category, 0)))
        if cat_spend > 0:
            if -1 < float(change) < 0:
                # Yuzde bazli azaltma (orn. -0.30 = %30 azalt)
                reduction = cat_spend * abs(change)
                sim_expense -= reduction
            else:
                # Mutlak deger azaltma (orn. -500 TL)
                sim_expense += change  # change negatif gelirse azaltir

    sim_savings = sim_income - sim_expense

    # Tek seferlik harcama farki
    savings_diff = sim_savings - monthly_savings
    annual_diff = savings_diff * 12

    # Secilen sureye gore projeksiyon
    horizon = request.horizon_months
    projections = []
    cumulative = Decimal("0")
    for month in range(1, horizon + 1):
        one_time = request.one_time_expense if month == 1 else Decimal("0")
        month_expense = sim_expense + one_time
        month_net = sim_income - month_expense
        cumulative += month_net
        projections.append(
            MonthlyProjection(
                month=month,
                income=sim_income,
                expense=month_expense,
                net_savings=month_net,
                cumulative_savings=cumulative,
            )
        )

    # Etki seviyesi ve AI yorumu
    impact_level = _impact_level(savings_diff)
    ai_summary = _generate_summary(
        request=request,
        current_savings=monthly_savings,
        sim_savings=sim_savings,
        savings_diff=savings_diff,
        annual_diff=annual_diff,
        category_totals=category_totals,
    )

    return SimulationResult(
        description=request.description or "What-If Senaryosu",
        current_monthly_income=monthly_income,
        current_monthly_expense=monthly_expense,
        current_monthly_savings=monthly_savings,
        simulated_monthly_income=sim_income,
        simulated_monthly_expense=sim_expense,
        simulated_monthly_savings=sim_savings,
        savings_difference=savings_diff,
        annual_savings_difference=annual_diff,
        horizon_months=horizon,
        monthly_projections=projections,
        ai_summary=ai_summary,
        impact_level=impact_level,
    )


def _impact_level(savings_diff: Decimal) -> str:
    if float(savings_diff) > 100:
        return "positive"
    elif float(savings_diff) < -100:
        return "negative"
    return "neutral"


def _generate_summary(
    request: SimulationRequest,
    current_savings: Decimal,
    sim_savings: Decimal,
    savings_diff: Decimal,
    annual_diff: Decimal,
    category_totals: dict[str, float],
) -> str:
    parts = []
    if float(request.income_change) != 0:
        direction = "artarsa" if float(request.income_change) > 0 else "azalirsa"
        parts.append(
            f"Aylik geliriniz {abs(float(request.income_change)):.0f} TL {direction}"
        )

    for cat, change in request.category_changes.items():
        if -1 < float(change) < 0:
            parts.append(
                f"'{cat}' harcamalarinizi %{abs(float(change))*100:.0f} azaltirsaniz"
            )
        elif float(change) < 0:
            parts.append(
                f"'{cat}' harcamalarinizi {abs(float(change)):.0f} TL azaltirsaniz"
            )

    if float(request.one_time_expense) > 0:
        parts.append(
            f"{float(request.one_time_expense):.0f} TL'lik tek seferlik harcama yaparsaniz"
        )

    scenario_text = " ve ".join(parts) if parts else "Bu senaryo"

    diff_text = ""
    if float(savings_diff) > 0:
        diff_text = (
            f"aylik tasarrufunuz {float(savings_diff):.0f} TL artar "
            f"({float(current_savings):.0f} -> {float(sim_savings):.0f} TL). "
            f"Yillik {float(annual_diff):.0f} TL ekstra birikim elde edersiniz."
        )
    elif float(savings_diff) < 0:
        diff_text = (
            f"aylik tasarrufunuz {abs(float(savings_diff)):.0f} TL azalir "
            f"({float(current_savings):.0f} -> {float(sim_savings):.0f} TL). "
            f"Yillik {abs(float(annual_diff)):.0f} TL daha az birikim yaparsiniz."
        )
    else:
        diff_text = "aylik tasarrufunuz degismez."

    return f"{scenario_text}, {diff_text}"


def save_scenario(
    db: Session,
    account_id: uuid.UUID,
    name: str,
    request: SimulationRequest,
) -> SavedScenarioDetail:
    """
    Senaryoyu calistirir ve sonucuyla birlikte kaydeder.
    Sonuc, kaydedildigi andaki haliyle JSONB olarak saklanir; ileride
    islemler degisse bile bu kayit ayni sonucu gosterir.
    """
    result = run_simulation(db=db, account_id=account_id, request=request)

    row = SavedScenario(
        account_id=account_id,
        name=name.strip() or result.description,
        request_payload=request.model_dump(mode="json"),
        result_snapshot=result.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return SavedScenarioDetail(
        id=row.id,
        name=row.name,
        created_at=row.created_at,
        request=request,
        result=result,
    )


def list_scenarios(db: Session, account_id: uuid.UUID) -> list[SavedScenarioSummary]:
    """Hesaba ait kaydedilmis senaryolari en yeniden eskiye listeler."""
    rows = (
        db.query(SavedScenario)
        .filter(SavedScenario.account_id == account_id)
        .order_by(SavedScenario.created_at.desc())
        .all()
    )
    return [
        SavedScenarioSummary(
            id=row.id,
            name=row.name,
            impact_level=row.result_snapshot["impact_level"],
            savings_difference=row.result_snapshot["savings_difference"],
            annual_savings_difference=row.result_snapshot["annual_savings_difference"],
            horizon_months=row.result_snapshot.get("horizon_months", 12),
            created_at=row.created_at,
        )
        for row in rows
    ]


def get_scenario(
    db: Session,
    account_id: uuid.UUID,
    scenario_id: uuid.UUID,
) -> SavedScenarioDetail | None:
    """Tek bir kayitli senaryonun tam detayini getirir."""
    row = (
        db.query(SavedScenario)
        .filter(SavedScenario.account_id == account_id, SavedScenario.id == scenario_id)
        .first()
    )
    if row is None:
        return None
    return SavedScenarioDetail(
        id=row.id,
        name=row.name,
        created_at=row.created_at,
        request=SimulationRequest(**row.request_payload),
        result=SimulationResult(**row.result_snapshot),
    )


def delete_scenario(
    db: Session,
    account_id: uuid.UUID,
    scenario_id: uuid.UUID,
) -> bool:
    """Kayitli senaryoyu siler. Bulunamazsa False doner."""
    row = (
        db.query(SavedScenario)
        .filter(SavedScenario.account_id == account_id, SavedScenario.id == scenario_id)
        .first()
    )
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True
