import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.goal_planner.schemas import GoalAnalysis, GoalCreate, GoalResponse
from app.domains.goal_planner import service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/goals", tags=["goal-planner"])


@router.post("/{account_id}", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    account_id: uuid.UUID,
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Yeni finansal hedef oluşturur."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.create_goal(db=db, account_id=account_id, data=data)


@router.get("/{account_id}", response_model=list[GoalResponse])
def list_goals(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hesabın aktif hedeflerini listeler."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.list_goals(db=db, account_id=account_id)


@router.get("/analyze/{goal_id}", response_model=GoalAnalysis)
def analyze_goal(
    goal_id: uuid.UUID,
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hedefe ulaşmak için gereken aylık tasarruf, tahmini tarih
    ve tasarruf fırsatlarını analiz eder.
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.analyze_goal(db=db, goal_id=goal_id, account_id=account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hedefi iptal eder (siler değil, status=cancelled yapar)."""
    service.delete_goal(db=db, goal_id=goal_id)
