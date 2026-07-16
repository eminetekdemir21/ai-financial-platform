import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """
    Kullanicinin simule etmek istedigi senaryo.
    Birden fazla degisiklik ayni anda simule edilebilir.
    """

    # Gelir degisikligi
    income_change: Decimal = Decimal("0")  # +5000 = maas artisi, -2000 = gelir azalmasi
    # Kategori bazli harcama degisikligi
    category_changes: dict[str, Decimal] = {}  # {"yemek": -0.30} = %30 azaltma, {"alisveris": 500} = 500 TL azaltma
    # Tek seferlik harcama
    one_time_expense: Decimal = Decimal("0")  # 15000 = telefon alimi
    # Aciklama (opsiyonel)
    description: str = ""
    # Projeksiyon suresi (ay) - varsayilan 12 ay, 1-60 ay arasi
    horizon_months: int = Field(default=12, ge=1, le=60)


class MonthlyProjection(BaseModel):
    month: int
    income: Decimal
    expense: Decimal
    net_savings: Decimal
    cumulative_savings: Decimal


class SimulationResult(BaseModel):
    """Simulasyon sonucu."""

    description: str
    # Mevcut durum
    current_monthly_income: Decimal
    current_monthly_expense: Decimal
    current_monthly_savings: Decimal
    # Simule edilmis durum
    simulated_monthly_income: Decimal
    simulated_monthly_expense: Decimal
    simulated_monthly_savings: Decimal
    # Fark
    savings_difference: Decimal
    annual_savings_difference: Decimal
    # Projeksiyon suresi ve aylik projeksiyon
    horizon_months: int
    monthly_projections: list[MonthlyProjection]
    # AI yorumu
    ai_summary: str
    impact_level: str  # "positive", "negative", "neutral"


class SaveScenarioRequest(BaseModel):
    """Bir senaryoyu kaydetmek icin gonderilen istek."""

    name: str = ""
    request: SimulationRequest


class SavedScenarioSummary(BaseModel):
    """Gecmis listesinde gosterilen ozet kayit."""

    id: uuid.UUID
    name: str
    impact_level: str
    savings_difference: Decimal
    annual_savings_difference: Decimal
    horizon_months: int
    created_at: datetime


class SavedScenarioDetail(BaseModel):
    """Tek bir kayitli senaryonun tam detayi (yeniden calistirmaya da yeterli)."""

    id: uuid.UUID
    name: str
    created_at: datetime
    request: SimulationRequest
    result: SimulationResult
