# DASE Engine - Unified CMake Build System
# Builds C++ core, Julia C API DLLs (all phases), and Python bindings

cmake_minimum_required(VERSION 3.15)
project(DASE_Engine VERSION 1.0.0 LANGUAGES CXX)

# ============================================================================
# BUILD CONFIGURATION
# ============================================================================

# FIX H1.1: Set default build type to Release for optimized builds
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message(STATUS "Setting build type to 'Release' as none was specified")
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Choose the type of build (Debug, Release, RelWithDebInfo, MinSizeRel)" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "RelWithDebInfo" "MinSizeRel")
endif()

# ============================================================================
# PROJECT OPTIONS
# ============================================================================

option(DASE_BUILD_JULIA_DLLS "Build Julia C API DLLs for all phases" ON)
option(DASE_BUILD_PYTHON "Build Python bindings" OFF)
option(DASE_BUILD_TESTS "Build C++ unit tests" OFF)
option(DASE_ENABLE_AVX2 "Enable AVX2 SIMD instructions" ON)
option(DASE_ENABLE_OPENMP "Enable OpenMP parallelization" ON)

# ============================================================================
# C++ STANDARD AND COMPILER REQUIREMENTS
# ============================================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Position Independent Code for shared libraries
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ============================================================================
# FIND DEPENDENCIES
# ============================================================================

# Find OpenMP (optional but recommended)
if(DASE_ENABLE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_CXX_FOUND)
        message(STATUS "OpenMP found: ${OpenMP_CXX_VERSION}")
    else()
        message(WARNING "OpenMP not found - parallel performance will be degraded")
    endif()
endif()

# FFTW3 - look in project root first
find_library(FFTW3_LIBRARY NAMES fftw3 libfftw3-3 PATHS ${CMAKE_CURRENT_SOURCE_DIR} NO_DEFAULT_PATH)
if(NOT FFTW3_LIBRARY)
    find_library(FFTW3_LIBRARY NAMES fftw3 libfftw3-3)
endif()

if(FFTW3_LIBRARY)
    message(STATUS "Found FFTW3: ${FFTW3_LIBRARY}")
else()
    message(FATAL_ERROR "FFTW3 library not found. Please place libfftw3-3.lib in project root.")
endif()

# Find FFTW3 header
find_file(FFTW3_HEADER fftw3.h PATHS ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/ftt NO_DEFAULT_PATH)
if(FFTW3_HEADER)
    get_filename_component(FFTW3_INCLUDE_DIR ${FFTW3_HEADER} DIRECTORY)
    message(STATUS "Found FFTW3 header: ${FFTW3_HEADER}")
endif()

# ============================================================================
# UNIFIED COMPILER FLAGS
# ============================================================================

set(DASE_COMPILE_FLAGS_MSVC
    /EHsc /bigobj /std:c++17 /O2 /Ob3 /Oi /Ot
    /fp:fast /GL /DNOMINMAX /openmp /MD
)

set(DASE_COMPILE_FLAGS_GCC
    -O3 -march=native -fopenmp -ffast-math -funroll-loops
)

# Select flags based on compiler
if(MSVC)
    set(DASE_COMPILE_FLAGS ${DASE_COMPILE_FLAGS_MSVC})
else()
    set(DASE_COMPILE_FLAGS ${DASE_COMPILE_FLAGS_GCC})
endif()

# ============================================================================
# CORE LIBRARY (Static)
# ============================================================================

add_library(dase_core STATIC
    src/cpp/analog_universal_node_engine_avx2.cpp
)

target_include_directories(dase_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cpp
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${FFTW3_INCLUDE_DIR}
)

target_link_libraries(dase_core PUBLIC ${FFTW3_LIBRARY})

# Apply compiler optimizations
target_compile_options(dase_core PRIVATE ${DASE_COMPILE_FLAGS})

# ============================================================================
# IGSOA GRAVITATIONAL WAVE ENGINE (Static Library)
# ============================================================================

add_library(igsoa_gw_core STATIC
    src/cpp/igsoa_gw_engine/core/symmetry_field.cpp
    src/cpp/igsoa_gw_engine/core/fractional_solver.cpp
    src/cpp/igsoa_gw_engine/core/projection_operators.cpp
    src/cpp/igsoa_gw_engine/core/source_manager.cpp
    src/cpp/igsoa_gw_engine/core/echo_generator.cpp
)

target_include_directories(igsoa_gw_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cpp
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${FFTW3_INCLUDE_DIR}
)

target_link_libraries(igsoa_gw_core PUBLIC ${FFTW3_LIBRARY})

# Apply compiler optimizations
target_compile_options(igsoa_gw_core PRIVATE ${DASE_COMPILE_FLAGS})

