"""
Centralized SQL Server connection module.

Builds the ODBC / SQLAlchemy connection string from `.env` settings,
supports both Windows Authentication (Trusted_Connection) and SQL Server
Authentication, and exposes:

  - `engine` / `SessionLocal` / `get_db()` for normal SQLAlchemy ORM use.
  - `raw_connection()` for bulk operations and stored-procedure calls that
    need OUTPUT parameters or fast `executemany` (pyodbc directly, since
    SQLAlchemy's Core/ORM layers add overhead that matters at
    multi-million-row scale -- section 3/34).
  - `init_db()` which creates the database schema / procedures / seed data
    on startup, idempotently, without ever destroying existing data
    (sections 64, 63).

Never hard-codes credentials (section 4).
"""
from __future__ import annotations

import contextlib
import logging
import re
from pathlib import Path
from typing import Generator, Iterator

import pyodbc
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger("ft.database")

_SQL_ROOT = Path(__file__).resolve().parent.parent.parent / "sql"

_GO_SPLIT_RE = re.compile(r"^\s*GO\s*(?:--.*)?$", re.IGNORECASE | re.MULTILINE)


class DatabaseConnectionError(RuntimeError):
    """Raised with a human-readable message; the real stack trace is logged,
    never shown to the end user (section 61)."""


def build_odbc_connection_string() -> str:
    settings = get_settings()
    parts = [
        f"DRIVER={{{settings.SQL_DRIVER}}}",
        f"SERVER={settings.SQL_SERVER}",
        f"DATABASE={settings.SQL_DATABASE}",
    ]
    if settings.SQL_TRUSTED_CONNECTION:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={settings.SQL_USERNAME}")
        parts.append(f"PWD={settings.SQL_PASSWORD}")
    if settings.SQL_EXTRA_ODBC_PARAMS:
        parts.append(settings.SQL_EXTRA_ODBC_PARAMS)
    return ";".join(parts) + ";"


def build_master_odbc_connection_string() -> str:
    """Connection string targeting `master`, used only for CREATE DATABASE."""
    settings = get_settings()
    parts = [
        f"DRIVER={{{settings.SQL_DRIVER}}}",
        f"SERVER={settings.SQL_SERVER}",
        "DATABASE=master",
    ]
    if settings.SQL_TRUSTED_CONNECTION:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={settings.SQL_USERNAME}")
        parts.append(f"PWD={settings.SQL_PASSWORD}")
    if settings.SQL_EXTRA_ODBC_PARAMS:
        parts.append(settings.SQL_EXTRA_ODBC_PARAMS)
    return ";".join(parts) + ";"


def _sqlalchemy_url(odbc_connect: str) -> URL:
    return URL.create("mssql+pyodbc", query={"odbc_connect": odbc_connect})


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            _sqlalchemy_url(build_odbc_connection_string()),
            fast_executemany=True,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped SQLAlchemy session."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def _friendly_connection_error(exc: Exception) -> DatabaseConnectionError:
    settings = get_settings()
    logger.exception("SQL Server connection failed")
    message = (
        "SQL Server connection failed.\n\n"
        "Please verify:\n"
        f"1. SQL Server is running.\n"
        f"2. Server name is {settings.SQL_SERVER}.\n"
        f"3. {settings.SQL_DATABASE} database exists.\n"
        "4. Windows Authentication is available (or SQL_USERNAME/SQL_PASSWORD are set).\n"
        f"5. {settings.SQL_DRIVER} is installed.\n"
    )
    return DatabaseConnectionError(message)


@contextlib.contextmanager
def raw_connection(database: str | None = None, autocommit: bool = False) -> Iterator[pyodbc.Connection]:
    """
    Direct pyodbc connection for bulk loads and stored-procedure calls that
    need OUTPUT parameters. `database=None` uses the configured
    FT_Filtration database; pass "master" for CREATE DATABASE.
    """
    settings = get_settings()
    conn_str = build_master_odbc_connection_string() if database == "master" else build_odbc_connection_string()
    try:
        conn = pyodbc.connect(conn_str, autocommit=autocommit, timeout=30)
    except pyodbc.Error as exc:
        raise _friendly_connection_error(exc) from exc
    try:
        yield conn
    finally:
        conn.close()


