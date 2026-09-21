from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Setting(Base):
    __tablename__ = "FT_Settings"

    SettingKey: Mapped[str] = mapped_column(String(100), primary_key=True)
    SettingValue: Mapped[str | None] = mapped_column(Text, nullable=True)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    UpdatedBy: Mapped[str | None] = mapped_column(String(100), nullable=True)
