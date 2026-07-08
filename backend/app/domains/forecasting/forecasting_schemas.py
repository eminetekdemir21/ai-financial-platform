from pydantic import BaseModel


class ForecastResult(BaseModel):
    method: str
    confidence: str
    predicted_next_month_net: float
    current_balance_estimate: float
    projected_balance: float
    monthly_history: dict[str, float]
    message: str
