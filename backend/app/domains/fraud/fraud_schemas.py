from pydantic import BaseModel


class FraudRunResult(BaseModel):
    total_analyzed: int
    flagged_count: int
