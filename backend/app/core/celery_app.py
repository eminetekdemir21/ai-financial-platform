from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_financial_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    # Bir worker aynı anda kaç task alabilir — ML inference CPU-yoğun
    # olduğu için düşük tutuyoruz, aksi halde worker'lar birbirini bloklar.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Faz 2'den itibaren her domain kendi task modülünü buraya register edecek:
# celery_app.autodiscover_tasks([
#     "app.domains.transactions",
#     "app.domains.categorization",
#     "app.domains.fraud_detection",
#     "app.domains.forecasting",
# ])
