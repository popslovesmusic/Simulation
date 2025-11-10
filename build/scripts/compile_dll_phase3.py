#!/usr/bin/env python3
"""
Compile DASE Engine DLL with Phase 3 aggressive optimizations.
"""

import subprocess
import sys
import os

print("="*60)
print("DASE Engine DLL Compilation - Phase 3 Optimizations")
print("="*60)
print()

# Compiler and linker paths
CL_EXE = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\HostX86\x64\cl.exe"
LINK_EXE = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\HostX86\x64\link.exe"

# Include paths
MSVC_INCLUDE = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\include"
UCRT_INCLUDE = r"C:\Program Files (x86)\Windows Kits\10\include\10.0.26100.0\ucrt"
UM_INCLUDE = r"C:\Program Files (x86)\Windows Kits\10\include\10.0.26100.0\um"
SHARED_INCLUDE = r"C:\Program Files (x86)\Windows Kits\10\include\10.0.26100.0\shared"

# Library paths
MSVC_LIB = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\lib\x64"
UCRT_LIB = r"C:\Program Files (x86)\Windows Kits\10\lib\10.0.26100.0\ucrt\x64"
UM_LIB = r"C:\Program Files (x86)\Windows Kits\10\lib\10.0.26100.0\um\x64"

# Phase 3: Maximum performance compiler flags
COMPILE_FLAGS = [
    "/c",
    "/EHsc",
    "/bigobj",
    "/std:c++17",
    "/O2",           # Maximum optimization
    "/Ob3",          # Aggressive inlining
    "/Oi",           # Intrinsics
    "/Ot",           # Favor speed
    "/Oy",           # Frame pointer omission
    "/arch:AVX2",    # AVX2 SIMD
    "/fp:fast",      # Fast floating point
    "/GL",           # Whole program optimization
    "/DNOMINMAX",
    "/DDASE_BUILD_DLL",
    "/openmp",
    "/MD",
    "/Qpar",         # Auto-parallelization
    "/favor:INTEL64", # Intel CPU optimization
    f"/I{os.path.join(os.getcwd(), 'src', 'cpp')}",
    "/I.",
    f"/I{MSVC_INCLUDE}",
    f"/I{UCRT_INCLUDE}",
    f"/I{UM_INCLUDE}",
    f"/I{SHARED_INCLUDE}",
]

# Source files
SOURCES = [
    r"src\cpp\analog_universal_node_engine_avx2.cpp",
    r"src\cpp\dase_capi.cpp",
]

# Link flags
LINK_FLAGS = [
    "/DLL",
    "/LTCG",         # Link-time code generation
    "/OPT:REF",      # Remove unreferenced functions
    "/OPT:ICF",      # Identical COMDAT folding
    "/OUT:dase_engine_phase3.dll",
    "/LIBPATH:.",
    f"/LIBPATH:{MSVC_LIB}",
    f"/LIBPATH:{UCRT_LIB}",
    f"/LIBPATH:{UM_LIB}",
]

LIBS = ["libfftw3-3.lib"]

print("Step 1: Compiling source files with aggressive optimizations...")
compile_cmd = [CL_EXE] + COMPILE_FLAGS + SOURCES
print(f"Running: {' '.join([CL_EXE] + COMPILE_FLAGS[:10] + ['...'])}")
result = subprocess.run(compile_cmd, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("COMPILATION FAILED:")
    print(result.stderr)
    sys.exit(1)

print()
print("Step 2: Linking DLL with LTCG and optimization...")
obj_files = [
    "analog_universal_node_engine_avx2.obj",
    "dase_capi.obj",
]
link_cmd = [LINK_EXE] + LINK_FLAGS + obj_files + LIBS
print(f"Running: {LINK_EXE} /DLL /LTCG /OPT:REF /OPT:ICF ...")
result = subprocess.run(link_cmd, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("LINKING FAILED:")
    print(result.stderr)
    sys.exit(1)

print()
print("="*60)
print("SUCCESS! dase_engine_phase3.dll created")
print("="*60)

# Get file size
dll_size = os.path.getsize("dase_engine_phase3.dll")
print(f"DLL size: {dll_size:,} bytes")
print()
print("Phase 3 Optimizations Applied:")
print("  ✓ /O2 /Ob3 /Oi /Ot /Oy - Maximum speed optimization")
print("  ✓ /arch:AVX2 - SIMD vectorization")
print("  ✓ /fp:fast - Fast floating point")
print("  ✓ /GL /LTCG - Whole program optimization")
print("  ✓ /Qpar - Auto-parallelization")
print("  ✓ /favor:INTEL64 - Intel CPU tuning")
print("  ✓ /OPT:REF /OPT:ICF - Link-time optimization")
print()
