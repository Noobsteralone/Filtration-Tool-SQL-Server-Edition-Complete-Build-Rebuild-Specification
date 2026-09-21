from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "FT_Roles"

    RoleID: Mapped[int] = mapped_column(Integer, primary_key=True)
    RoleName: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    Description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class User(Base):
    __tablename__ = "FT_Users"

    UserID: Mapped[int] = mapped_column(Integer, primary_key=True)
    Username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    Email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    RoleID: Mapped[int] = mapped_column(Integer, ForeignKey("FT_Roles.RoleID"), nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    UpdatedAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    LastLoginAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    role: Mapped["Role"] = relationship("Role")
