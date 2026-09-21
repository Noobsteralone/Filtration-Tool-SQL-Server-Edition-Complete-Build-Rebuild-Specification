import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Job(Base):
    __tablename__ = "FT_Jobs"

    JobID: Mapped[int] = mapped_column(Integer, primary_key=True)
    JobGuid: Mapped[uuid.UUID] = mapped_column(nullable=False)
    JobType: Mapped[str] = mapped_column(String(50), nullable=False)
    FileName: Mapped[str | None] = mapped_column(String(500), nullable=True)
    OriginalFilePath: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    StagingTableName: Mapped[str | None] = mapped_column(String(128), nullable=True)
    EmailColumn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    TitleColumn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    IndustryColumn: Mapped[str | None] = mapped_column(String(255), nullable=True)
    OptionsJson: Mapped[str | None] = mapped_column(Text, nullable=True)
    UploadedBy: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Users.UserID"), nullable=True)
    StartTime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    EndTime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    Status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    TotalRows: Mapped[int] = mapped_column(Integer, default=0)
    ProcessedRows: Mapped[int] = mapped_column(Integer, default=0)
    KeptRows: Mapped[int] = mapped_column(Integer, default=0)
    OtherTLDRows: Mapped[int] = mapped_column(Integer, default=0)
    RejectedRows: Mapped[int] = mapped_column(Integer, default=0)
    ProgressPercent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    CurrentStep: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ErrorMessage: Mapped[str | None] = mapped_column(Text, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class JobColumn(Base):
    __tablename__ = "FT_JobColumns"

    JobColumnID: Mapped[int] = mapped_column(Integer, primary_key=True)
    JobID: Mapped[int] = mapped_column(Integer, ForeignKey("FT_Jobs.JobID"), nullable=False)
    OriginalName: Mapped[str] = mapped_column(String(255), nullable=False)
    SqlColumnName: Mapped[str] = mapped_column(String(128), nullable=False)
    OrdinalPosition: Mapped[int] = mapped_column(Integer, nullable=False)
    DetectedRole: Mapped[str | None] = mapped_column(String(50), nullable=True)


class JobResult(Base):
    __tablename__ = "FT_JobResults"

    JobResultID: Mapped[int] = mapped_column(Integer, primary_key=True)
    JobID: Mapped[int] = mapped_column(Integer, ForeignKey("FT_Jobs.JobID"), nullable=False)
    ReasonCode: Mapped[str] = mapped_column(String(50), nullable=False)
    DisplayName: Mapped[str] = mapped_column(String(100), nullable=False)
    RowCount: Mapped[int] = mapped_column(Integer, default=0)
    OutputFilePath: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
