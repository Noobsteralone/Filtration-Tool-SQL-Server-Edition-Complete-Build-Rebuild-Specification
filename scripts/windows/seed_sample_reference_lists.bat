@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0..\.."

set SQLSERVER=LAP-S2M059
set SQLDB=FT_Filtration

if exist backend\.env (
    for /f "tokens=2 delims==" %%a in ('findstr /b "SQL_SERVER=" backend\.env') do set SQLSERVER=%%a
    for /f "tokens=2 delims==" %%a in ('findstr /b "SQL_DATABASE=" backend\.env') do set SQLDB=%%a
)

where sqlcmd >nul 2>nul
if errorlevel 1 (
    echo sqlcmd.exe was not found on PATH ^(it ships with SQL Server / SSMS
    echo tools^). Instead, open sample_data\sample_reference_lists.sql in
    echo SQL Server Management Studio, connect to %SQLSERVER%, and run it
    echo against the %SQLDB% database.
    pause
    exit /b 1
)

echo Seeding demo Restricted/Spam Domain, Keyword, Title and Industry
echo entries into %SQLDB% on %SQLSERVER% (see sample_data\README.md) ...
sqlcmd -S %SQLSERVER% -d %SQLDB% -E -i sample_data\sample_reference_lists.sql
if errorlevel 1 (
    echo.
    echo sqlcmd reported an error - see above.
    pause
    exit /b 1
)
echo Done. sample_data\sample_leads.csv should now reproduce the exact
echo category breakdown documented in sample_data\README.md.
pause
