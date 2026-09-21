@echo off
cd /d "%~dp0"
echo Launching FT backend and frontend in separate windows ...
start "FT Backend  (http://localhost:8000)"  cmd /k call start_backend.bat
timeout /t 3 /nobreak >nul
start "FT Frontend (http://localhost:5173)" cmd /k call start_frontend.bat
timeout /t 6 /nobreak >nul
start "" http://localhost:5173
echo.
echo Two new windows should now be running the backend and frontend.
echo Your browser should open http://localhost:5173 automatically.
echo Log in with: admin / ChangeMe!123  (change this password immediately).
echo This window can be closed - closing the OTHER two windows stops the app.
pause
