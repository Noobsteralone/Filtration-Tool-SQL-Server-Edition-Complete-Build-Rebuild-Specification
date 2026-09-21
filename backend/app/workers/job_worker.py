"""
Background job execution (sections 58-60).

DESIGN DECISION (documented per section 74): the heavy, CPU-intensive work
of this application is pushed down into SQL Server set-based operations
(stored procedures) -- the Python side is I/O-bound orchestration (file
streaming, waiting on the database). A `ThreadPoolExecutor` sized to
`MAX_CONCURRENT_JOBS` is therefore used instead of
`multiprocessing.get_context("spawn")`: it avoids the complexity and
Windows-specific pitfalls of process-based workers (the spec explicitly
warns against `fork`, which is moot here since no `multiprocessing` is
used) while still keeping the HTTP request path non-blocking and
respecting the configured concurrency limit. Each job releases the GIL
almost immediately (waiting on network I/O to SQL Server or disk I/O),
so a thread pool provides real concurrency for this workload.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import get_settings
from app.database import get_session_factory, raw_connection
from app.filtration.csv_importer import (
    add_pipeline_columns,
    build_column_mappings,
    create_staging_table,
    insert_rows_chunked,
    iter_csv_rows,
    read_csv_header,
    try_native_bulk_insert,
)
from app.filtration.excel_reader import iter_all_sheet_rows, unified_headers
from app.filtration.pipeline import FilterToggles, FiltrationPipeline
from app.filtration.reason_codes import KEPT_CODE, NON_REJECTION_CODES
from app.models.job import Job
from app.services import job_service, master_service, report_service
from app.services.activity_log_service import log_activity
from app.utils.identifiers import staging_table_name

logger = logging.getLogger("ft.job_worker")

ROLE_FROM_REQUEST_FIELD = {
    "email_column": "EMAIL",
    "title_column": "TITLE",
    "industry_column": "INDUSTRY",
    "name_column": "NAME",
    "company_column": "COMPANY",
    "country_column": "COUNTRY",
    "linkedin_column": "LINKEDIN",
}

class JobCancelledException(Exception):
    """Raised internally to unwind a job's processing once a user has
    requested cancellation (section 30/59: cooperative cancel, checked
    between pipeline steps rather than killing the thread)."""


_executor: Optional[ThreadPoolExecutor] = None


def get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        settings = get_settings()
        _executor = ThreadPoolExecutor(max_workers=max(1, settings.MAX_CONCURRENT_JOBS), thread_name_prefix="ft-job")
    return _executor


def submit_job(job_id: int, start_request: dict, merge_to_master: bool) -> None:
    get_executor().submit(_run_job_safe, job_id, start_request, merge_to_master)


def _run_job_safe(job_id: int, start_request: dict, merge_to_master: bool) -> None:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        _run_job(db, job_id, start_request, merge_to_master)
    except JobCancelledException:
        logger.info("Job %s cancelled by user request", job_id)
        try:
            job_service.update_job(db, job_id, Status="CANCELLED", EndTime=datetime.now(timezone.utc))
            log_activity(db, "FILTRATION_CANCELLED", job_id=job_id, status="SUCCESS")
        except Exception:
            logger.exception("Failed to persist CANCELLED status for job %s", job_id)
    except Exception as exc:  # noqa: BLE001 - job-level catch-all, logged with full trace
        logger.exception("Job %s failed", job_id)
        try:
            job_service.update_job(
                db, job_id, Status="FAILED", ErrorMessage=str(exc), EndTime=datetime.now(timezone.utc)
            )
            log_activity(db, "FILTRATION_FAILED", job_id=job_id, status="FAILED", message=str(exc))
        except Exception:
            logger.exception("Failed to persist FAILED status for job %s", job_id)
    finally:
        db.close()


def _raise_if_cancelled(db, job_id: int) -> None:
    from sqlalchemy import select

    status_value = db.execute(select(Job.Status).where(Job.JobID == job_id)).scalar_one_or_none()
    if status_value == "CANCELLING":
        raise JobCancelledException()


def _run_job(db, job_id: int, start_request: dict, merge_to_master: bool) -> None:
    settings = get_settings()
    job: Job | None = job_service.get_job(db, job_id)
    if job is None:
        raise RuntimeError(f"Job {job_id} not found")

    staging_table = job.StagingTableName or staging_table_name(job_id)
    file_path = Path(job.OriginalFilePath)
    suffix = file_path.suffix.lower()

    job_service.update_job(
        db, job_id, Status="IMPORTING", CurrentStep="Reading source file", StartTime=datetime.now(timezone.utc)
    )

    if suffix == ".csv":
        headers = read_csv_header(file_path)
    else:
        headers = unified_headers(file_path)

    mappings = build_column_mappings(headers)
    original_to_sql = {m.original_name: m.sql_column_name for m in mappings}

    role_by_original: dict[str, str] = {}
    for field_name, role in ROLE_FROM_REQUEST_FIELD.items():
        original_name = start_request.get(field_name)
        if original_name:
            role_by_original[original_name] = role

    job_columns_payload = [
        {
            "original_name": m.original_name,
            "sql_column_name": m.sql_column_name,
            "ordinal": m.ordinal,
            "detected_role": role_by_original.get(m.original_name, "OTHER"),
        }
        for m in mappings
    ]
    job_service.set_job_columns(db, job_id, job_columns_payload)

    email_sql_column = original_to_sql[start_request["email_column"]]
    title_sql_column = original_to_sql.get(start_request.get("title_column") or "")
    industry_sql_column = original_to_sql.get(start_request.get("industry_column") or "")

    with raw_connection(autocommit=False) as conn:
        cursor = conn.cursor()
        create_staging_table(cursor, staging_table, mappings)

        if suffix == ".csv":
            bulk_ok = try_native_bulk_insert(cursor, staging_table, str(file_path), mappings)
            if not bulk_ok:
                _stream_import(
                    cursor, staging_table, mappings, iter_csv_rows(file_path), settings.CSV_CHUNK_SIZE,
                    db, job_id,
                )
        else:
            rows = (values for _, _, values in iter_all_sheet_rows(file_path, headers))
            _stream_import(cursor, staging_table, mappings, rows, settings.EXCEL_CHUNK_SIZE, db, job_id)

        add_pipeline_columns(cursor, staging_table)
        cursor.execute("EXEC dbo.sp_FT_IndexStagingTable @StagingTable=?", [staging_table])
        conn.commit()

        _raise_if_cancelled(db, job_id)

        cursor.execute(f"SELECT COUNT(*) FROM [{staging_table}]")
        (total_rows,) = cursor.fetchone()
        job_service.update_job(db, job_id, TotalRows=total_rows, Status="PROCESSING")

        toggles = FilterToggles.from_dict(start_request.get("toggles") or {})

        last_update = time.monotonic()

        def on_step(step_name: str, rows_affected: int) -> None:
            nonlocal last_update
            now = time.monotonic()
            if now - last_update >= settings.PROGRESS_UPDATE_EVERY_SECONDS:
                job_service.update_job(db, job_id, CurrentStep=step_name)
                last_update = now
            _raise_if_cancelled(db, job_id)

        pipeline = FiltrationPipeline(
            conn=conn,
            staging_table=staging_table,
            email_column=email_sql_column,
            title_column=title_sql_column,
            industry_column=industry_sql_column,
            on_step=on_step,
        )
        pipeline.run_full_pipeline(toggles)

        summary = pipeline.job_summary()
        job_service.save_job_results(db, job_id, summary)

        kept = summary.get(KEPT_CODE, 0)
        other_tld = summary.get("OTHER_TLD", 0)
        rejected = sum(v for k, v in summary.items() if k not in NON_REJECTION_CODES)

        job_service.update_job(
            db, job_id,
            ProcessedRows=total_rows,
            KeptRows=kept,
            OtherTLDRows=other_tld,
            RejectedRows=rejected,
            ProgressPercent=100.0,
            CurrentStep="Generating reports",
        )

        job_columns = job_service.get_job_columns(db, job_id)

        merge_stats = {}
        if merge_to_master and job.JobType == "FILTRATION":
            merge_stats = master_service.merge_job_into_master(
                conn, db, job, staging_table, job_columns, job.UploadedBy
            )

        output_dir = settings.job_dir(job_id) / "output"
        category_files = report_service.generate_all_category_csvs(conn, staging_table, job_columns, summary, output_dir)
        report_service.generate_consolidated_excel(
            conn, staging_table, job_columns, summary, output_dir,
            job_meta={
                "job_id": job_id,
                "file_name": job.FileName,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "total_rows": total_rows,
            },
        )

        for reason_code, path in category_files.items():
            _record_output_path(db, job_id, reason_code, str(path))

    job_service.update_job(
        db, job_id, Status="COMPLETED", EndTime=datetime.now(timezone.utc), CurrentStep=None
    )
    log_activity(
        db, "FILTRATION_COMPLETED", job_id=job_id, status="SUCCESS",
        message=f"Kept={kept} OtherTLD={other_tld} Rejected={rejected} Merge={merge_stats}",
    )


def _stream_import(cursor, staging_table, mappings, row_iterator, chunk_size, db, job_id) -> None:
    def progress(n: int) -> None:
        job_service.update_job(db, job_id, ProcessedRows=n, CurrentStep="Importing rows")

    insert_rows_chunked(cursor, staging_table, mappings, row_iterator, chunk_size, on_progress=progress)


def _record_output_path(db, job_id: int, reason_code: str, path: str) -> None:
    from sqlalchemy import select

    from app.models.job import JobResult

    result = db.execute(
        select(JobResult).where(JobResult.JobID == job_id, JobResult.ReasonCode == reason_code)
    ).scalar_one_or_none()
    if result:
        result.OutputFilePath = path
        db.commit()
