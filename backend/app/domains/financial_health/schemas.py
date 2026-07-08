from pydantic import BaseModel


class FactorDetail(BaseModel):
    score: float
    weight: float
    comment: str
    label: str


class HealthScoreResponse(BaseModel):
    score: float
    grade: str
    breakdown: dict[str, FactorDetail]
    summary: str
