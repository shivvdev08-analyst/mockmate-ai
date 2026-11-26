from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, onboarding, providers

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Alembic is the migration path; create_all keeps first-run local dev
    # working before any migration has been applied.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MockMate AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(providers.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"ok": True, "service": "mockmate-ai", "version": "0.1.0"}


@app.get("/api/v1/health")
def health_v1():
    return {"ok": True, "service": "mockmate-ai", "version": "0.1.0"}
