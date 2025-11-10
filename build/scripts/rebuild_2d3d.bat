@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" > nul
echo Building DASE CLI with 2D/3D engine support...
cl.exe /EHsc /std:c++17 /MD /O2 /Isrc /I..\src\cpp src\main.cpp src\command_router.cpp src\engine_manager.cpp /Fe:dase_cli.exe
if %ERRORLEVEL% EQU 0 (
    echo Build successful!
) else (
    echo Build failed with error code %ERRORLEVEL%
)
