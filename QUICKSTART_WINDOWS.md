# Windows Quickstart

For machines that already have **Python 3.11+**, **Node.js 18+**, and the
**ODBC Driver 17 or 18 for SQL Server** installed, and SQL Server running
locally (e.g. `LAP-S2M059`). No commands to type by hand -- just run these
`.bat` files from `scripts\windows\`.

## One-time setup

Double-click:

```
scripts\windows\setup.bat
```

This will:
1. Create `backend\.venv` and install all Python dependencies.
2. Create `backend\.env` from the template (default: `SQL_SERVER=LAP-S2M059`,
   Windows Authentication). **If your instance name is different**
   (e.g. `LAP-S2M059\SQLEXPRESS`), open `backend\.env` in Notepad, fix
   `SQL_SERVER`, save, and re-run `setup.bat`.
3. Create the `FT_Filtration` database, every table/index/stored
   procedure, and seed default reference data (safe to re-run any time).
4. Install the frontend's `node_modules`.

Watch the console output -- it tells you exactly what failed if something
does, and what to fix.

## Every time you want to run the app

Double-click:

```
scripts\windows\start_all.bat
```

This opens two windows (backend on `:8000`, frontend on `:5173`) and
opens your browser to `http://localhost:5173` automatically.

Log in:
```
Username: admin
Password: ChangeMe!123
```
**Change this password immediately** (Users page, once logged in).

To stop everything: close the two backend/frontend windows, or run
`scripts\windows\stop_all.bat`.

## Try it with sample data

Optional, to reproduce the exact category counts documented in
`sample_data\README.md`:

```
scripts\windows\seed_sample_reference_lists.bat
```

Then, in the app, go to **Filtration**, upload
`sample_data\sample_leads.csv`, confirm the `Email` column, and click
**Start Filtration**. Compare the Report Summary against
`sample_data\README.md`.

## If something goes wrong

- `start_all.bat` opens a window that closes immediately / shows an
  error -> re-run `scripts\windows\start_backend.bat` or
  `start_frontend.bat` directly and read the error text (they `pause`
  before closing).
- Backend starts but `http://localhost:8000/api/health` shows
  `"database_ready": false` -> read `database_error` in that response,
  it names the exact problem (SQL Server not running, wrong server name,
  missing driver, etc.). See the Troubleshooting section of `README.md`.
- Anything else -> see `README.md` section 9 (Troubleshooting).

## Scripts reference

| Script | What it does |
|---|---|
| `scripts\windows\setup.bat` | One-time: venv, pip install, `.env`, DB init, npm install |
| `scripts\windows\start_all.bat` | Launches backend + frontend + opens browser |
| `scripts\windows\start_backend.bat` | Backend only (useful for reading errors) |
| `scripts\windows\start_frontend.bat` | Frontend only |
| `scripts\windows\stop_all.bat` | Stops anything on ports 8000/5173 |
| `scripts\windows\seed_sample_reference_lists.bat` | Loads demo reference-list entries via `sqlcmd` |
