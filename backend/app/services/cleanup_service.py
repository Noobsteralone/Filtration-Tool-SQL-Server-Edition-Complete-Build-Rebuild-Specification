"""
Retention / cleanup (section 48). Only ever touches temporary uploads,
job workspaces, and generated reports for terminal (COMPLETED/FAILED/
CANCELLED) jobs older than the configured retention window. NEVER deletes
dbo.FT_MasterEmails or dbo.FT_OtherTLDMaster data, and never drops a
staging table for a job that is still QUEUED/IMPORTING/PROCESSING.
"""
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database import raw_connection
from app.models.job import Job
from app.utils.identifiers import assert_safe_identifier, quote_ident

logger = logging.getLogger("ft.cleanup")

TERMINAL_STATUSES = ("COMPLETED", "FAILED", "CANCELLED")


def cleanup_old_job_workspaces(db) -> int:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.UPLOAD_RETENTION_DAYS)
    stmt = select(Job).where(Job.Status.in_(TERMINAL_STATUSES), Job.CreatedAt < cutoff)
    jobs = db.execute(stmt).scalars().all()

    removed = 0
    for job in jobs:
        job_dir = settings.jobs_dir / str(job.JobID) / "input"
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1
    logger.info("Cleanup: removed input files for %s job(s) older than %s day(s).", removed, settings.UPLOAD_RETENTION_DAYS)
    return removed


def cleanup_old_reports(db) -> int:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.REPORT_RETENTION_DAYS)
    stmt = select(Job).where(Job.Status.in_(TERMINAL_STATUSES), Job.CreatedAt < cutoff)
    jobs = db.execute(stmt).scalars().all()

    removed = 0
    for job in jobs:
        output_dir = settings.jobs_dir / str(job.JobID) / "output"
        if output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
            removed += 1
    logger.info("Cleanup: removed report output for %s job(s) older than %s day(s).", removed, settings.REPORT_RETENTION_DAYS)
    return removed


def cleanup_temp_files() -> int:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.TEMP_RETENTION_HOURS)
    removed = 0
    for job_dir in settings.jobs_dir.glob("*/temp"):
        try:
            mtime = datetime.fromtimestamp(job_dir.stat().st_mtime, tz=timezone.utc)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            shutil.rmtree(job_dir, ignore_errors=True)
            removed += 1
    logger.info("Cleanup: removed %s stale temp folder(s).", removed)
    return removed


def drop_staging_tables_for_terminal_jobs(db) -> int:
    """Drops FT_Staging_<id> tables for jobs that finished more than
    REPORT_RETENTION_DAYS ago -- their output files and (if merged) Master
    rows already preserved everything of lasting value."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.REPORT_RETENTION_DAYS)
    stmt = select(Job).where(Job.Status.in_(TERMINAL_STATUSES), Job.CreatedAt < cutoff, Job.StagingTableName.is_not(None))
    jobs = db.execute(stmt).scalars().all()

    dropped = 0
    with raw_connection(autocommit=True) as conn:
        cursor = conn.cursor()
        for job in jobs:
            table_name = job.StagingTableName
            assert_safe_identifier(table_name)
            cursor.execute(f"IF OBJECT_ID('{table_name}', 'U') IS NOT NULL DROP TABLE {quote_ident(table_name)};")
            dropped += 1
    logger.info("Cleanup: dropped %s staging table(s) for old terminal jobs.", dropped)
    return dropped
