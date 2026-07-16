from pydantic import BaseModel
from decimal import Decimal


class SavingTip(BaseModel):
    """Tek bir tasarruf önerisi."""
    category: str
    title: str
    description: str
    monthly_saving_potential: Decimal
    annual_saving_potential: Decimal
    difficulty: str  # "kolay", "orta", "zor"
    priority: str    # "yuksek", "orta", "dusuk"


class SpendingTrend(BaseModel):
    """Bir kategorinin harcama trendi."""
    category: str
    current_monthly: Decimal
    previous_monthly: Decimal
    change_pct: float
    trend: str  # "artiyor", "azaliyor", "stabil"


class SavingsCoachReport(BaseModel):
    """AI Savings Coach'un ürettiği tam rapor."""
    total_monthly_income: Decimal
    total_monthly_expense: Decimal
    current_savings_rate: float  # yüzde olarak
    target_savings_rate: float   # hedef yüzde
    monthly_savings_gap: Decimal # hedefe ulaşmak için gereken ekstra tasarruf

    spending_trends: list[SpendingTrend]
    tips: list[SavingTip]

    coach_message: str  # Kişisel mesaj
    potential_annual_savings: Decimal  # Tüm önerileri uygularsa
