from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ActivityLog(Base):
    __tablename__ = "FT_ActivityLogs"

    LogID: Mapped[int] = mapped_column(Integer, primary_key=True)
    UserID: Mapped[int | None] = mapped_column(Integer, ForeignKey("FT_Users.UserID"), nullable=True)
    Username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    Action: Mapped[str] = mapped_column(String(100), nullable=False)
    JobID: Mapped[int | None] = mapped_column(Integer, nullable=True)
    EntityType: Mapped[str | None] = mapped_column(String(100), nullable=True)
    EntityId: Mapped[str | None] = mapped_column(String(100), nullable=True)
    Status: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    Message: Mapped[str | None] = mapped_column(Text, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
