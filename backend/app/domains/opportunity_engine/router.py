import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.opportunity_engine.schemas import OpportunityReport
from app.domains.opportunity_engine import service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/opportunities", tags=["opportunity-engine"])


@router.get("/{account_id}", response_model=OpportunityReport)
def get_opportunities(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabın işlem verilerini analiz ederek:
    - Çakışan abonelikleri tespit eder
    - Yüksek harcamalı kategorileri bulur
    - Somut tasarruf önerileri üretir
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.analyze(db=db, account_id=account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
