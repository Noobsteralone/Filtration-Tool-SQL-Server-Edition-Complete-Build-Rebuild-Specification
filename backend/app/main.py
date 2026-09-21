"""
FT - Filtration Tool: FastAPI application entrypoint.

Run with:  uvicorn app.main:app --host 0.0.0.0 --port 8000
(see backend/README section of the project README for full instructions).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

from app.config import get_settings
from app.database import DatabaseConnectionError, init_db
from app.routers import activity_logs, auth, jobs, master, reference, settings, users

_FRIENDLY_DB_ERROR = (
    "SQL Server connection failed. Please verify SQL Server is running, the server "
    "name and database are correct, and the ODBC driver is installed, then try again."
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ft.main")

app_state: dict[str, object] = {"db_ready": False, "db_error": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        app_state["db_ready"] = True
        app_state["db_error"] = None
        logger.info("Startup: database initialization succeeded.")
    except DatabaseConnectionError as exc:
        # Section 61: human-readable error, full detail only in the log file.
        app_state["db_ready"] = False
        app_state["db_error"] = str(exc)
        logger.error("Startup: database initialization failed:\n%s", exc)
        logger.warning(
            "The API will still start so /api/health can report this problem, "
            "but every data endpoint will fail until SQL Server is reachable."
        )
    yield


def create_app() -> FastAPI:
    settings_obj = get_settings()
    application = FastAPI(title=settings_obj.APP_NAME, version="1.0.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings_obj.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(jobs.router)
    application.include_router(master.router)
    application.include_router(master.other_tld_router)
    application.include_router(reference.router)
    application.include_router(settings.router)
    application.include_router(activity_logs.router)

    @application.get("/api/health")
    def health():
        return {
            "app": settings_obj.APP_NAME,
            "database_ready": app_state["db_ready"],
            "database_error": app_state["db_error"],
        }

    # Section 61: any request that fails because SQL Server itself is
    # unreachable (whether through the SQLAlchemy `get_db()` dependency or
    # a raw pyodbc call) must return a clean, human-readable error to the
    # client -- never a raw stack trace. Full detail always still goes to
    # the log.
    @application.exception_handler(DBAPIError)
    @application.exception_handler(DatabaseConnectionError)
    async def handle_database_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Database error while handling %s %s", request.method, request.url.path)
        return JSONResponse(status_code=503, content={"detail": _FRIENDLY_DB_ERROR})

    return application


app = create_app()
