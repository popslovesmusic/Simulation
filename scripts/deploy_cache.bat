@echo off
REM DASE Cache System - Deployment Script for Windows
REM
REM This script:
REM 1. Creates cache directory structure
REM 2. Runs warmup to pre-populate cache
REM 3. Validates cache integrity
REM 4. Shows cache statistics
REM
REM Usage: deploy_cache.bat

echo ============================================================
echo DASE CACHE SYSTEM - DEPLOYMENT
echo ============================================================

cd /d "%~dp0.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found in PATH
    exit /b 1
)

echo.
echo [1/4] Checking cache directory structure...
if not exist "cache" (
    echo Creating cache directory...
    mkdir cache
)

REM Initialize cache manager (creates structure)
python -c "import sys; sys.path.insert(0, 'backend'); from cache import CacheManager; CacheManager(root='./cache')"
if errorlevel 1 (
    echo Error: Failed to initialize cache
    exit /b 1
)
echo [OK] Cache structure ready

echo.
echo [2/4] Running cache warmup...
python backend/cache/warmup.py --root ./cache
if errorlevel 1 (
    echo Error: Cache warmup failed
    exit /b 1
)
echo [OK] Cache warmed up

echo.
echo [3/4] Validating cache integrity...
python backend/cache/dase_cache_cli.py --root ./cache validate
if errorlevel 1 (
    echo Warning: Some cache entries may be corrupted
    echo Continuing anyway...
)

echo.
echo [4/4] Displaying cache statistics...
python backend/cache/dase_cache_cli.py --root ./cache stats

echo.
echo ============================================================
echo DEPLOYMENT COMPLETE
echo ============================================================
echo.
echo Cache is ready for use.
echo.
echo Common commands:
echo   python backend/cache/dase_cache_cli.py ls
echo   python backend/cache/dase_cache_cli.py stats
echo   python backend/cache/warmup.py
echo.

exit /b 0
