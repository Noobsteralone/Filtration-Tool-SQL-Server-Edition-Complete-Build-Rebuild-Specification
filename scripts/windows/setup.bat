@echo off
setlocal
cd /d "%~dp0..\.."

echo ===============================================
echo  FT Filtration Tool - First-time setup
echo ===============================================

echo.
echo [1/5] Creating Python virtual environment (backend\.venv) ...
cd backend
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Is Python 3.11+ on your PATH?
        goto :fail
    )
)
call .venv\Scripts\activate.bat

echo.
echo [2/5] Installing backend Python dependencies ...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install backend dependencies. See the error above.
    goto :fail
)

echo.
echo [3/5] Preparing backend\.env ...
if not exist .env (
    copy .env.example .env >nul
    echo Created backend\.env from the template.
    echo   Default SQL_SERVER is LAP-S2M059 with Windows Authentication.
    echo   Edit backend\.env now if your instance name is different
    echo   ^(e.g. LAP-S2M059\SQLEXPRESS^), then re-run this script.
) else (
    echo backend\.env already exists - leaving it untouched.
)

echo.
echo [4/5] Initializing the FT_Filtration database ...
echo       ^(creates tables/indexes/stored procedures, seeds defaults -
echo        safe to re-run any time^)
python ..\scripts\init_db.py
if errorlevel 1 (
    echo.
    echo Database initialization failed - see the message above.
    echo Common causes: SQL Server not running, wrong SQL_SERVER name in
    echo backend\.env, or the ODBC driver name in .env not matching what's
    echo installed. Fix it and re-run scripts\windows\setup.bat.
    goto :fail
)

cd ..

echo.
echo [5/5] Installing frontend dependencies ...
cd frontend
call npm install
if errorlevel 1 (
    echo Failed to install frontend dependencies. See the error above.
    goto :fail
)
if not exist .env (
    copy .env.example .env >nul
)
cd ..

echo.
echo ===============================================
echo  Setup complete!
echo  Run scripts\windows\start_all.bat to launch the app.
echo ===============================================
pause
exit /b 0

:fail
cd /d "%~dp0..\.."
echo.
echo Setup did not finish. Fix the error above and run this script again.
pause
exit /b 1
