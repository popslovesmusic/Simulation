@echo off
ECHO ========================================================
ECHO DASE INTERACTIVE RUN & ANALYZE SUITE (with Minify-Check)
ECHO ========================================================
ECHO.

REM --- Define file paths ---
SET MINIFY_SCRIPT=dase_cli\minify_json.py
SET CLI_EXE=dase_cli\dase_cli.exe
SET TEMP_MISSION_FILE=missions\temp_mission.minified.json
SET OUTPUT_LOG_FILE=analysis\raw_translation_log_v2_blend.txt
SET ANALYSIS_BAT=analyze_satp_v2.bat

REM --- 1. Prompt for mission file ---
ECHO Please enter the path to your JSON mission file:
SET /p MISSION_FILE_PRETTY="Mission File (e.g., missions\SATP_v2_blend.ndjson): "

REM Strip quotes from the input, if any
SET MISSION_FILE_PRETTY=%MISSION_FILE_PRETTY:"=%

IF NOT EXIST %MISSION_FILE_PRETTY% (
    ECHO ❌ ERROR: File not found: %MISSION_FILE_PRETTY%
    GOTO :eof
)
ECHO.

REM --- 2. Attempt to Minify the JSON file ---
ECHO [1/3] Attempting to minify %MISSION_FILE_PRETTY%...
python %MINIFY_SCRIPT% %MISSION_FILE_PRETTY% %TEMP_MISSION_FILE% > nul

REM --- Check if minify_json.py succeeded (ERRORLEVEL 0) or failed (ERRORLEVEL 1) ---
IF %ERRORLEVEL% EQU 0 (
    ECHO ✅ Minify successful. Running the minified file...
    SET MISSION_TO_RUN=%TEMP_MISSION_FILE%
) ELSE (
    ECHO ⚠️  Minify failed. Assuming file is already in the correct format.
    ECHO    Running the original file: %MISSION_FILE_PRETTY%
    SET MISSION_TO_RUN=%MISSION_FILE_PRETTY%
)
ECHO.

REM --- 3. Run the DASE Mission ---
ECHO [2/3] Running DASE mission...
ECHO    (This may take several minutes)
ECHO.

REM The %MISSION_TO_RUN% variable will be either the temp file or the original
type %MISSION_TO_RUN% | %CLI_EXE% > %OUTPUT_LOG_FILE%

IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ DASE CLI FAILED!
    ECHO    Check %OUTPUT_LOG_FILE% for errors.
    GOTO :cleanup
)
ECHO ✅ Mission complete!
ECHO ✅ Log file saved to: %OUTPUT_LOG_FILE%
ECHO.

REM --- 4. Run the Analysis Script ---
ECHO [3/3] Calling analysis script...
ECHO.
CALL %ANALYSIS_BAT%
IF %ERRORLEVEL% NEQ 0 (
    ECHO ❌ ANALYSIS SCRIPT FAILED!
    GOTO :cleanup
)
ECHO ✅ Analysis script finished.
ECHO.

:cleanup
REM --- 5. Clean up temporary file ---
ECHO Cleaning up temporary mission file...
REM Suppress errors if the temp file was never created
del %TEMP_MISSION_FILE% > nul 2> nul
ECHO.
ECHO =======================================
ECHO DONE.
ECHO Final results are in the 'analysis' directory.
ECHO =======================================