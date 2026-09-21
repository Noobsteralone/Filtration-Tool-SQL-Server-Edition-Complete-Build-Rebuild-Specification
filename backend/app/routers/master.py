from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, raw_connection
from app.schemas.master import MasterEmailOut, MasterFileOut, MasterMergeRequest, OtherTLDMasterOut
from app.services import job_service, master_service
from app.services.activity_log_service import log_activity
from app.services.auth_service import require_admin, require_user

router = APIRouter(prefix="/api/master", tags=["master"])
other_tld_router = APIRouter(prefix="/api/other-tld-master", tags=["other-tld-master"])


@router.get("", response_model=list[MasterEmailOut])
def search_master(search: str | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), _=Depends(require_user)):
    rows, _total = master_service.search_master(db, search, page, page_size)
    return rows


@router.get("/files", response_model=list[MasterFileOut])
def list_master_files(db: Session = Depends(get_db), _=Depends(require_user)):
    return master_service.list_master_files(db)


@router.delete("/files/{master_file_id}")
def delete_master_file(master_file_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    ok = master_service.soft_delete_master_file(db, master_file_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Master file entry not found")
    log_activity(db, "MASTER_MERGE", user=user, entity_type="MasterFile", entity_id=master_file_id, message="Removed from Master listing")
    return {"deleted": True}


@router.post("/merge")
def merge_job_to_master(payload: MasterMergeRequest, db: Session = Depends(get_db), user=Depends(require_admin)):
    job = job_service.get_job(db, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.Status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job must be COMPLETED before it can be merged into Master")

    job_columns = job_service.get_job_columns(db, job.JobID)
    with raw_connection() as conn:
        stats = master_service.merge_job_into_master(conn, db, job, job.StagingTableName, job_columns, job.UploadedBy)
    log_activity(db, "MASTER_MERGE", user=user, job_id=job.JobID, message=str(stats))
    return stats


@other_tld_router.get("", response_model=list[OtherTLDMasterOut])
def search_other_tld(search: str | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), _=Depends(require_user)):
    rows, _total = master_service.search_other_tld_master(db, search, page, page_size)
    return rows
