import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.financial_health.schemas import HealthScoreResponse
from app.domains.financial_health.scoring import calculate_health_score
from app.domains.transactions.models import Transaction
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/health-score", tags=["financial-health"])


@router.get("/{account_id}", response_model=HealthScoreResponse)
def get_health_score(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabın tüm işlemlerini analiz edip 0-100 arası finansal sağlık
    skoru hesaplar. 5 faktör: tasarruf oranı, gider çeşitliliği,
    fraud riski, gelir istikrarı, harcama trendi.
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="Bu hesapta henüz işlem yok. Skor hesaplamak için işlem yükleyin.",
        )

    result = calculate_health_score(transactions)
    return HealthScoreResponse(**result)
