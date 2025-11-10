@echo off
REM Build script for 2D engine comprehensive test

echo Building 2D engine comprehensive test...

"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe" ^
    /I"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\include" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\ucrt" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\shared" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\um" ^
    /I"..\src\cpp" ^
    /EHsc /std:c++17 /O2 /W3 /MD ^
    test_2d_engine_comprehensive.cpp ^
    /link ^
    /LIBPATH:"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\lib\x64" ^
    /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64" ^
    /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\um\x64" ^
    /OUT:test_2d_engine.exe

if errorlevel 1 (
    echo Build FAILED
    exit /b 1
) else (
    echo Build SUCCESSFUL
    echo Running tests...
    test_2d_engine.exe
)
