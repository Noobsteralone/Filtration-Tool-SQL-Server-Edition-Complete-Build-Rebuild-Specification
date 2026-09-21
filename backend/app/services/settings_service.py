from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settings import Setting


def get_all(db: Session) -> list[Setting]:
    return list(db.execute(select(Setting)).scalars().all())


def get(db: Session, key: str) -> str | None:
    setting = db.get(Setting, key)
    return setting.SettingValue if setting else None


def set_value(db: Session, key: str, value: str, updated_by: str | None = None) -> Setting:
    setting = db.get(Setting, key)
    if setting:
        setting.SettingValue = value
        setting.UpdatedAt = datetime.now(timezone.utc)
        setting.UpdatedBy = updated_by
    else:
        setting = Setting(SettingKey=key, SettingValue=value, UpdatedAt=datetime.now(timezone.utc), UpdatedBy=updated_by)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting
