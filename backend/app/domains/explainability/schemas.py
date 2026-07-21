from pydantic import BaseModel
from decimal import Decimal


class FraudExplanation(BaseModel):
    transaction_id: str
    description: str
    amount: str
    is_flagged: bool
    fraud_score: float
    reasons: list[str]
    risk_level: str  # "dusuk", "orta", "yuksek", "kritik"
    recommendation: str


class CategoryExplanation(BaseModel):
    transaction_id: str
    description: str
    category: str
    method: str  # "kural", "embedding", "fallback"
    matched_keyword: str | None
    confidence: float
    alternative_categories: list[str]
    explanation: str


class HealthScoreExplanation(BaseModel):
    score: int
    grade: str
    factors: list[dict]
    improvement_tips: list[str]
    explanation: str


class RecommendationExplanation(BaseModel):
    recommendation_type: str
    title: str
    reasoning: list[str]
    data_points: list[dict]
    confidence: str
    explanation: str
