@echo off
echo Stopping anything listening on ports 8000 (backend) and 5173 (frontend) ...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -Expand OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
echo Done. (If the backend/frontend windows are still open, you can also just close them.)
pause
