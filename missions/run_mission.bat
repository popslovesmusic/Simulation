@echo off
REM Run DASE mission from JSON file
REM Usage: run_mission.bat [json_file]

if "%~1"=="" (
    echo Usage: run_mission.bat [json_file]
    echo Example: run_mission.bat mission_short_fixed.json
    exit /b 1
)

type "%~1" | dase_cli.exe
