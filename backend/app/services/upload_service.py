"""
Upload handling (sections 1-2, 9, 46). Validates file type/size, saves the
ORIGINAL file untouched into the job's input directory (section 70), and
runs cheap header-only inspection so the user can confirm/select the
e-mail column before any heavy processing starts.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings
from app.filtration.column_detection import detect_role_columns
from app.filtration.excel_reader import sheet_names, unified_headers
from app.filtration.csv_importer import read_csv_header

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


class UnsupportedFileTypeError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


def validate_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{suffix}'. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return suffix


def save_uploaded_file(job_id: int, file: UploadFile, suffix: str) -> Path:
    settings = get_settings()
    job_dir = settings.job_dir(job_id)
    dest = job_dir / "input" / f"source{suffix}"
    max_bytes = settings.MAX_FILE_SIZE_GB * 1024 * 1024 * 1024

    dest.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(dest, "wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                out.close()
                dest.unlink(missing_ok=True)
                raise FileTooLargeError(
                    f"File exceeds the configured maximum of {settings.MAX_FILE_SIZE_GB} GB."
                )
            out.write(chunk)
    return dest


def inspect_file(path: Path, suffix: str) -> dict:
    """Cheap, header-only inspection (never loads full data)."""
    if suffix == ".csv":
        headers = read_csv_header(path)
        sheets = None
    else:
        headers = unified_headers(path)
        sheets = sheet_names(path)
    roles = detect_role_columns(headers)
    return {
        "headers": headers,
        "detected_email_columns": roles["EMAIL"],
        "detected_roles": roles,
        "sheet_names": sheets,
    }
