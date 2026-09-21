#!/usr/bin/env python3
"""
Runs FT database initialization (creates the FT_Filtration database, all
tables/indexes/stored procedures, and seeds default reference data) without
starting the web server. Safe to re-run at any time (idempotent).

Usage (from the `backend` directory, with its virtualenv active):

    python ../scripts/init_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import DatabaseConnectionError, init_db  # noqa: E402


def main() -> int:
    try:
        init_db()
    except DatabaseConnectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("FT_Filtration database initialized successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
