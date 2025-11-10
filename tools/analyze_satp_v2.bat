@echo off
ECHO =======================================
ECHO DASE SATP v2 ANALYSIS SCRIPT (Fixed v2)
ECHO =======================================
ECHO.

REM --- Define file paths ---
SET LOG_FILE_SOURCE=analysis\raw_translation_log_v2_blend.txt
REM Correct relative path from dase_cli/
SET LOG_FILE_PARAM=..\analysis\raw_translation_log_v2_blend.txt
REM Hardcoded name that analyze_translation_log.py expects
SET HARDCODED_LOG_NAME=raw_translation_log.txt

REM --- Check if log file exists from the root ---
IF NOT EXIST %LOG_FILE_SOURCE% (
    ECHO ❌ ERROR: Log file not found!
    ECHO    Expected at: %LOG_FILE_SOURCE%
    ECHO    Please run the mission first to generate the log.
    GOTO :eof
)
ECHO Found log file: %LOG_FILE_SOURCE%
ECHO.

REM --- Change to dase_cli directory as per protocol ---
ECHO Changing to dase_cli directory...
cd dase_cli
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ ERROR: Failed to change to dase_cli directory.
    GOTO :eof
)
ECHO.

REM --- STAGE 1: ANALYZE TRANSLATION ---
ECHO [1/2] ANALYZING TRANSLATION (Zero-Drift Test)...
ECHO   Copying %LOG_FILE_PARAM% to %HARDCODED_LOG_NAME% for script...
copy %LOG_FILE_PARAM% %HARDCODED_LOG_NAME% > nul

REM Run script (it will find the hardcoded "raw_translation_log.txt")
python analyze_translation_log.py
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ TRANSLATION ANALYSIS FAILED!
    del %HARDCODED_LOG_NAME% > nul
    GOTO :end
)

ECHO   Moving plot to ..\analysis\
move /Y satp_translation_track.png ..\analysis\satp_translation_track.png > nul
ECHO   Cleaning up temporary log file...
del %HARDCODED_LOG_NAME% > nul
ECHO ✅ Translation plot saved to analysis directory.
ECHO.

REM --- STAGE 2: ANALYZE EXOTIC COST ---
ECHO [2/2] ANALYZING EXOTIC COST...
REM Run script (using the CORRECT relative path)
python analyze_exotic_cost.py %LOG_FILE_PARAM%
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ EXOTIC COST ANALYSIS FAILED!
    GOTO :end
)

ECHO   Moving plot to ..\analysis\
move /Y satp_exotic_cost_profile.png ..\analysis\satp_exotic_cost_profile.png > nul
ECHO ✅ Exotic cost plot saved to analysis directory.
ECHO.

:end
REM --- Return to root directory ---
ECHO Returning to root directory...
cd ..
ECHO.
ECHO =======================================
ECHO SATP v2 ANALYSIS COMPLETE.
ECHO Results are in the 'analysis' directory.
ECHO =======================================