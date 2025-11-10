@echo off
echo Building IGSOA Physics Tests...

REM Set up MSVC environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1

REM Navigate to source directory
cd /d "D:\isoG\New-folder\sase amp fixed"

REM Compile test
cl.exe /EHsc /std:c++17 /MD /O2 /I"src\cpp" ^
    src\cpp\test_igsoa_physics.cpp ^
    /Fe:test_igsoa_physics.exe

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build successful!
echo.
echo Running physics tests...
echo.

test_igsoa_physics.exe

echo.
