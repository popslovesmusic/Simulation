@echo off
REM Static Code Analysis Wrapper for IGSOA-SIM
REM Windows batch file to run the Python static analysis script

setlocal

echo.
echo ===============================================================================
echo                    IGSOA-SIM Static Code Analysis
echo ===============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.7 or later.
    echo.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Run the Python analysis script
python "%SCRIPT_DIR%run_static_analysis.py" %*

REM Check exit code
if errorlevel 1 (
    echo.
    echo [ERROR] Static analysis failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Analysis complete!
echo.
echo Next steps:
echo   1. Review the analysis report in build/analysis_reports/
echo   2. Fix critical errors and warnings
echo   3. Run again to verify fixes
echo.

pause
exit /b 0
