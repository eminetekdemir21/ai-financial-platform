from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator


class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    target_date: date
    priority: str = "medium"
    current_savings: Decimal = Decimal("0")
    notes: str | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v not in ("low", "medium", "high"):
            raise ValueError("Öncelik 'low', 'medium' veya 'high' olmalıdır.")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Hedef tutar 0'dan büyük olmalıdır.")
        return v


class GoalResponse(BaseModel):
    id: str
    account_id: str
    name: str
    target_amount: Decimal
    target_date: date
    priority: str
    current_savings: Decimal
    notes: str | None
    status: str

    model_config = {"from_attributes": True}


class GoalAnalysis(BaseModel):
    """AI'ın hedefe ulaşmak için ürettiği analiz."""
    goal: GoalResponse
    months_remaining: int
    monthly_savings_needed: Decimal
    current_monthly_savings: Decimal
    is_achievable: bool
    estimated_completion_date: date
    shortfall_per_month: Decimal
    top_saving_opportunities: list[dict]
    ai_recommendation: str
