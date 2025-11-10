# DASE/IGSOA Codebase Structure and Organization

## Project Overview

Name: DASE (Dynamic Analog Simulation Engine) / IGSOA 

Purpose: High-performance computing platform for simulation and analysis of 
Spatially-Aware Temporal Physics (SATP). Provides dual-engine architecture 
for analog computation and quantum-inspired physics simulations.

Key Technology: 
- Real-valued analog computation via AVX2 SIMD optimization
- Complex-valued quantum-inspired physics simulations
- Multi-dimensional (1D/2D/3D) support
- Non-local causal interaction modeling

---

## Directory Structure and Purposes

### Root Level
F:\satp\igsoa-sim\
├── src/                  # Core source code (C++, Python, Julia)
├── dase_cli/             # Command-line JSON interface (primary executable)
├── backend/              # Node.js WebSocket backend server
├── web/                  # Web-based user interface
├── benchmarks/           # Performance benchmarking suite
├── tests/                # Unit and integration tests
├── missions/             # Pre-built mission configuration files
├── build/                # CMake build artifacts
├── docs/                 # Documentation and analysis reports
└── [numerous .md files]  # Project documentation

### src/ - Core Engine Implementation
src/
├── cpp/                  # C++ engine implementations
│   ├── analog_universal_node_engine_avx2.cpp/.h
│   ├── dase_capi.cpp/.h
│   ├── igsoa_complex_engine.h
│   ├── igsoa_complex_engine_2d.h
│   ├── igsoa_complex_engine_3d.h
│   ├── igsoa_physics.h
│   ├── igsoa_state_init_2d.h
│   └── [20+ optimization and physics headers]
├── python/               # Python bindings and tools
└── julia/                # Julia FFI wrappers

### dase_cli/ - Command-Line Interface
dase_cli/
├── src/
│   ├── main.cpp          # Entry point
│   ├── command_router.cpp/.h
│   ├── engine_manager.cpp/.h
│   ├── json.hpp
│   └── json_helper.h
├── dase_cli.exe          # Compiled executable (232KB)
└── README.md

### backend/ - Web Server Integration
backend/
├── server.js             # Express/WebSocket bridge
├── package.json
└── README.md

### web/ - Web User Interface
web/
├── dase_interface.html
├── css/
└── js/

### benchmarks/ - Performance Testing Suite
benchmarks/
├── julia/                # Julia performance tests
└── python/               # Python performance tests

### missions/ - Pre-built Simulation Configurations
missions/
├── SATP_v1.json
├── SATP_v2.json
└── [25+ mission files]

---

## Key Programming Languages

Language     | Primary Use         | Files | Key Components
-------------|---------------------|-------|---------------
C++          | Core engine         | 39    | AVX2 SIMD, physics
Julia        | High-perf FFI       | 8     | DaseEngine.jl
Python       | Tools, bindings     | 5+    | ctypes, benchmarks
JavaScript   | Web backend         | 1     | Express, WebSocket
JSON         | Configuration       | 50+   | Missions, commands

C++ Statistics: ~7,453 total lines across 39 files

---

## Main Components and Modules

### 1. Phase 4B Analog Engine
Location: src/cpp/analog_universal_node_engine_avx2.cpp/h

Purpose: High-performance real-valued analog computation
Performance: 2.85 ns/op, 351M ops/sec
Features:
- AVX2 SIMD optimization
- 1024+ node support
- Zero-copy FFI integration
- OpenMP parallelization

### 2. IGSOA Complex Engine
Location: src/cpp/igsoa_complex_*.h

Purpose: Complex-valued quantum-inspired physics simulation
Performance: ~25 ns/op, 40M ops/sec
Features:
- Complex quantum state evolution
- Non-local causal radius (R_c) parameter
- 1D/2D/3D variants
- Spectral analysis support

### 3. Command-Line Interface
Location: dase_cli/src/

Purpose: Headless JSON-based engine control
Features:
- Newline-delimited JSON protocol
- Command routing and dispatch
- Engine lifecycle management
- Real-time metrics collection

### 4. Physics Engine
Location: src/cpp/igsoa_physics*.h

Features:
- Schrödinger-like evolution equations
- Non-local interactions
- Spatial optimization (caching, hashing)

### 5. Julia FFI Wrapper
Location: src/julia/DaseEngine.jl

Interface:
- create_engine(num_nodes)
- run_mission!(engine, inputs, controls)
- get_metrics(engine)
- Zero-copy performance

### 6. Python Bindings
Location: src/python/ + src/cpp/python_bindings.cpp

Interface:
- ctypes wrappers for C API
- Benchmark harness
- Test utilities

### 7. Web Backend
Location: backend/server.js

Features:
- HTTP server (port 3000)
- WebSocket server (port 8080)
- CLI process management

---

## Build System

CMake Configuration:
- CMAKE_CXX_STANDARD: 17
- DASE_ENABLE_AVX2: ON (critical)
- DASE_ENABLE_OPENMP: ON
- DASE_BUILD_JULIA_DLLS: ON

Dependencies:
- FFTW3 (signal processing)
- OpenMP (parallelization)
- nlohmann/json (JSON parsing)

Build Outputs:
- dase_engine_phase4b.dll (27.6 KB)
- dase_cli.exe (232 KB)
- dase_engine.cp311-win_amd64.pyd (Python bindings)
- libfftw3-3.dll (2.7 MB)

---

## Test Structure

C++ Unit Tests:
- test_igsoa_complex_node.cpp
- test_igsoa_engine.cpp
- test_igsoa_physics.cpp

Integration Tests:
- test_2d_engine_comprehensive.cpp
- test_igsoa_2d.cpp
- test_igsoa_3d.cpp

Benchmarks:
- benchmarks/julia/test_julia_quick.jl (1 second)
- benchmarks/julia/benchmark_julia_endurance.jl (8-12 minutes)
- benchmarks/python/quick_benchmark_python.py

Expected Results:
- Phase 4B: 2.85 ns/op, 351M ops/sec
- IGSOA Complex: ~25 ns/op, 40M ops/sec

---

## Code Review Organization

Organize your review by these sections:

1. ARCHITECTURE & DESIGN
   - CMake build configuration
   - Project structure and modularity
   - API design (C/Julia/Python)
   - Error handling

2. CORE ENGINE IMPLEMENTATION
   - Phase 4B analog engine (AVX2, SIMD)
   - IGSOA complex engine (physics)
   - Spatial optimization (caching, hashing)
   - Physics implementations (1D/2D/3D)

3. INTERFACE LAYERS
   - C API (dase_capi.h)
   - Julia FFI wrapper
   - Python bindings
   - Command-line interface

4. COMMAND PROCESSING
   - JSON command routing
   - Engine management
   - State initialization and handling
   - Metrics collection

5. PERFORMANCE & OPTIMIZATION
   - AVX2 SIMD implementations
   - Memory alignment and allocation
   - Kernel caching strategies
   - Parallelization (OpenMP)

6. TESTING & VALIDATION
   - Unit tests
   - Integration tests
   - Benchmark suite
   - Physics validation

7. TOOLS & INTEGRATION
   - Web backend server
   - Web interface
   - Analysis tools
   - Mission configuration system

---

## Critical Design Patterns

1. Opaque Handle Pattern - C API uses opaque pointers
2. Factory Pattern - EngineManager creates instances
3. Command Router Pattern - Centralized dispatch
4. Zero-copy FFI - Julia direct memory sharing
5. Alignment-aware Allocation - 64-byte cache lines
6. Namespace Organization - dase::igsoa namespace
