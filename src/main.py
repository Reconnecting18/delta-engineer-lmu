from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.health import router as health_router
from src.api.laps import router as laps_router
from src.api.sessions import router as sessions_router
from src.api.setups import router as setups_router
from src.api.telemetry import router as telemetry_router
from src.config import get_settings
from src.db.init_db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Local API only (no auth): allow Electron renderer (Vite dev, file://, or custom protocol).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(laps_router)
app.include_router(sessions_router)
app.include_router(setups_router)
app.include_router(telemetry_router)
