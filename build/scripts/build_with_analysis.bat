@echo off
REM Build DASE CLI with Analysis Integration
REM Run from dase_cli directory

echo ========================================
echo Building DASE CLI with Analysis
echo ========================================

REM Create build directory
if not exist build mkdir build
cd build

REM Configure with CMake
echo.
echo Configuring with CMake...
cmake .. -G "Visual Studio 17 2022" -A x64

if errorlevel 1 (
    echo ERROR: CMake configuration failed
    pause
    exit /b 1
)

REM Build Release version
echo.
echo Building Release version...
cmake --build . --config Release

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Copy executable to dase_cli root
echo.
echo Copying executable...
copy /Y Release\dase_cli.exe ..

echo.
echo ========================================
echo Build complete!
echo Executable: dase_cli.exe
echo ========================================
echo.

cd ..
pause
