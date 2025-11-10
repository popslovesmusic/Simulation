@echo off
cd /d "D:\isoG\New-folder\sase amp fixed\dase_cli"

echo Testing simple compilation...
"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe" ^
    /I"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\include" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\ucrt" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\shared" ^
    /I"C:\Program Files (x86)\Windows Kits\10\Include\10.0.26100.0\um" ^
    /EHsc /std:c++17 /MD test_compile.cpp ^
    /link ^
    /LIBPATH:"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\lib\x64" ^
    /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64" ^
    /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\um\x64" ^
    /OUT:test_compile.exe

echo Done!
pause
