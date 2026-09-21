# FT -- Filtration Tool (SQL Server Edition)

A local Windows application for cleaning, deduplicating, and categorizing
very large (hundreds of thousands to 10M+ row) contact/e-mail CSV and Excel
datasets. SQL Server does the heavy set-based work; Python (FastAPI)
orchestrates uploads, jobs, and reporting; React (Ant Design) is the UI.

```
React (Ant Design)  --->  FastAPI (Python)  --->  SQL Server (LAP-S2M059)
                                 |
                                 v
                         Local Windows Storage
                    (uploads / jobs / reports / backups / logs)
```

No MySQL/PostgreSQL/SQLite/MongoDB, no S3, no cloud dependency. SQL Server
is the single authoritative datastore.

---

## 1. Repository layout

```
FT/
├── backend/            FastAPI app (Python)
│   ├── app/
│   │   ├── main.py         FastAPI entrypoint
│   │   ├── config.py       .env-driven settings
│   │   ├── database.py     SQL Server connection + init_db()
│   │   ├── models/         SQLAlchemy ORM models
│   │   ├── schemas/        Pydantic request/response schemas
│   │   ├── routers/        REST API endpoints
│   │   ├── services/       business logic (auth, jobs, master, reports, ...)
│   │   ├── workers/        background job execution
│   │   ├── filtration/     pure-Python rule engine + SQL orchestration
│   │   └── utils/          security, safe-identifier helpers
│   ├── requirements.txt
│   └── .env.example
├── frontend/           React + Ant Design app (Vite)
├── sql/
│   ├── schema/          idempotent table/index DDL
│   ├── procedures/      sp_FT_* stored procedures
│   └── seed/            idempotent default reference data
├── scripts/             init_db.py, run_cleanup.py, backup_database.py, ...
├── sample_data/         sample CSV/XLSX + expected results (see its README)
├── tests/               pytest suite (pure-logic + FastAPI wiring tests)
├── data/                uploads / jobs / reports / backups / logs (local)
└── pytest.ini
```

---

## 2. Prerequisites (Windows machine, e.g. `LAP-S2M059`)

1. **SQL Server** (2017 or later) installed and running locally, with
   Windows Authentication enabled (or a SQL login if you prefer).
2. **ODBC Driver 17 or 18 for SQL Server** installed --
   https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
3. **Python 3.11+** -- https://www.python.org/downloads/windows/
4. **Node.js 18+** (for the React frontend) -- https://nodejs.org/
5. Enough free disk space for `DATA_ROOT` (uploads/jobs/reports can get
   large for multi-million-row files).

---

## 3. SQL Server setup

