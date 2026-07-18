from decimal import Decimal
from pydantic import BaseModel


class Opportunity(BaseModel):
    """Tek bir tasarruf fırsatı."""
    type: str           # "abonelik", "yuksek_harcama", "tekrar_eden", "fraud_risk"
    title: str
    description: str
    monthly_saving: Decimal
    annual_saving: Decimal
    priority: str       # "yuksek", "orta", "dusuk"
    category: str
    action: str         # Kullanıcının yapması gereken somut adım


class OpportunityReport(BaseModel):
    """AI Opportunity Engine raporu."""
    opportunity_score: int          # 0-100 (ne kadar çok fırsat var)
    total_monthly_saving: Decimal
    total_annual_saving: Decimal
    opportunities: list[Opportunity]
    summary: str
    subscriptions_total: Decimal    # Toplam abonelik harcaması
    top_merchant_waste: list[dict]  # En çok para harcanan ama azaltılabilir yerler
