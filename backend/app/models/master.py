from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MasterEmail(Base):
    __tablename__ = "FT_MasterEmails"

    MasterID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Email: Mapped[str] = mapped_column(String(320), nullable=False)
    Name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    LinkedIn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    SourceFile: Mapped[str | None] = mapped_column(String(500), nullable=True)
    SourceJobID: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Jobs.JobID"), nullable=True)
    AdditionalData: Mapped[str | None] = mapped_column(Text, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class OtherTLDMaster(Base):
    __tablename__ = "FT_OtherTLDMaster"

    OtherTLDID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Email: Mapped[str] = mapped_column(String(320), nullable=False)
    TLD: Mapped[str | None] = mapped_column(String(50), nullable=True)
    Name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    Country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    LinkedIn: Mapped[str | None] = mapped_column(String(500), nullable=True)
    SourceFile: Mapped[str | None] = mapped_column(String(500), nullable=True)
    SourceJobID: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Jobs.JobID"), nullable=True)
    AdditionalData: Mapped[str | None] = mapped_column(Text, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MasterFile(Base):
    __tablename__ = "FT_MasterFiles"

    MasterFileID: Mapped[int] = mapped_column(Integer, primary_key=True)
    FileName: Mapped[str] = mapped_column(String(500), nullable=False)
    SourceJobID: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Jobs.JobID"), nullable=True)
    TargetTable: Mapped[str] = mapped_column(String(50), default="FT_MasterEmails")
    RowsAdded: Mapped[int] = mapped_column(Integer, default=0)
    RowsDuplicate: Mapped[int] = mapped_column(Integer, default=0)
    UploadedBy: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Users.UserID"), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    IsDeleted: Mapped[bool] = mapped_column(Boolean, default=False)
