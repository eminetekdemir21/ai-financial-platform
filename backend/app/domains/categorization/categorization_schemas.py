from pydantic import BaseModel


class CategorizationPreviewRequest(BaseModel):
    description: str
    merchant: str | None = None


class CategorizationPreviewResponse(BaseModel):
    category: str
    method: str
    confidence: float


class CategorizationRunResult(BaseModel):
    total_categorized: int
    by_method: dict[str, int]