def check_connection() -> None:
    """Raises DatabaseConnectionError with a friendly message on failure."""
    with raw_connection() as conn:
        conn.cursor().execute("SELECT 1").fetchone()


def _split_batches(sql_text: str) -> list[str]:
    batches = [b.strip() for b in _GO_SPLIT_RE.split(sql_text)]
    return [b for b in batches if b]


def _run_script_file(cursor: pyodbc.Cursor, path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8-sig")
    for batch in _split_batches(sql_text):
        try:
            cursor.execute(batch)
            while cursor.nextset():
                pass
        except pyodbc.Error as exc:
            raise DatabaseConnectionError(
                f"Failed executing migration script {path.name}: {exc}"
            ) from exc


def init_db() -> None:
    """
    Startup initialization (section 64):
      1. Ensure the FT_Filtration database exists (master connection).
      2. Create missing tables / indexes (idempotent scripts).
      3. Create stored procedures (CREATE OR ALTER -- always safe to rerun).
      4. Seed default reference data / settings (idempotent MERGE).
    Never drops or truncates existing data.
    """
    settings = get_settings()

    # Step 1: create database if missing (needs a `master` connection).
    try:
        with raw_connection(database="master", autocommit=True) as conn:
            cursor = conn.cursor()
            _run_script_file(cursor, _SQL_ROOT / "schema" / "000_create_database.sql")
    except pyodbc.Error as exc:
        raise _friendly_connection_error(exc) from exc

    # Steps 2-4: run against the FT_Filtration database itself.
    schema_files = sorted((_SQL_ROOT / "schema").glob("*.sql"))
    schema_files = [f for f in schema_files if f.name != "000_create_database.sql"]
    procedure_files = sorted((_SQL_ROOT / "procedures").glob("*.sql"))
    seed_files = sorted((_SQL_ROOT / "seed").glob("*.sql"))

    with raw_connection(autocommit=True) as conn:
        cursor = conn.cursor()
        for f in schema_files:
            logger.info("Running schema script: %s", f.name)
            _run_script_file(cursor, f)
        for f in procedure_files:
            logger.info("Creating/updating stored procedure: %s", f.name)
            _run_script_file(cursor, f)
        for f in seed_files:
            logger.info("Seeding reference data: %s", f.name)
            _run_script_file(cursor, f)

    _ensure_default_superadmin()
    logger.info("Database initialization complete.")


def _ensure_default_superadmin() -> None:
    """Creates the default SUPER_ADMIN user only if no users exist yet."""
    from app.utils.security import hash_password

    settings = get_settings()
    with raw_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dbo.FT_Users")
        (count,) = cursor.fetchone()
        if count and count > 0:
            return
        cursor.execute("SELECT RoleID FROM dbo.FT_Roles WHERE RoleName = 'SUPER_ADMIN'")
        row = cursor.fetchone()
        if not row:
            logger.warning("SUPER_ADMIN role not found; skipping default admin creation.")
            return
        role_id = row[0]
        cursor.execute(
            "INSERT INTO dbo.FT_Users (Username, Email, PasswordHash, RoleID, IsActive) "
            "VALUES (?, ?, ?, ?, 1)",
            settings.DEFAULT_SUPERADMIN_USERNAME,
            settings.DEFAULT_SUPERADMIN_EMAIL,
            hash_password(settings.DEFAULT_SUPERADMIN_PASSWORD),
            role_id,
        )
        conn.commit()
        logger.info(
            "Created default SUPER_ADMIN user '%s'. Change this password immediately.",
            settings.DEFAULT_SUPERADMIN_USERNAME,
        )
