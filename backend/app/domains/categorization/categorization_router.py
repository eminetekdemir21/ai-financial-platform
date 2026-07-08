import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.categorization import categorization_schemas as schemas
from app.domains.categorization import categorization_service as service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/categorization", tags=["categorization"])


@router.post("/run", response_model=schemas.CategorizationRunResult)
def run_categorization(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirtilen hesabin henuz kategorisi olmayan tum islemlerini
    kategorilendirir. Hesabin gercekten bu kullaniciya ait oldugu
    dogrulanir (guvenlik).
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.categorize_account_transactions(db=db, account_id=account_id)


@router.post("/preview", response_model=schemas.CategorizationPreviewResponse)
def preview_categorization(
    payload: schemas.CategorizationPreviewRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Veritabanina yazmadan, tek bir metin/satici adi icin hangi
    kategorinin secilecegini gosterir. Kural setini test etmek
    icin kullanislidir (orn. "Migros Market" -> market, rule).
    """
    category, method, confidence = service.categorize_transaction(
        payload.description, payload.merchant
    )
    return schemas.CategorizationPreviewResponse(
        category=category, method=method, confidence=confidence
    )
