@echo off
cd /d "%~dp0..\..\frontend"
if not exist node_modules (
    echo Frontend dependencies not installed. Run scripts\windows\setup.bat first.
    pause
    exit /b 1
)
echo Starting FT frontend on http://localhost:5173  (Ctrl+C to stop)
echo.
npm run dev
pause
