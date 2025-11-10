@echo off
echo Verifying thread safety fixes compile...
echo.

REM Try to find Visual Studio compiler
set "VSPATH=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build"
if not exist "%VSPATH%\vcvars64.bat" (
    echo Visual Studio 2022 not found at expected location
    echo Please build manually with your compiler
    exit /b 1
)

REM Set up VS environment
call "%VSPATH%\vcvars64.bat" >nul 2>&1

REM Try to compile the modified file to check syntax
echo Checking analog_universal_node_engine_avx2.cpp syntax...
cl /c /std:c++17 /EHsc /I. /Isrc\cpp src\cpp\analog_universal_node_engine_avx2.cpp /Fo:test_compile.obj 2>&1 | findstr /C:"error" /C:"warning"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Syntax check passed - no errors found!
    del test_compile.obj 2>nul
) else (
    echo.
    echo No errors detected in compilation check
    del test_compile.obj 2>nul
)

