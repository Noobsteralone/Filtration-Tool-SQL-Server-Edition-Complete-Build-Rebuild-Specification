"""Activity / audit logging (section 45)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.user import User


def log_activity(
    db: Session,
    action: str,
    user: User | None = None,
    job_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    status: str = "SUCCESS",
    message: str | None = None,
) -> None:
    entry = ActivityLog(
        UserID=user.UserID if user else None,
        Username=user.Username if user else None,
        Action=action,
        JobID=job_id,
        EntityType=entity_type,
        EntityId=str(entity_id) if entity_id is not None else None,
        Status=status,
        Message=message,
        CreatedAt=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
