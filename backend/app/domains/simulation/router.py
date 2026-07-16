import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.simulation import service
from app.domains.simulation.schemas import (
    SaveScenarioRequest,
    SavedScenarioDetail,
    SavedScenarioSummary,
    SimulationRequest,
    SimulationResult,
)
from app.domains.transactions.service import verify_account_ownership

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/{account_id}", response_model=SimulationResult)
def run_simulation(
    account_id: uuid.UUID,
    request: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    What-If senaryosu calistirir.

    Ornek senaryolar:
    - Maas artisi: {"income_change": 5000}
    - Restoran azaltma: {"category_changes": {"yemek": -0.30}}
    - Telefon alimi: {"one_time_expense": 15000}
    - Kombine: {"income_change": 3000, "category_changes": {"alisveris": -0.20}}
    - Farkli sure: {"income_change": 5000, "horizon_months": 60}
    """
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.run_simulation(db=db, account_id=account_id, request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/scenarios", response_model=SavedScenarioDetail)
def save_scenario(
    account_id: uuid.UUID,
    body: SaveScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bir senaryoyu calistirir ve sonucuyla birlikte kaydeder."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    try:
        return service.save_scenario(
            db=db, account_id=account_id, name=body.name, request=body.request
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/scenarios", response_model=list[SavedScenarioSummary])
def list_scenarios(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hesaba ait kaydedilmis senaryolarin gecmisini listeler."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    return service.list_scenarios(db=db, account_id=account_id)


@router.get("/{account_id}/scenarios/{scenario_id}", response_model=SavedScenarioDetail)
def get_scenario(
    account_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tek bir kayitli senaryonun tam detayini getirir."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    result = service.get_scenario(db=db, account_id=account_id, scenario_id=scenario_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Senaryo bulunamadi.")
    return result


@router.delete("/{account_id}/scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    account_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kayitli senaryoyu siler."""
    verify_account_ownership(db=db, account_id=account_id, user_id=current_user.id)
    deleted = service.delete_scenario(db=db, account_id=account_id, scenario_id=scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Senaryo bulunamadi.")
