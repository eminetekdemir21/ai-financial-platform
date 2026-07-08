from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.models import User
from app.domains.auth.schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from app.domains.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Yeni kullanici kaydi."""
    try:
        return AuthService(db).register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Kullanici girisi, JWT token doner."""
    try:
        return AuthService(db).login(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Giris yapmis kullanicinin kendi bilgilerini doner.

    GUVENLIK DUZELTMESI: Token artik query parametresi olarak elle
    yazilmiyor - Authorization: Bearer <token> header'i uzerinden
    otomatik okunuyor. Bu sayede Swagger'daki "Authorize" butonu
    calisir ve token URL'de acikca gorunmez.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )
