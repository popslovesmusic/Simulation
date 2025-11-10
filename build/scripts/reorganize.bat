@echo off
REM DASE Project Reorganization Script
REM Moves development files to development/ directory

echo ================================================================================
echo                    DASE Project Reorganization
echo ================================================================================
echo.
echo This script will move development files to development/ directory.
echo Operational files will remain in place.
echo.
pause

REM Create development directory structure
echo Creating development/ directory structure...
if not exist development mkdir development
if not exist development\build_artifacts mkdir development\build_artifacts
if not exist development\test_executables mkdir development\test_executables
if not exist development\build_scripts mkdir development\build_scripts
if not exist development\source_code mkdir development\source_code
if not exist development\benchmarks mkdir development\benchmarks
if not exist development\documentation mkdir development\documentation
if not exist development\old_builds mkdir development\old_builds
if not exist development\miscellaneous mkdir development\miscellaneous

REM Move build artifacts (*.obj files)
echo Moving build artifacts...
move *.obj development\build_artifacts\ 2>nul

REM Move old DLL versions
echo Moving old engine DLLs...
move dase_engine.dll development\old_builds\ 2>nul
move dase_engine_phase3.dll development\old_builds\ 2>nul
move dase_engine_phase4a.dll development\old_builds\ 2>nul

REM Move test executables
echo Moving test executables...
move test_igsoa_*.exe development\test_executables\ 2>nul
move test_igsoa_*.obj development\test_executables\ 2>nul

REM Move build scripts
echo Moving build scripts...
move build_igsoa_*.bat development\build_scripts\ 2>nul
move compile_dll_*.py development\build_scripts\ 2>nul
move CMakeLists.txt development\build_scripts\ 2>nul

REM Move benchmarks
echo Moving benchmarks...
if exist benchmarks (
    xcopy /E /I /Y benchmarks development\benchmarks
    rmdir /S /Q benchmarks
)

REM Move documentation (keep essential ones)
echo Moving historical documentation...
if exist docs (
    xcopy /E /I /Y docs development\documentation
    rmdir /S /Q docs
)

REM Move build directory
echo Moving build cache...
if exist build (
    xcopy /E /I /Y build development\build_artifacts\build
    rmdir /S /Q build
)

REM Move miscellaneous files
echo Moving miscellaneous files...
move complete_dvsl_interface.html development\miscellaneous\ 2>nul
move dir.py development\miscellaneous\ 2>nul
move COMPREHENSIVE_ANALYSIS.md development\documentation\ 2>nul

REM Move dase_cli build artifacts
echo Cleaning dase_cli directory...
move dase_cli\*.obj development\build_artifacts\ 2>nul
move dase_cli\build_cli.bat development\build_scripts\ 2>nul
move dase_cli\build_simple.bat development\build_scripts\ 2>nul
move dase_cli\rebuild.bat development\build_scripts\ 2>nul
move dase_cli\test_compile.cpp development\build_scripts\ 2>nul
move dase_cli\dase_engine_igsoa_complex.dll development\old_builds\ 2>nul

REM Move old/redundant JSON files from dase_cli
echo Moving old JSON examples...
move dase_cli\mission_complex.json development\miscellaneous\ 2>nul
move dase_cli\mission_complex_fixed.json development\miscellaneous\ 2>nul
move dase_cli\mission_short.json development\miscellaneous\ 2>nul
move dase_cli\mission_short_fixed.json development\miscellaneous\ 2>nul
move dase_cli\igsoa_test_commands.json development\miscellaneous\ 2>nul
move dase_cli\igsoa_test_commands_v2.json development\miscellaneous\ 2>nul
move dase_cli\quick_test_commands.json development\miscellaneous\ 2>nul

REM Move CLI development docs (keep user-facing ones)
move "dase_cli\Appendix A_ Critical Operational Findings.md" development\documentation\ 2>nul
move dase_cli\json_commands_guide.md development\documentation\ 2>nul
move dase_cli\test_cli.py development\test_executables\ 2>nul
move dase_cli\test_all.bat development\test_executables\ 2>nul
move dase_cli\minify_json.py development\build_scripts\ 2>nul

REM Create summary of what remains
echo.
echo ================================================================================
echo                          Reorganization Complete!
echo ================================================================================
echo.
echo Operational files (in current directory):
echo   - dase_cli/dase_cli.exe
echo   - dase_cli/dase_engine_phase4b.dll
echo   - dase_cli/libfftw3-3.dll
echo   - dase_cli/*.json (essential examples)
echo   - dase_cli/*.md (user documentation)
echo   - web/dase_interface.html
echo   - backend/ (server files)
echo   - INTEGRATION_PLAN.md
echo.
echo Development files (in development/ directory):
echo   - build_artifacts/ (*.obj, build cache)
echo   - old_builds/ (old DLLs)
echo   - test_executables/ (test programs)
echo   - build_scripts/ (compilation scripts)
echo   - benchmarks/ (performance tests)
echo   - documentation/ (historical docs)
echo   - miscellaneous/ (utility scripts)
echo.
pause
