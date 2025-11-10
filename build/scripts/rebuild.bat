@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
cl.exe /EHsc /std:c++17 /MD /O2 /Isrc /I..\src\cpp src\main.cpp src\command_router.cpp src\engine_manager.cpp /Fe:dase_cli.exe
echo Build complete, exit code: %ERRORLEVEL%
