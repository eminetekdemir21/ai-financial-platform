from pydantic import BaseModel, EmailStr, field_validator


class UserRegister(BaseModel):
    """Kayıt endpoint'inin beklediği veri."""
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır.")
        return v


class UserLogin(BaseModel):
    """Giriş endpoint'inin beklediği veri."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """API'nin kullanıcı verisi dönerken kullandığı şema.
    password_hash asla dışarı verilmez."""
    id: str
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Başarılı girişte dönen token verisi."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
