from fastapi import APIRouter

from app.domains.auth.router import router as auth_router
from app.domains.transactions.router import router as transactions_router
from app.domains.financial_health.router import router as health_router
from app.domains.goal_planner.router import router as goals_router
from app.domains.simulation.router import router as simulation_router
from app.domains.savings_coach.router import router as savings_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(transactions_router)
api_router.include_router(health_router)
api_router.include_router(goals_router)
api_router.include_router(simulation_router)
api_router.include_router(savings_router)

try:
    from app.domains.categorization.categorization_router import router as cat_router
    api_router.include_router(cat_router)
except ImportError:
    pass

try:
    from app.domains.fraud.fraud_router import router as fraud_router
    api_router.include_router(fraud_router)
except ImportError:
    pass

try:
    from app.domains.forecasting.forecasting_router import router as forecast_router
    api_router.include_router(forecast_router)
except ImportError:
    pass

try:
    from app.domains.assistant.assistant_router import router as assistant_router
    api_router.include_router(assistant_router)
except ImportError:
    pass
