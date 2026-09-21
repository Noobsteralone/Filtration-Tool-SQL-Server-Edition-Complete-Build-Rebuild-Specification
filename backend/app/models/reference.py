"""
One ORM class per reference table, but all sharing the same shape --
mirrors the shared-shape design in sql/schema/010_reference_tables.sql so
that app/services/reference_service.py can manage every list through one
generic service class.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class _ReferenceMixin:
    ID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Value: Mapped[str] = mapped_column(String(255), nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    UpdatedAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    CreatedBy: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AllowedTLD(_ReferenceMixin, Base):
    __tablename__ = "FT_AllowedTLDs"


class PersonalEmailDomain(_ReferenceMixin, Base):
    __tablename__ = "FT_PersonalEmailDomains"


class RestrictedDomain(_ReferenceMixin, Base):
    __tablename__ = "FT_RestrictedDomains"


class SpamDomain(_ReferenceMixin, Base):
    __tablename__ = "FT_SpamDomains"


class RestrictedKeyword(_ReferenceMixin, Base):
    __tablename__ = "FT_RestrictedKeywords"

    Category: Mapped[str] = mapped_column(String(50), default="EMAIL_USERNAME")


class RestrictedTitle(_ReferenceMixin, Base):
    __tablename__ = "FT_RestrictedTitles"


class RestrictedIndustry(_ReferenceMixin, Base):
    __tablename__ = "FT_RestrictedIndustries"
