from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db import database
from app.routers import accounts, dashboard, fx, health, preferences, sync, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        await database.connect(settings)
        app.state.database_startup_error = None
    except Exception as exc:
        if settings.app_env != "development":
            raise
        app.state.database_startup_error = str(exc)
    yield
    await database.disconnect()


app = FastAPI(
    title="PocketPal / Personal Finance HQ",
    description="Offline-first personal finance ledger and automation API.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


app.include_router(health.router)
app.include_router(preferences.router)
app.include_router(accounts.router)
app.include_router(sync.router)
app.include_router(dashboard.router)
app.include_router(fx.router)
app.include_router(webhooks.router)
