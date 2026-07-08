"""
AI Goal Planner servisi.

Kullanıcının finansal hedefini, mevcut gelir/gider verisine bakarak
analiz eder:
- Hedefe ulaşmak için aylık ne kadar biriktirmeli?
- Mevcut tasarruf oranıyla hedefe ulaşılabilir mi?
- Hangi harcama kategorilerini kısarsa ne kadar erken ulaşır?
"""
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domains.goal_planner.models import FinancialGoal
from app.domains.goal_planner.schemas import GoalAnalysis, GoalCreate, GoalResponse
from app.domains.transactions.models import Account, Transaction


def create_goal(
    db: Session, account_id: uuid.UUID, data: GoalCreate
) -> GoalResponse:
    goal = FinancialGoal(
        account_id=account_id,
        name=data.name,
        target_amount=data.target_amount,
        target_date=data.target_date,
        priority=data.priority,
        current_savings=data.current_savings,
        notes=data.notes,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _to_response(goal)


def list_goals(db: Session, account_id: uuid.UUID) -> list[GoalResponse]:
    goals = (
        db.query(FinancialGoal)
        .filter(
            FinancialGoal.account_id == account_id,
            FinancialGoal.status == "active",
        )
        .order_by(FinancialGoal.target_date)
        .all()
    )
    return [_to_response(g) for g in goals]


def delete_goal(db: Session, goal_id: uuid.UUID) -> None:
    goal = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id).first()
    if goal:
        goal.status = "cancelled"
        db.commit()


def analyze_goal(
    db: Session, goal_id: uuid.UUID, account_id: uuid.UUID
) -> GoalAnalysis:
    """
    Hedefe ulaşmak için gereken aylık tasarrufu hesaplar,
    mevcut harcama verisiyle karşılaştırır, öneriler üretir.
    """
    goal = db.query(FinancialGoal).filter(FinancialGoal.id == goal_id).first()
    if not goal:
        raise ValueError("Hedef bulunamadı.")

    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    # Mevcut aylık ortalama gelir ve gider
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    total_expense = sum(abs(float(t.amount)) for t in transactions if float(t.amount) < 0)

    # Kaç aylık veri var
    if transactions:
        dates = [t.transaction_date for t in transactions]
        date_range_days = (max(dates) - min(dates)).days + 1
        months_of_data = max(date_range_days / 30, 1)
    else:
        months_of_data = 1

    monthly_income = total_income / months_of_data
    monthly_expense = total_expense / months_of_data
    current_monthly_savings = monthly_income - monthly_expense

    # Hedefe kalan ay
    today = date.today()
    days_remaining = (goal.target_date - today).days
    months_remaining = max(int(days_remaining / 30), 1)

    # Kalan hedef tutarı
    remaining_amount = float(goal.target_amount) - float(goal.current_savings)
    monthly_needed = remaining_amount / months_remaining if months_remaining > 0 else remaining_amount

    # Ulaşılabilir mi?
    is_achievable = current_monthly_savings >= monthly_needed
    shortfall = max(monthly_needed - current_monthly_savings, 0)

    # Tahmini tamamlanma tarihi (mevcut tasarruf oranıyla)
    if current_monthly_savings > 0:
        months_to_complete = remaining_amount / current_monthly_savings
        estimated_completion = today + timedelta(days=int(months_to_complete * 30))
    else:
        estimated_completion = goal.target_date + timedelta(days=365)

    # Kategori bazında tasarruf fırsatları
    category_totals: dict[str, float] = defaultdict(float)
    for t in transactions:
        if float(t.amount) < 0 and t.category:
            category_totals[t.category] += abs(float(t.amount)) / months_of_data

    # Kısılabilir harcamalar (yemek, alışveriş, eğlence öncelikli)
    reducible_categories = ["yemek", "alisveris", "abonelik", "diger"]
    opportunities = []
    for cat in reducible_categories:
        if cat in category_totals and category_totals[cat] > 0:
            monthly_spend = category_totals[cat]
            saving_10 = monthly_spend * 0.10
            saving_20 = monthly_spend * 0.20
            days_saved = int((saving_20 * months_remaining) / (monthly_needed if monthly_needed > 0 else 1) * 30)
            opportunities.append({
                "category": cat,
                "monthly_spend": round(monthly_spend, 2),
                "saving_10_percent": round(saving_10, 2),
                "saving_20_percent": round(saving_20, 2),
                "days_earlier": days_saved,
            })

    # AI önerisi metni
    recommendation = _generate_recommendation(
        goal_name=goal.name,
        is_achievable=is_achievable,
        monthly_needed=monthly_needed,
        current_savings=current_monthly_savings,
        shortfall=shortfall,
        months_remaining=months_remaining,
        opportunities=opportunities,
    )

    return GoalAnalysis(
        goal=_to_response(goal),
        months_remaining=months_remaining,
        monthly_savings_needed=Decimal(str(round(monthly_needed, 2))),
        current_monthly_savings=Decimal(str(round(current_monthly_savings, 2))),
        is_achievable=is_achievable,
        estimated_completion_date=estimated_completion,
        shortfall_per_month=Decimal(str(round(shortfall, 2))),
        top_saving_opportunities=opportunities[:3],
        ai_recommendation=recommendation,
    )


def _generate_recommendation(
    goal_name: str,
    is_achievable: bool,
    monthly_needed: float,
    current_savings: float,
    shortfall: float,
    months_remaining: int,
    opportunities: list[dict],
) -> str:
    if is_achievable:
        return (
            f"'{goal_name}' hedefine ulaşmak için aylık "
            f"{monthly_needed:.0f} TL tasarruf etmeniz yeterli. "
            f"Mevcut tasarruf oranınız ({current_savings:.0f} TL/ay) "
            f"bu hedefe {months_remaining} ay içinde ulaşmanızı sağlıyor. "
            f"Harika gidiyorsunuz, bu tempoyu koruyun!"
        )
    else:
        tip = ""
        if opportunities:
            best = opportunities[0]
            tip = (
                f" '{best['category']}' harcamalarınızı %20 azaltırsanız "
                f"aylık {best['saving_20_percent']:.0f} TL ekstra tasarruf edersiniz."
            )
        return (
            f"'{goal_name}' hedefine mevcut tasarruf oranınızla "
            f"ulaşmak zor görünüyor. Aylık {monthly_needed:.0f} TL "
            f"biriktirmeniz gerekirken şu an {current_savings:.0f} TL "
            f"biriktiriyorsunuz ({shortfall:.0f} TL açık var).{tip}"
        )


def _to_response(goal: FinancialGoal) -> GoalResponse:
    return GoalResponse(
        id=str(goal.id),
        account_id=str(goal.account_id),
        name=goal.name,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        priority=goal.priority,
        current_savings=goal.current_savings,
        notes=goal.notes,
        status=goal.status,
    )