You do **not** need to run any `.sql` file by hand -- `scripts/init_db.py`
(and the FastAPI app's own startup routine) creates the `FT_Filtration`
database, every table, every index, every stored procedure, and seeds the
default reference data automatically, and it is **idempotent**: safe to
run again after an upgrade without touching existing data.

If you prefer to run the SQL by hand (e.g. via SSMS), execute, in order:

```
sql/schema/000_create_database.sql
sql/schema/010_reference_tables.sql
sql/schema/020_core_tables.sql
sql/schema/030_indexes.sql
sql/procedures/000_helper_functions.sql
sql/procedures/*.sql                      (any order after the file above)
sql/seed/seed_reference_data.sql
```

Every script uses `IF ... IS NULL` / `CREATE OR ALTER` / `MERGE ... WHEN
NOT MATCHED` guards, so re-running any of them is always safe.

---

## 4. Backend setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Edit `.env`:

```env
SQL_SERVER=LAP-S2M059
SQL_DATABASE=FT_Filtration
SQL_DRIVER=ODBC Driver 17 for SQL Server
SQL_TRUSTED_CONNECTION=True
DATA_ROOT=D:\FT_Data
```

Leave `SQL_TRUSTED_CONNECTION=True` for Windows Authentication (the
FastAPI process then connects to SQL Server as whichever Windows account
runs it). Set it to `False` and fill in `SQL_USERNAME`/`SQL_PASSWORD` to
use SQL Server Authentication instead.

Initialize the database (optional -- the app also does this automatically
on startup):

```powershell
python ..\scripts\init_db.py
```

Expected output: `FT_Filtration database initialized successfully.` A
default `SUPER_ADMIN` user is created **only if no users exist yet**:

```
Username: admin              (DEFAULT_SUPERADMIN_USERNAME)
Password: ChangeMe!123        (DEFAULT_SUPERADMIN_PASSWORD)
```

**Change this password immediately after first login** (Users screen, or
`PUT /api/users/{id}`).

Run the API:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API documentation,
and `http://localhost:8000/api/health` to confirm SQL Server connectivity.

---

## 5. Frontend setup

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` to
`http://localhost:8000` (see `vite.config.js`); adjust
`VITE_API_PROXY_TARGET` / `VITE_API_BASE_URL` if the backend runs
elsewhere.

For a production build served as static files:

```powershell
npm run build
```

`frontend/dist/` can then be served by any static file server (IIS, nginx,
or FastAPI's own `StaticFiles`).

---

## 6. First end-to-end run

1. Log in as `admin` (see above).
2. Optionally seed a few demo reference-list entries so every category is
   exercised: run `sample_data/sample_reference_lists.sql` against
   `FT_Filtration`.
3. Go to **Filtration**, upload `sample_data/sample_leads.csv`.
4. Confirm the `Email` column, leave the default filter toggles checked,
   click **Start Filtration**.
5. Watch progress on the Job page; when `COMPLETED`, check the Report
   Summary against `sample_data/README.md`'s expected numbers.
6. Download `Kept.csv`, the other per-category CSVs, or the consolidated
   `Report.xlsx`.
7. Check **Master Files** -- the Kept rows should now also appear in the
   permanent Master dataset (since "Merge to Master" defaults on).

See `sample_data/README.md` for a multi-sheet Excel test and a
Duplicate-vs-Master test.

---

## 7. Running the automated test suite

```bash
pip install -r backend/requirements.txt
pytest
```

The suite (52 tests) covers email normalization, invalid-email detection,
duplicate detection, TLD classification (including multi-label TLDs like
`.co.uk`), the personal-domain list, every username rule, the wildcard
keyword matcher, safe-identifier handling, password hashing / JWT
issuance, multi-sheet Excel ingestion (verifies every sheet is read, not
just `Sheet1`), and the full FastAPI application wiring (including a
graceful, human-readable failure path when SQL Server is unreachable).
It also replays the exact rule pipeline against `sample_data/sample_leads.csv`
in pure Python and asserts the documented category breakdown.

These tests do **not** require a live SQL Server connection -- they
exercise the pure business-logic modules and the API's dependency graph
directly. Exercising the T-SQL stored procedures themselves requires a
real SQL Server instance (see section 3); the SQL was written and
reviewed for correctness against that logic but a live run against
`LAP-S2M059` (or any SQL Server 2017+ instance) is required to verify it
end-to-end, since no SQL Server was available in this environment.

---

## 8. Operations

### Cleanup (retention)

```powershell
python scripts\run_cleanup.py
```

Removes stale uploads/temp files/old report output/staging tables for
long-finished jobs per the `*_RETENTION_*` settings in `.env`. **Never**
touches `FT_MasterEmails` or `FT_OtherTLDMaster`. Schedule nightly via
Windows Task Scheduler:

```powershell
schtasks /Create /SC DAILY /TN "FT Cleanup" /TR "C:\FT\backend\.venv\Scripts\python.exe C:\FT\scripts\run_cleanup.py" /ST 02:00
```

### Backup

```powershell
python scripts\backup_database.py
```

Runs a native `BACKUP DATABASE` to `BACKUP_DIRECTORY` and prunes backups
older than `BACKUP_RETENTION_DAYS`. Requires the connecting account to
hold the SQL Server `BACKUP DATABASE` permission.

### Concurrency

`MAX_CONCURRENT_JOBS` (default `1`) bounds how many filtration jobs run at
once, via a bounded thread pool (see
`backend/app/workers/job_worker.py` for the rationale: SQL Server does the
CPU-heavy work, so Python's role is I/O-bound orchestration, which a
thread pool handles well without the Windows `multiprocessing`/`fork`
pitfalls the spec warns about).

---

## 9. Troubleshooting

**"SQL Server connection failed"** (shown on `/api/health` and in logs):

1. Is SQL Server running? (`services.msc` -> SQL Server (MSSQLSERVER))
2. Is `SQL_SERVER` in `.env` correct? (`LAP-S2M059`, or `LAP-S2M059\INSTANCENAME`)
3. Does the `FT_Filtration` database exist? Run `scripts\init_db.py`.
4. Windows Authentication: is the account running the backend allowed to
   log in to SQL Server? (SSMS -> Security -> Logins)
5. Is the ODBC driver installed? Check "ODBC Data Sources (64-bit)" ->
   Drivers tab for "ODBC Driver 17/18 for SQL Server".

**Upload fails with "Unsupported file type"**: only `.csv`, `.xlsx`,
`.xlsm` are accepted.

**Upload fails with a size error**: raise `MAX_FILE_SIZE_GB` in `.env`.

**A filtration job is stuck in `PROCESSING`**: check
`data/logs` (or the console the backend is running in) for the full stack
trace -- the UI only ever shows a short, human-readable message
(`ErrorMessage` on the job), never a raw traceback, by design.

**BULK INSERT fails / falls back to slower row-by-row import**: this
happens when the SQL Server service account cannot see the uploaded file's
path (common when SQL Server and the backend run under different
accounts, or on different machines). The import still completes correctly
via chunked `executemany`, just more slowly for very large files. Running
the backend directly on the SQL Server box (as this spec assumes) avoids
this.

**Ports already in use**: change `--port` on the `uvicorn` command and
`VITE_API_BASE_URL` / the Vite proxy target to match.

---

## 10. Design decisions worth knowing about

These are documented here per the instruction to make a reasonable,
documented decision wherever the specification leaves an implementation
detail open, rather than stopping to ask:

- **Staging tables are never row-deleted during processing.** Every rule
  tags a `ReasonCode` column (`WHERE ReasonCode IS NULL` guards on every
  step), which is what makes "first applicable reason wins" (spec section
  54) trivial and keeps every row fully auditable until the job finishes.
- **Reference-table shape for keywords vs. titles/industries.** Section 17
  describes generic keyword categories (Email Username / Title / Industry)
  while section 28 lists three distinct tables
  (`FT_RestrictedKeywords`/`FT_RestrictedTitles`/`FT_RestrictedIndustries`).
  This build keeps `FT_RestrictedKeywords` for the e-mail-username rule
  (with a `Category` column for future extension) and uses the two
  dedicated tables for the Title/Industry filters, all sharing one
  wildcard-matching function on each side (Python: `filtration/keywords.py`;
  SQL: `fn_FT_WildcardToLike`).
- **The doubled numeric-username rule** (section 21 states it twice) is
  implemented exactly once, in `sp_FT_FilterNumericUsernames` /
  `username_rules.is_invalid_numeric_username`, independently toggleable
  from the one-character-username rule.
- **Background jobs use a `ThreadPoolExecutor`, not
  `multiprocessing.get_context("spawn")`.** SQL Server performs all
  CPU-heavy set-based work; Python only streams files and waits on network/
  disk I/O, which releases the GIL. A bounded thread pool gives real
  concurrency for this workload without the added complexity Windows
  process-spawning would introduce. See the docstring in
  `backend/app/workers/job_worker.py`.
- **BULK INSERT with a chunked-`executemany` fallback.** Native `BULK
  INSERT` is attempted first for CSV (fastest path, mirrors the original
  reference workflow this tool replaces); if the SQL Server service
  account cannot see the file path, it falls back automatically.
