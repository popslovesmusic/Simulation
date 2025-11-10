@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
lib /DEF:libfftw3-3.def /OUT:libfftw3-3.lib /MACHINE:X64
