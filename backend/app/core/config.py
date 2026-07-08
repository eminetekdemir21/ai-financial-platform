from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Uygulama genelindeki tüm ortam değişkenlerini tek bir yerden,
    tip kontrolü yaparak okur. .env dosyasındaki bir değişken eksikse
    veya yanlış tipte ise uygulama başlamadan hata verir — production'da
    "çalışıyor ama yanlış config ile çalışıyor" senaryosunu engeller.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Veritabanı ---
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432

    # --- Redis / Celery ---
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # --- Güvenlik ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Uygulama ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Financial Intelligence Platform"

    # --- LLM ---
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-6"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Settings nesnesini her import'ta yeniden okumak yerine cache'ler.
    FastAPI'nin dependency injection sisteminde Depends(get_settings)
    olarak kullanılır.
    """
    return Settings()


settings = get_settings()
