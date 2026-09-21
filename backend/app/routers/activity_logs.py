from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogOut
from app.services.auth_service import require_admin

router = APIRouter(prefix="/api/activity-logs", tags=["activity-logs"])


@router.get("", response_model=list[ActivityLogOut])
def list_activity_logs(
    limit: int = 200,
    job_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    stmt = select(ActivityLog).order_by(ActivityLog.CreatedAt.desc()).limit(min(limit, 1000))
    if job_id is not None:
        stmt = stmt.where(ActivityLog.JobID == job_id)
    return list(db.execute(stmt).scalars().all())