# AVX2 support
if(DASE_ENABLE_AVX2)
    if(MSVC)
        target_compile_options(dase_core PRIVATE /arch:AVX2)
    else()
        target_compile_options(dase_core PRIVATE -mavx2 -mfma)
    endif()
endif()

# OpenMP support
if(DASE_ENABLE_OPENMP AND OpenMP_CXX_FOUND)
    target_link_libraries(dase_core PUBLIC OpenMP::OpenMP_CXX)
endif()

# ============================================================================
# JULIA C API DLLS (One for each optimization phase)
# ============================================================================

if(DASE_BUILD_JULIA_DLLS)
    # Function to create DLL for each phase
    function(add_dase_dll DLL_NAME DESCRIPTION)
        add_library(${DLL_NAME} SHARED
            src/cpp/dase_capi.cpp
        )

        target_link_libraries(${DLL_NAME} PRIVATE dase_core)
        target_compile_definitions(${DLL_NAME} PRIVATE DASE_BUILD_DLL)
        target_compile_options(${DLL_NAME} PRIVATE ${DASE_COMPILE_FLAGS})

        if(DASE_ENABLE_AVX2)
            if(MSVC)
                target_compile_options(${DLL_NAME} PRIVATE /arch:AVX2)
            else()
                target_compile_options(${DLL_NAME} PRIVATE -mavx2 -mfma)
            endif()
        endif()

        # Link-time optimization
        if(MSVC)
            target_link_options(${DLL_NAME} PRIVATE /LTCG /OPT:REF /OPT:ICF)
        else()
            target_link_options(${DLL_NAME} PRIVATE -flto)
        endif()

        message(STATUS "Configured Julia DLL: ${DLL_NAME} - ${DESCRIPTION}")
    endfunction()

    # Build all phase DLLs
    add_dase_dll(dase_engine "Baseline version")
    add_dase_dll(dase_engine_phase3 "Phase 3 optimizations")
    add_dase_dll(dase_engine_phase4a "Phase 4A: Hot-path optimization")
    add_dase_dll(dase_engine_phase4b "Phase 4B: Barrier elimination (PRODUCTION)")
    add_dase_dll(dase_engine_phase4c "Phase 4C: AVX2 vectorization (deprecated)")
endif()

# ============================================================================
# TESTS
# ============================================================================

if(DASE_BUILD_TESTS)
    # GW Engine Basic Test
    add_executable(test_gw_engine_basic
        tests/test_gw_engine_basic.cpp
    )
    target_link_libraries(test_gw_engine_basic PRIVATE igsoa_gw_core)
    target_compile_options(test_gw_engine_basic PRIVATE ${DASE_COMPILE_FLAGS})

    # GW Waveform Generation Test
    add_executable(test_gw_waveform_generation
        tests/test_gw_waveform_generation.cpp
    )
    target_link_libraries(test_gw_waveform_generation PRIVATE igsoa_gw_core)
    target_compile_options(test_gw_waveform_generation PRIVATE ${DASE_COMPILE_FLAGS})

    # Echo Detection Test
    add_executable(test_echo_detection
        tests/test_echo_detection.cpp
    )
    target_link_libraries(test_echo_detection PRIVATE igsoa_gw_core)
    target_compile_options(test_echo_detection PRIVATE ${DASE_COMPILE_FLAGS})

    message(STATUS "Configured test: test_gw_engine_basic")
    message(STATUS "Configured test: test_gw_waveform_generation")
    message(STATUS "Configured test: test_echo_detection")
endif()

# ============================================================================
# INSTALLATION
# ============================================================================

if(DASE_BUILD_JULIA_DLLS)
    # Install DLLs to project root for Julia to find
    install(TARGETS dase_engine dase_engine_phase3 dase_engine_phase4a dase_engine_phase4b dase_engine_phase4c
            RUNTIME DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
            LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR})
endif()

# ============================================================================
# BUILD SUMMARY
# ============================================================================

message(STATUS "")
message(STATUS "========================================")
message(STATUS "DASE Engine Build Configuration")
message(STATUS "========================================")
message(STATUS "Build type:       ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler:     ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "C++ standard:     C++${CMAKE_CXX_STANDARD}")
message(STATUS "AVX2 enabled:     ${DASE_ENABLE_AVX2}")
message(STATUS "OpenMP enabled:   ${DASE_ENABLE_OPENMP}")
message(STATUS "")
message(STATUS "Build targets:")
message(STATUS "  - dase_core (static library)")
if(DASE_BUILD_JULIA_DLLS)
    message(STATUS "  - Julia C API DLLs (5 versions)")
endif()
if(DASE_BUILD_PYTHON)
    message(STATUS "  - Python bindings")
endif()
if(DASE_BUILD_TESTS)
    message(STATUS "  - C++ unit tests")
endif()
message(STATUS "========================================")
message(STATUS "")
