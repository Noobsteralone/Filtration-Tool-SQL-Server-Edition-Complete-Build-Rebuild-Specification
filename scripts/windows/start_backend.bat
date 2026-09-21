@echo off
cd /d "%~dp0..\..\backend"
if not exist .venv (
    echo Virtual environment not found. Run scripts\windows\setup.bat first.
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
echo Starting FT backend on http://localhost:8000  (Ctrl+C to stop)
echo API docs: http://localhost:8000/docs
echo Health check: http://localhost:8000/api/health
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
