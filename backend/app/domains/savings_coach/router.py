import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.savings_coach.schemas import SavingsCoachReport
from app.domains.savings_coach import service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/savings-coach", tags=["savings-coach"])


@router.get("/{account_id}", response_model=SavingsCoachReport)
def get_savings_report(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabın harcama geçmişini analiz edip kişiselleştirilmiş
    tasarruf önerileri ve trend analizi döndürür.
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.analyze(db=db, account_id=account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
