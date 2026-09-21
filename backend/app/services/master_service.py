"""
Master dataset + Other-TLD Master management (sections 25-27, 41, 43).
Search always happens in SQL Server (never loads the whole table into the
browser / Python process) via LIMIT/OFFSET pagination.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pyodbc
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.job import Job, JobColumn
from app.models.master import MasterEmail, MasterFile, OtherTLDMaster
from app.utils.identifiers import quote_alias, quote_ident

ROLE_TO_MERGE_PARAM = {
    "NAME": "NameColumn",
    "TITLE": "TitleColumn",
    "COMPANY": "CompanyColumn",
    "INDUSTRY": "IndustryColumn",
    "COUNTRY": "CountryColumn",
    "LINKEDIN": "LinkedInColumn",
}


def search_master(db: Session, search: str | None, page: int = 1, page_size: int = 50) -> tuple[list[MasterEmail], int]:
    stmt = select(MasterEmail)
    count_stmt = select(func.count()).select_from(MasterEmail)
    if search:
        like = f"%{search}%"
        cond = or_(
            MasterEmail.Email.ilike(like),
            MasterEmail.Company.ilike(like),
            MasterEmail.Name.ilike(like),
            MasterEmail.Title.ilike(like),
            MasterEmail.Industry.ilike(like),
            MasterEmail.SourceFile.ilike(like),
        )
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(MasterEmail.MasterID.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.execute(stmt).scalars().all())
    return rows, total


def search_other_tld_master(db: Session, search: str | None, page: int = 1, page_size: int = 50):
    stmt = select(OtherTLDMaster)
    count_stmt = select(func.count()).select_from(OtherTLDMaster)
    if search:
        like = f"%{search}%"
        cond = or_(OtherTLDMaster.Email.ilike(like), OtherTLDMaster.Company.ilike(like), OtherTLDMaster.Name.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    total = db.execute(count_stmt).scalar_one()
    stmt = stmt.order_by(OtherTLDMaster.OtherTLDID.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.execute(stmt).scalars().all())
    return rows, total


def list_master_files(db: Session) -> list[MasterFile]:
    stmt = select(MasterFile).where(MasterFile.IsDeleted == False).order_by(MasterFile.CreatedAt.desc())  # noqa: E712
    return list(db.execute(stmt).scalars().all())


def soft_delete_master_file(db: Session, master_file_id: int) -> bool:
    mf = db.get(MasterFile, master_file_id)
    if not mf:
        return False
    mf.IsDeleted = True
    db.commit()
    return True


def merge_job_into_master(
    conn: pyodbc.Connection,
    db: Session,
    job: Job,
    staging_table: str,
    job_columns: list[JobColumn],
    uploaded_by_user_id: int | None,
) -> dict:
    """
    Calls sp_FT_MergeToMaster and sp_FT_MergeToOtherTLDMaster, then records
    a FT_MasterFiles entry so the Master Files screen can show/search/
    delete/export by contributing source file (section 41).
    """
    role_columns: dict[str, str] = {}
    other_columns: list[JobColumn] = []
    for jc in job_columns:
        if jc.DetectedRole in ROLE_TO_MERGE_PARAM and jc.DetectedRole not in role_columns:
            role_columns[jc.DetectedRole] = jc.SqlColumnName
        elif jc.DetectedRole in (None, "OTHER"):
            other_columns.append(jc)

    additional_sql = None
    if other_columns:
        additional_sql = ", ".join(
            f"s.{quote_ident(jc.SqlColumnName)} AS {quote_alias(jc.OriginalName)}" for jc in other_columns
        )

    params = {
        "StagingTable": staging_table,
        "JobID": job.JobID,
        "FileName": job.FileName,
    }
    for role, param_name in ROLE_TO_MERGE_PARAM.items():
        params[param_name] = role_columns.get(role)
    params["AdditionalDataSql"] = additional_sql

    cursor = conn.cursor()

    cursor.execute(
        """
        DECLARE @ins INT, @dup INT;
        EXEC dbo.sp_FT_MergeToMaster
            @StagingTable=?, @JobID=?, @FileName=?,
            @NameColumn=?, @TitleColumn=?, @CompanyColumn=?, @IndustryColumn=?,
            @CountryColumn=?, @LinkedInColumn=?, @AdditionalDataSql=?,
            @RowsInserted=@ins OUTPUT, @RowsDuplicate=@dup OUTPUT;
        SELECT @ins AS RowsInserted, @dup AS RowsDuplicate;
        """,
        [
            params["StagingTable"], params["JobID"], params["FileName"],
            params["NameColumn"], params["TitleColumn"], params["CompanyColumn"], params["IndustryColumn"],
            params["CountryColumn"], params["LinkedInColumn"], params["AdditionalDataSql"],
        ],
    )
    row = cursor.fetchone()
    rows_inserted, rows_duplicate = (row.RowsInserted, row.RowsDuplicate) if row else (0, 0)
    conn.commit()

    cursor.execute(
        """
        DECLARE @ins2 INT;
        EXEC dbo.sp_FT_MergeToOtherTLDMaster
            @StagingTable=?, @JobID=?, @FileName=?,
            @NameColumn=?, @TitleColumn=?, @CompanyColumn=?, @IndustryColumn=?,
            @CountryColumn=?, @LinkedInColumn=?, @AdditionalDataSql=?,
            @RowsInserted=@ins2 OUTPUT;
        SELECT @ins2 AS RowsInserted;
        """,
        [
            params["StagingTable"], params["JobID"], params["FileName"],
            params["NameColumn"], params["TitleColumn"], params["CompanyColumn"], params["IndustryColumn"],
            params["CountryColumn"], params["LinkedInColumn"], params["AdditionalDataSql"],
        ],
    )
    row2 = cursor.fetchone()
    other_tld_inserted = row2.RowsInserted if row2 else 0
    conn.commit()

    db.add(
        MasterFile(
            FileName=job.FileName or f"job-{job.JobID}",
            SourceJobID=job.JobID,
            TargetTable="FT_MasterEmails",
            RowsAdded=rows_inserted,
            RowsDuplicate=rows_duplicate,
            UploadedBy=uploaded_by_user_id,
            CreatedAt=datetime.now(timezone.utc),
        )
    )
    db.commit()

    return {
        "master_rows_inserted": rows_inserted,
        "master_rows_duplicate": rows_duplicate,
        "other_tld_rows_inserted": other_tld_inserted,
    }
