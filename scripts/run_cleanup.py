#!/usr/bin/env python3
"""
Runs the configured retention cleanup once (section 48). Intended to be
scheduled via Windows Task Scheduler, e.g. nightly:

    schtasks /Create /SC DAILY /TN "FT Cleanup" /TR "python C:\\FT\\scripts\\run_cleanup.py" /ST 02:00

Never touches Master data -- only stale uploads, temp folders, old report
output, and staging tables belonging to long-finished jobs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import get_session_factory  # noqa: E402
from app.services import cleanup_service  # noqa: E402


def main() -> int:
    db = get_session_factory()()
    try:
        cleanup_service.cleanup_old_job_workspaces(db)
        cleanup_service.cleanup_old_reports(db)
        cleanup_service.cleanup_temp_files()
        cleanup_service.drop_staging_tables_for_terminal_jobs(db)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
