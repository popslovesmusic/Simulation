@echo off
REM Comprehensive test of DASE CLI - both engine types
echo ================================================================================
echo                      DASE CLI COMPREHENSIVE TEST
echo ================================================================================
echo.

echo Test 1: Phase 4B Engine (AVX2 Optimized)
echo --------------------------------------------------------------------------------
type mission_short_corrected.json | dase_cli.exe 2>nul
echo.

echo Test 2: IGSOA Complex Engine
echo --------------------------------------------------------------------------------
type mission_igsoa_complex.json | dase_cli.exe 2>nul
echo.

echo Test 3: Get Capabilities
echo --------------------------------------------------------------------------------
echo {"command":"get_capabilities","params":{}}| dase_cli.exe 2>nul
echo.

echo ================================================================================
echo All tests completed!
echo ================================================================================
