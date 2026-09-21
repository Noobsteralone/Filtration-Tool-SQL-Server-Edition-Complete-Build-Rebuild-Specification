"""
Centralized application configuration, read from environment variables /
`.env`. Nothing in this module hard-codes business rules or credentials --
see sections 4, 51 and 66 of the specification.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- App -----------------------------------------------------------
    APP_NAME: str = "FT Filtration Tool"
    APP_ENV: str = "production"
    APP_SECRET_KEY: str = "change-this-to-a-long-random-string"

    # -- SQL Server ------------------------------------------------------
    SQL_SERVER: str = "LAP-S2M059"
    SQL_DATABASE: str = "FT_Filtration"
    SQL_DRIVER: str = "ODBC Driver 17 for SQL Server"
    SQL_TRUSTED_CONNECTION: bool = True
    SQL_USERNAME: str = ""
    SQL_PASSWORD: str = ""
    SQL_EXTRA_ODBC_PARAMS: str = ""

    # -- Local storage -----------------------------------------------------
    DATA_ROOT: str = "./data"
    MAX_FILE_SIZE_GB: int = 20
    CSV_CHUNK_SIZE: int = 100_000
    EXCEL_CHUNK_SIZE: int = 50_000

    # -- Jobs / concurrency --------------------------------------------------
    MAX_CONCURRENT_JOBS: int = 1
    PROGRESS_UPDATE_EVERY_ROWS: int = 25_000
    PROGRESS_UPDATE_EVERY_SECONDS: int = 3

    # -- Retention -------------------------------------------------------
    UPLOAD_RETENTION_DAYS: int = 1
    REPORT_RETENTION_DAYS: int = 30
    TEMP_RETENTION_HOURS: int = 24
    BACKUP_RETENTION_DAYS: int = 7
    BACKUP_DIRECTORY: str = "./data/backups"

    # -- Default seed values ------------------------------------------------
    DEFAULT_ALLOWED_TLDS: str = ".com,.org,.edu,.us"

    # -- Auth -------------------------------------------------------------
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DEFAULT_SUPERADMIN_USERNAME: str = "admin"
    DEFAULT_SUPERADMIN_PASSWORD: str = "ChangeMe!123"
    DEFAULT_SUPERADMIN_EMAIL: str = "admin@example.com"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def default_allowed_tlds_list(self) -> List[str]:
        return [t.strip() for t in self.DEFAULT_ALLOWED_TLDS.split(",") if t.strip()]

    @property
    def data_root_path(self) -> Path:
        p = Path(self.DATA_ROOT)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def uploads_dir(self) -> Path:
        p = self.data_root_path / "uploads"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def jobs_dir(self) -> Path:
        p = self.data_root_path / "jobs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def reports_dir(self) -> Path:
        p = self.data_root_path / "reports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def backups_dir(self) -> Path:
        p = Path(self.BACKUP_DIRECTORY)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_dir(self) -> Path:
        p = self.data_root_path / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_dir(self, job_id: int) -> Path:
        p = self.jobs_dir / str(job_id)
        (p / "input").mkdir(parents=True, exist_ok=True)
        (p / "output").mkdir(parents=True, exist_ok=True)
        (p / "temp").mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
