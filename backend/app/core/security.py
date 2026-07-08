import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Swagger'daki "Authorize" butonunu bu tanimliyor. HTTPBearer, tek bir
# metin kutusuna direkt token yapistirmani saglar (Bearer on-eki otomatik
# eklenir) - OAuth2PasswordBearer'in aksine ayri bir login formu istemez.
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Kullanicinin sifresini bcrypt ile hashler.
    Duz metin sifre asla veritabanina yazilmaz.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanicinin girdigi sifreyi veritabanindaki hash ile karsilastirir."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Kullanici bilgilerini iceren JWT access token uretir.
    Token suresi .env dosyasindaki ACCESS_TOKEN_EXPIRE_MINUTES ile belirlenir.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """JWT token'i cozumler. Gecersiz veya suresi dolmussa None doner."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    GUVENLIK: Tum korumali endpoint'lerin kullanacagi tek, merkezi
    kimlik dogrulama bagimligi (dependency).

    Onceki versiyonda token bir query parametresi olarak elle
    yaziliyordu - bu hem yanlis kullanima acikti hem de Swagger'in
    "Authorize" butonunu tanimasini engelliyordu.

    Simdi: Swagger'da "Authorize" butonuna tikladiginda tek bir kutuya
    ham token'i yapistiriyorsun (Bearer on-eki otomatik eklenir).
    Token dogrulanir, veritabanindan gercek User kaydi getirilir ve
    dondurulur. Herhangi bir endpoint bu kullanici disinda birinin
    verisine erisemez - cunku user_id artik hep buradan gelir,
    disaridan (URL/body) verilemez.
    """
    from app.domains.auth.models import User  # circular import'u onlemek icin burada

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Gecersiz veya suresi dolmus token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_raw = payload.get("sub")
    try:
        user_uuid = uuid.UUID(str(user_id_raw))
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise credentials_exception

    return user
