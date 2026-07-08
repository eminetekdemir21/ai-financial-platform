import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.fraud import fraud_schemas as schemas
from app.domains.fraud import fraud_service as service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/run", response_model=schemas.FraudRunResult)
def run_fraud_detection(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Belirtilen hesabin tum islemlerini yeniden analiz eder, fraud_score
    ve is_flagged alanlarini gunceller. Hesabin gercekten bu kullaniciya
    ait oldugu dogrulanir (guvenlik).
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.run_fraud_detection(db=db, account_id=account_id)
