import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    bank_name: str
    account_number_masked: str
    currency: str = "TRY"


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bank_name: str
    account_number_masked: str
    currency: str
    current_balance: Decimal


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    description: Optional[str] = None
    merchant: Optional[str] = None
    transaction_date: datetime
    category: Optional[str] = None
    fraud_score: Optional[float] = None
    is_flagged: bool = False
    source: str


class UploadResult(BaseModel):
    imported_count: int
    source: str
    categorized_count: int = 0
    # Ayni hesapta, ayni tutar+aciklama+tarih ile zaten var olan satirlar
    # tekrar eklenmez - bunlarin sayisi burada raporlanir. Kullanici ayni
    # dosyayi yanlislikla iki kez yuklerse, ikinci yuklemede bu sayi
    # yukledigi satir sayisina esit, imported_count ise 0 olur.
    skipped_duplicates: int = 0
