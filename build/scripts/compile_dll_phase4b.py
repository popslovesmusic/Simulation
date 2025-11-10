#!/usr/bin/env python3
"""
Build script for Phase 4B optimized DLL

Phase 4B Optimizations:
- Single parallel region (eliminates 54,750 barriers)
- Manual thread work distribution
- Better cache locality
- Expected 20-30% improvement over Phase 4A

Compilation flags remain same as Phase 4A:
- /O2 /Ob3 /Oi /Ot: Maximum speed optimizations
- /arch:AVX2: Enable AVX2 SIMD instructions
- /fp:fast: Fast floating-point model
- /GL: Whole program optimization
- /LTCG: Link-time code generation
- /openmp: OpenMP parallelization
"""

import subprocess
import sys
import os

# MSVC Compiler path (Visual Studio 2022)
CL_PATH = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\cl.exe"
LINK_PATH = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64\link.exe"

# Source files
CPP_FILES = [
    r"src\cpp\analog_universal_node_engine_avx2.cpp",
    r"src\cpp\dase_capi.cpp"
]

# Output DLL name
OUTPUT_DLL = "dase_engine_phase4b.dll"

# Compiler flags (same as Phase 4A - optimizations are in C++ code structure)
COMPILE_FLAGS = [
    "/c",              # Compile only
    "/EHsc",           # Exception handling
    "/bigobj",         # Large object files
    "/std:c++17",      # C++17 standard
    "/O2",             # Maximum speed optimization
    "/Ob3",            # Aggressive inlining (VS 2019+)
    "/Oi",             # Intrinsic functions
    "/Ot",             # Favor fast code
    "/arch:AVX2",      # Enable AVX2 instructions
    "/fp:fast",        # Fast floating-point model
    "/GL",             # Whole program optimization
    "/DNOMINMAX",      # Disable min/max macros
    "/DDASE_BUILD_DLL", # DLL export macro
    "/openmp",         # Enable OpenMP
    "/MD",             # Multithreaded DLL runtime
    "/I" + "src\\cpp", # Include directory
    "/I" + "."         # Current directory
]

# Linker flags
LINK_FLAGS = [
    "/DLL",            # Build DLL
    "/LTCG",           # Link-time code generation
    "/OPT:REF",        # Eliminate unreferenced code
    "/OPT:ICF",        # COMDAT folding
    f"/OUT:{OUTPUT_DLL}",
    "libfftw3-3.lib"   # FFTW library
]

def run_command(cmd, description):
    """Run a command and check for errors"""
    print(f"\n{description}...")

    # Properly quote each argument that may contain spaces
    quoted_cmd = []
    for arg in cmd:
        if ' ' in arg:
            quoted_cmd.append(f'"{arg}"')
        else:
            quoted_cmd.append(arg)

    cmd_str = ' '.join(quoted_cmd)
    print(f"Command: {cmd_str}")
    print("-" * 80)

    # Wrap command with vcvars64.bat to set up MSVC environment
    vcvars_path = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    full_cmd = f'cmd.exe /c ""{vcvars_path}" && {cmd_str}"'

    result = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print(f"\nERROR: {description} failed with return code {result.returncode}")
        sys.exit(1)

    print(f"{description} succeeded!")
    return result

def main():
    print("=" * 80)
    print("DASE ENGINE - PHASE 4B DLL COMPILATION")
    print("=" * 80)
    print()
    print("Phase 4B Optimizations:")
    print("  - Single parallel region (no implicit barriers)")
    print("  - Manual thread work distribution")
    print("  - Better cache locality per thread")
    print()
    print(f"Output: {OUTPUT_DLL}")
    print()

    # Verify compiler exists
    if not os.path.exists(CL_PATH):
        print(f"ERROR: MSVC compiler not found at {CL_PATH}")
        print("Please update CL_PATH in this script to match your Visual Studio installation")
        sys.exit(1)

    # Step 1: Compile source files to object files
    obj_files = []
    for cpp_file in CPP_FILES:
        obj_file = cpp_file.replace(".cpp", ".obj").replace("src\\cpp\\", "")
        obj_files.append(obj_file)

        compile_cmd = [CL_PATH] + COMPILE_FLAGS + [cpp_file]
        run_command(compile_cmd, f"Compiling {cpp_file}")

    # Step 2: Link object files into DLL
    link_cmd = [LINK_PATH] + LINK_FLAGS + obj_files
    run_command(link_cmd, "Linking DLL")

    # Step 3: Verify DLL was created
    if os.path.exists(OUTPUT_DLL):
        size_kb = os.path.getsize(OUTPUT_DLL) / 1024
        print()
        print("=" * 80)
        print("COMPILATION SUCCESSFUL!")
        print("=" * 80)
        print(f"Output DLL: {OUTPUT_DLL}")
        print(f"DLL Size:   {size_kb:.2f} KB")
        print()
        print("Phase 4B DLL is ready for benchmarking!")
        print()
        print("Next steps:")
        print("  1. Run: julia quick_benchmark_julia_phase4b.jl")
        print("  2. Compare with Phase 4A results")
        print("  3. Expected: 20-30% improvement (265-290 M ops/sec)")
        print("=" * 80)
    else:
        print()
        print("ERROR: DLL file was not created!")
        sys.exit(1)

if __name__ == "__main__":
    main()
