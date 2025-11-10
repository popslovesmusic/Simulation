@echo off
echo Building IGSOA Complex Node Tests...

REM Set up MSVC environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

REM Navigate to source directory
cd /d "D:\isoG\New-folder\sase amp fixed"

REM Compile test
cl.exe /EHsc /std:c++17 /MD /O2 /I"src\cpp" ^
    src\cpp\test_igsoa_complex_node.cpp ^
    /Fe:test_igsoa_complex_node.exe

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build successful!
echo.
echo Running tests...
echo.

test_igsoa_complex_node.exe

echo.
pause
