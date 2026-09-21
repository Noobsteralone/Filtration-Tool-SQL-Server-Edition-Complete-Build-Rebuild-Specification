import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.job import JobOut, JobResultOut, StartJobRequest, UploadResponse
from app.services import job_service, upload_service
from app.services.activity_log_service import log_activity
from app.services.auth_service import require_admin, require_user
from app.workers import job_worker

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/upload", response_model=UploadResponse)
def upload_file(
    job_type: str = "FILTRATION",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    try:
        suffix = upload_service.validate_upload(file)
    except upload_service.UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job = job_service.create_job(db, job_type=job_type, file_name=file.filename, original_file_path="", uploaded_by=user)

    try:
        dest = upload_service.save_uploaded_file(job.JobID, file, suffix)
    except upload_service.FileTooLargeError as exc:
        job_service.update_job(db, job.JobID, Status="FAILED", ErrorMessage=str(exc))
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    job_service.update_job(db, job.JobID, OriginalFilePath=str(dest))
    inspection = upload_service.inspect_file(dest, suffix)

    log_activity(db, "UPLOAD", user=user, job_id=job.JobID, entity_type="Job", message=file.filename)

    return UploadResponse(
        job_id=job.JobID,
        file_name=file.filename or "",
        headers=inspection["headers"],
        detected_email_columns=inspection["detected_email_columns"],
        detected_roles=inspection["detected_roles"],
        sheet_names=inspection["sheet_names"],
    )


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), user=Depends(require_user)):
    return job_service.list_jobs(db, user)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/start", response_model=JobOut)
def start_job(job_id: int, payload: StartJobRequest, db: Session = Depends(get_db), user=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.Status not in ("QUEUED", "FAILED", "CANCELLED"):
        raise HTTPException(status_code=400, detail=f"Job cannot be started while in status {job.Status}")

    start_request = payload.model_dump()
    job_service.update_job(
        db, job_id,
        EmailColumn=payload.email_column,
        TitleColumn=payload.title_column,
        IndustryColumn=payload.industry_column,
        OptionsJson=json.dumps(start_request, default=str),
        Status="QUEUED",
        ErrorMessage=None,
    )
    job_worker.submit_job(job_id, start_request, payload.merge_to_master)
    log_activity(db, "FILTRATION_STARTED", user=user, job_id=job_id)
    return job_service.get_job(db, job_id)


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.Status not in ("QUEUED", "IMPORTING", "PROCESSING"):
        raise HTTPException(status_code=400, detail=f"Job cannot be cancelled while in status {job.Status}")
    job_service.update_job(db, job_id, Status="CANCELLING")
    log_activity(db, "FILTRATION_CANCELLED", user=user, job_id=job_id)
    return job_service.get_job(db, job_id)


@router.post("/{job_id}/retry", response_model=JobOut)
def retry_job(job_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.Status not in ("FAILED", "CANCELLED"):
        raise HTTPException(status_code=400, detail="Only FAILED or CANCELLED jobs can be retried")
    if not job.OptionsJson:
        raise HTTPException(status_code=400, detail="No prior run configuration found for this job")

    start_request = json.loads(job.OptionsJson)
    job_service.update_job(db, job_id, Status="QUEUED", ErrorMessage=None, ProgressPercent=0, CurrentStep=None)
    job_worker.submit_job(job_id, start_request, start_request.get("merge_to_master", True))
    log_activity(db, "FILTRATION_STARTED", user=user, job_id=job_id, message="retry")
    return job_service.get_job(db, job_id)


@router.get("/{job_id}/results", response_model=list[JobResultOut])
def get_job_results(job_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_service.get_job_results(db, job_id)


@router.get("/{job_id}/download/{download_type}")
def download_job_output(job_id: int, download_type: str, db: Session = Depends(get_db), user=Depends(require_user)):
    job = job_service.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if download_type.lower() == "report":
        from app.config import get_settings

        path = get_settings().job_dir(job_id) / "output" / "Report.xlsx"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Consolidated report not available for this job")
        log_activity(db, "DOWNLOAD", user=user, job_id=job_id, message="Report.xlsx")
        return FileResponse(str(path), filename=f"Job_{job_id}_Report.xlsx")

    results = job_service.get_job_results(db, job_id)
    match = next((r for r in results if r.ReasonCode.upper() == download_type.upper()), None)
    if not match or not match.OutputFilePath:
        raise HTTPException(status_code=404, detail=f"No output file for category '{download_type}'")

    path = Path(match.OutputFilePath)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file is missing on disk")
    log_activity(db, "DOWNLOAD", user=user, job_id=job_id, message=path.name)
    return FileResponse(str(path), filename=path.name)
