import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.db.base import engine
from app.modules.ads.router import router as ads_router
from app.modules.audit.recorder import is_auditable, record_audit
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.clients.router import router as clients_router
from app.modules.reports.router import router as reports_router
from app.modules.settings.router import router as settings_router
from app.modules.users.router import router as users_router
from app.startup import startup_setup
from app.workers.scheduler import start_scheduler, stop_scheduler

settings = get_settings()
setup_logging()

if settings.environment != "local" and settings.sentry_url:
    import sentry_sdk

    sentry_sdk.init(dsn=settings.sentry_url, traces_sample_rate=1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_setup()
    run_scheduler = settings.scheduler_enabled and settings.environment != "test"
    if run_scheduler:
        start_scheduler()
    yield
    if run_scheduler:
        stop_scheduler()


app = FastAPI(
    title="Externam Hub API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "prod" else "/docs",
    redoc_url=None if settings.environment == "prod" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.front_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response


@app.middleware("http")
async def audit_requests(request: Request, call_next):
    """Journalise automatiquement chaque action mutante (best-effort, désactivé en test)."""
    response = await call_next(request)
    if settings.environment != "test" and is_auditable(request.method, request.url.path):
        await run_in_threadpool(
            record_audit,
            request.method,
            request.url.path,
            response.status_code,
            response.headers.get("x-request-id"),
            request.headers.get("authorization"),
        )
    return response


@app.get("/health", tags=["Health"])
def health() -> dict:
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "down",
        "environment": settings.environment,
    }


# --- Routers (un include par module) ---
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(ads_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
