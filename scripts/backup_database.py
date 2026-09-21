#!/usr/bin/env python3
"""
SQL Server native backup (section 49). Runs `BACKUP DATABASE` against the
configured instance, writing to BACKUP_DIRECTORY, and prunes backups older
than BACKUP_RETENTION_DAYS. Requires the connecting account to hold the
SQL Server BACKUP DATABASE permission.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings  # noqa: E402
from app.database import DatabaseConnectionError, raw_connection  # noqa: E402


def main() -> int:
    settings = get_settings()
    backup_dir = settings.backups_dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{settings.SQL_DATABASE}_{timestamp}.bak"

    try:
        with raw_connection(autocommit=True) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "BACKUP DATABASE ? TO DISK = ? WITH INIT, COMPRESSION;",
                [settings.SQL_DATABASE, str(backup_path)],
            )
    except DatabaseConnectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Backup written to {backup_path}")

    cutoff = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
    removed = 0
    for f in backup_dir.glob(f"{settings.SQL_DATABASE}_*.bak"):
        if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink(missing_ok=True)
            removed += 1
    print(f"Removed {removed} backup(s) older than {settings.BACKUP_RETENTION_DAYS} day(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
