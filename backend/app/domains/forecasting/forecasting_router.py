import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.forecasting import forecasting_schemas as schemas
from app.domains.forecasting import forecasting_service as service
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/forecast", tags=["forecasting"])


@router.get("/{account_id}", response_model=schemas.ForecastResult)
def get_forecast(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Hesabin gecmis islem verisine dayanarak gelecek ayin net nakit
    akisini ve projekte edilen bakiyesini tahmin eder.
    """
    account = verify_account_ownership(
        db=db, account_id=account_id, user_id=current_user.id
    )
    return service.forecast_next_month(db=db, account=account)
