import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.explainability import service
from app.domains.explainability.schemas import (
    FraudExplanation, CategoryExplanation,
    HealthScoreExplanation, RecommendationExplanation,
)
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/explain", tags=["explainability"])


@router.get("/fraud/{account_id}/{transaction_id}", response_model=FraudExplanation)
def explain_fraud(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bir islemin neden supheli isaretledigini aciklar."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.explain_fraud(db=db, transaction_id=transaction_id, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/category/{account_id}/{transaction_id}", response_model=CategoryExplanation)
def explain_category(
    account_id: uuid.UUID,
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bir islemin neden bu kategoriye atandigini aciklar."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.explain_category(db=db, transaction_id=transaction_id, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health-score/{account_id}", response_model=HealthScoreExplanation)
def explain_health_score(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Finansal saglik skorunun neden bu degerde oldugunu aciklar."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.explain_health_score(db=db, account_id=account_id)


@router.get("/recommendation/{account_id}/{recommendation_type}", response_model=RecommendationExplanation)
def explain_recommendation(
    account_id: uuid.UUID,
    recommendation_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bir tavsiyenin neden yapildigini aciklar."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.explain_recommendation(
        db=db, account_id=account_id, recommendation_type=recommendation_type
    )
