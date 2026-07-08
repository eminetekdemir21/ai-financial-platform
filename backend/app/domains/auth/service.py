from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.domains.auth.models import User
from app.domains.auth.schemas import TokenResponse, UserLogin, UserRegister, UserResponse


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def register(self, data: UserRegister) -> UserResponse:
        """
        Yeni kullanıcı kaydı. Email daha önce alınmışsa hata fırlatır.
        Şifre hashlenerek kaydedilir, düz metin asla tutulmaz.
        """
        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ValueError("Bu email adresi zaten kayıtlı.")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        )

    def login(self, data: UserLogin) -> TokenResponse:
        """
        Email ve şifre doğrulama. Başarılıysa JWT token döner.
        Hata mesajı kasıtlı olarak belirsiz tutulur (güvenlik gereği):
        'email yanlış' veya 'şifre yanlış' yerine tek mesaj kullanılır.
        """
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.password_hash):
            raise ValueError("Email veya şifre hatalı.")

        if not user.is_active:
            raise ValueError("Hesap aktif değil.")

        token = create_access_token({"sub": str(user.id), "email": user.email})
        user_response = UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        return TokenResponse(access_token=token, user=user_response)

    def get_user_by_id(self, user_id: str) -> User | None:
        """Korumalı endpoint'lerin kullanıcı doğrulaması için."""
        return self.db.query(User).filter(User.id == user_id).first()
