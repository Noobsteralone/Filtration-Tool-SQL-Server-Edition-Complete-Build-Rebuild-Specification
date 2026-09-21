"""
Job metadata CRUD (section 29). The staging table itself (the actual
million-row dataset) is never touched through the ORM -- only small
per-job bookkeeping rows live here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job, JobColumn, JobResult
from app.models.user import User
from app.utils.identifiers import staging_table_name


def create_job(
    db: Session,
    job_type: str,
    file_name: str,
    original_file_path: str,
    uploaded_by: User | None,
) -> Job:
    job = Job(
        JobGuid=uuid.uuid4(),
        JobType=job_type,
        FileName=file_name,
        OriginalFilePath=original_file_path,
        UploadedBy=uploaded_by.UserID if uploaded_by else None,
        Status="QUEUED",
        CreatedAt=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job.StagingTableName = staging_table_name(job.JobID)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)


def list_jobs(db: Session, user: User) -> list[Job]:
    role_name = user.role.RoleName if user.role else "USER"
    stmt = select(Job).order_by(Job.CreatedAt.desc())
    if role_name == "USER":
        stmt = stmt.where(Job.UploadedBy == user.UserID)
    return list(db.execute(stmt).scalars().all())


def set_job_columns(db: Session, job_id: int, mappings: list[dict]) -> None:
    for m in mappings:
        db.add(
            JobColumn(
                JobID=job_id,
                OriginalName=m["original_name"],
                SqlColumnName=m["sql_column_name"],
                OrdinalPosition=m["ordinal"],
                DetectedRole=m.get("detected_role"),
            )
        )
    db.commit()


def get_job_columns(db: Session, job_id: int) -> list[JobColumn]:
    stmt = select(JobColumn).where(JobColumn.JobID == job_id).order_by(JobColumn.OrdinalPosition)
    return list(db.execute(stmt).scalars().all())


def update_job(db: Session, job_id: int, **fields) -> Job | None:
    job = db.get(Job, job_id)
    if not job:
        return None
    for key, value in fields.items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


def save_job_results(db: Session, job_id: int, summary: dict[str, int]) -> None:
    from app.filtration.reason_codes import display_name

    # Clear any previous results (retry case) then insert fresh, accurate counts.
    existing = db.execute(select(JobResult).where(JobResult.JobID == job_id)).scalars().all()
    for row in existing:
        db.delete(row)
    db.commit()

    now = datetime.now(timezone.utc)
    for reason_code, row_count in summary.items():
        db.add(
            JobResult(
                JobID=job_id,
                ReasonCode=reason_code,
                DisplayName=display_name(reason_code),
                RowCount=row_count,
                CreatedAt=now,
            )
        )
    db.commit()


def get_job_results(db: Session, job_id: int) -> list[JobResult]:
    stmt = select(JobResult).where(JobResult.JobID == job_id)
    return list(db.execute(stmt).scalars().all())
