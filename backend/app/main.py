from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    import app.domains.auth.models
    import app.domains.transactions.models
    import app.domains.goal_planner.models
    import app.domains.simulation.models
    with engine.begin() as conn:
        Base.metadata.create_all(bind=engine)
    print(f"[startup] {settings.PROJECT_NAME} ortam: {settings.ENVIRONMENT}")
    yield
    print("[shutdown] Uygulama kapatiliyor")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
