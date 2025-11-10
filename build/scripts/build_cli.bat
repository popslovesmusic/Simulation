@echo off
REM Build DASE CLI using MSVC

echo Building DASE CLI...

REM Set up MSVC environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

REM Navigate to CLI directory
cd /d "D:\isoG\New-folder\sase amp fixed\dase_cli"

REM Compile
cl.exe /EHsc /std:c++17 /MD /O2 /I"src" /I"..\src\cpp" ^
    src\main.cpp ^
    src\command_router.cpp ^
    src\engine_manager.cpp ^
    /Fe:dase_cli.exe

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build successful! dase_cli.exe created.
