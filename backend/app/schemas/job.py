from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.filtration.pipeline import FilterToggles


class UploadResponse(BaseModel):
    job_id: int
    file_name: str
    headers: list[str]
    detected_email_columns: list[str]
    detected_roles: dict[str, list[str]]
    row_count_estimate: int | None = None
    sheet_names: list[str] | None = None


class StartJobRequest(BaseModel):
    email_column: str
    title_column: Optional[str] = None
    industry_column: Optional[str] = None
    name_column: Optional[str] = None
    company_column: Optional[str] = None
    country_column: Optional[str] = None
    linkedin_column: Optional[str] = None
    toggles: FilterToggles = FilterToggles()
    merge_to_master: bool = True


class JobOut(BaseModel):
    JobID: int
    JobType: str
    FileName: str | None
    Status: str
    TotalRows: int
    ProcessedRows: int
    KeptRows: int
    OtherTLDRows: int
    RejectedRows: int
    ProgressPercent: float
    CurrentStep: str | None
    ErrorMessage: str | None
    StartTime: datetime | None
    EndTime: datetime | None
    CreatedAt: datetime

    model_config = {"from_attributes": True}


class JobResultOut(BaseModel):
    ReasonCode: str
    DisplayName: str
    RowCount: int
    OutputFilePath: str | None

    model_config = {"from_attributes": True}


class JobSummaryOut(BaseModel):
    job: JobOut
    results: list[JobResultOut]
