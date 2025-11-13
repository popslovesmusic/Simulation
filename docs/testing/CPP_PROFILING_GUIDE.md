# C++ Engine Profiling Guide

**Date**: 2025-11-12
**Purpose**: Guide for profiling C++ engines to establish performance baselines

---

## Overview

This guide covers profiling the three C++ computation engines:
- **DASE** (Distributed Analog Solver Engine)
- **IGSOA** (Infinite Gauge Scalar Omega Architecture)
- **SATP** (Spatially Asynchronous Temporal Processing)

---

## Profiling Tools

### Windows (Recommended for this project)

#### 1. Visual Studio Profiler

**Best for**: CPU profiling, hot path identification

**How to use**:
1. Open solution in Visual Studio 2022
2. Build in **Release** mode with debug info:
   ```cmake
   cmake -B build -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo
   cmake --build build --config RelWithDebInfo
   ```

3. Run profiler:
   - Debug → Performance Profiler
   - Select "CPU Usage"
   - Select target executable
   - Click "Start"

4. Analyze results:
   - Top Functions view: Shows hottest functions
   - Call Tree: Shows call hierarchy
   - Flame Graph: Visual representation

**Output**: CPU usage per function, call stacks

#### 2. Intel VTune (if available)

**Best for**: Deep CPU analysis, threading, vectorization

**How to use**:
```bash
vtune -collect hotspots -result-dir vtune_results ./test_executable
vtune -report hotspots -result-dir vtune_results -format text -report-output hotspots.txt
```

#### 3. Very Sleepy (Free alternative)

**Best for**: Sampling profiler, simple to use

**How to use**:
1. Download from http://www.codersnotes.com/sleepy/
2. Launch Very Sleepy
3. Launch your executable
4. Profile for 30-60 seconds
5. Analyze call tree

---

### Linux

#### 1. perf

```bash
# Record
perf record -g ./test_executable

# Report
perf report

# Annotate (see assembly)
perf annotate function_name
```

#### 2. Valgrind (Callgrind)

```bash
# Profile
valgrind --tool=callgrind ./test_executable

# Visualize with KCacheGrind
kcachegrind callgrind.out.*
```

---

## What to Profile

### 1. DASE Engine

**Target**: `analog_universal_node_engine_avx2.cpp`

**Key functions to profile**:
- `update_nodes()` - Main computation loop
- `compute_fractional_derivative()` - Fractional calculus
- `apply_avx2_vectorization()` - SIMD operations

**Test workload**:
```cpp
// Create engine with 10,000 nodes
DASEEngine engine(10000);

// Profile 1000 time steps
for (int i = 0; i < 1000; ++i) {
    engine.step(dt);
}
```

**What to look for**:
- [ ] Is `update_nodes()` the hottest function? (should be)
- [ ] Are AVX2 intrinsics being used effectively?
- [ ] Any memory access bottlenecks (cache misses)?
- [ ] Unnecessary allocations in hot paths?

**Expected baseline**:
- ~0.1-1 ms per time step for 10,000 nodes
- >80% time in compute kernels (not overhead)
- Good vectorization (check assembly)

---

### 2. IGSOA Engine

**Target**: `igsoa_complex_engine_*.cpp`

**Key functions to profile**:
- `updateComplexField()` - Field evolution
- `compute_interactions()` - Node-node interactions
- `apply_boundary_conditions()` - Boundary handling

**Test workload**:
```cpp
// 2D: 256x256 grid
IGSOAComplexEngine2D engine(256, 256);

// Profile 100 time steps
for (int i = 0; i < 100; ++i) {
    engine.step(dt);
}
```

**What to look for**:
- [ ] Time spent in field updates vs interactions
- [ ] Neighbor lookup efficiency (spatial hash performance)
- [ ] Memory bandwidth utilization
- [ ] Loop vectorization opportunities

**Expected baseline**:
- 2D (256x256): ~10-50 ms per step
- 3D (64x64x64): ~100-500 ms per step
- Interaction computation should dominate

---

### 3. SATP Engine

**Target**: `satp_higgs_engine_*.h` (header-only)

**Key functions to profile**:
- `evolveField()` - Higgs field evolution
- `computeGWWaveform()` - Gravitational wave generation
- `detectEchoes()` - Echo detection

**Test workload**:
```cpp
// 1D Higgs field simulation
SATPHiggsEngine1D engine(1024);

// Profile 1000 steps
for (int i = 0; i < 1000; ++i) {
    engine.step(dt);
}
```

**What to look for**:
- [ ] FFTW performance (should be fast with wisdom)
- [ ] Asynchronous update overhead
- [ ] Echo detection algorithm efficiency

**Expected baseline**:
- 1D (1024 nodes): ~1-5 ms per step
- 2D (256x256): ~50-200 ms per step
- FFTW should be <10% of total time (with wisdom)

---

## Profiling Checklist

### Before Profiling

- [ ] Build in **Release** or **RelWithDebInfo** mode
- [ ] Disable logging/debug output
- [ ] Use realistic problem sizes
- [ ] Run long enough for accurate sampling (30+ seconds)
- [ ] Close other applications
- [ ] Disable CPU frequency scaling (if possible)

### During Profiling

- [ ] Record compiler flags used
- [ ] Note CPU model and core count
- [ ] Record problem size (N, grid dimensions)
- [ ] Note any anomalies (background processes, etc.)

### After Profiling

- [ ] Identify top 10 hottest functions
- [ ] Calculate % time in each major subsystem
- [ ] Check for unexpected allocations
- [ ] Verify vectorization (check assembly)
- [ ] Document findings

---

## Example Profiling Session

### Step 1: Build with profiling-friendly flags

```bash
# Windows (MSVC)
cmake -B build -S . ^
    -DCMAKE_BUILD_TYPE=RelWithDebInfo ^
    -DDASE_BUILD_TESTS=ON ^
    -DDASE_ENABLE_AVX2=ON

cmake --build build --config RelWithDebInfo
```

### Step 2: Create test executable

Create `tests/profile_dase.cpp`:
```cpp
#include "../src/cpp/analog_universal_node_engine_avx2.h"
#include <chrono>
#include <iostream>

int main() {
    const int N = 10000;
    const int steps = 1000;
    const double dt = 0.01;

    DASEEngine engine(N);
    engine.initialize_random();

    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < steps; ++i) {
        engine.step(dt);
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Total time: " << duration.count() << " ms\n";
    std::cout << "Time per step: " << duration.count() / (double)steps << " ms\n";

    return 0;
}
```

### Step 3: Profile with Visual Studio

1. Open `build/DASE_Engine.sln`
2. Set `profile_dase` as startup project
3. Debug → Performance Profiler
4. Select "CPU Usage"
5. Start profiling
6. Wait for completion
7. Analyze "Top Functions" view

### Step 4: Document results

Create `reports/profiling/dase_baseline_YYYYMMDD.txt`:
```
DASE Engine Profiling Results

Configuration:
- Nodes: 10,000
- Steps: 1,000
- dt: 0.01
- Build: Release (AVX2 enabled)
- CPU: Intel Core i7-XXXX

Results:
- Total time: 523 ms
- Time per step: 0.523 ms

Hot Functions:
1. update_nodes() - 72% (376 ms)
2. compute_fractional_derivative() - 18% (94 ms)
3. apply_boundary_conditions() - 6% (31 ms)
4. (other) - 4% (22 ms)

Observations:
- Good: Most time in compute kernels
- Good: AVX2 intrinsics visible in disassembly
- Concern: Some cache misses in interaction loop
- Opportunity: Vectorize boundary condition application

Recommendations:
1. Investigate cache miss pattern in update_nodes()
2. Consider Structure of Arrays (SoA) layout
3. Profile with larger problem sizes
```

---

## Performance Baselines

### Target Baselines (to be measured)

| Engine | Configuration | Target Time | Notes |
|--------|--------------|-------------|-------|
| DASE | 10K nodes, 1K steps | <1 ms/step | With AVX2 |
| IGSOA 2D | 256x256, 100 steps | <50 ms/step | With spatial hash |
| IGSOA 3D | 64³, 100 steps | <500 ms/step | Memory bandwidth limited |
| SATP 1D | 1024 nodes, 1K steps | <5 ms/step | With FFTW wisdom |
| SATP 2D | 256x256, 100 steps | <200 ms/step | FFT should be fast |

### Actual Baselines

*To be filled in after profiling*

---

## Bottleneck Analysis Template

```markdown
## [Engine Name] Bottleneck Analysis

### Top 3 Bottlenecks

1. **Function**: `function_name()`
   - **Time**: 45% (234 ms)
   - **Cause**: Unvectorized loop, poor data locality
   - **Fix**: Vectorize with AVX2, use SoA layout
   - **Expected speedup**: 3-4x

2. **Function**: `another_function()`
   - **Time**: 25% (130 ms)
   - **Cause**: Redundant computations
   - **Fix**: Cache intermediate results
   - **Expected speedup**: 1.5x

3. **Function**: `third_function()`
   - **Time**: 15% (78 ms)
   - **Cause**: Branch mispredictions
   - **Fix**: Branchless code, __builtin_expect
   - **Expected speedup**: 1.2x

### Overall Optimization Potential

- Current: 523 ms
- After optimizations: ~100-150 ms (estimated)
- **Speedup**: 3-5x
```

---

## Automation

### Automated Profiling Script

Save as `scripts/profile_engines.sh` (or `.bat` for Windows):

```bash
#!/bin/bash

# Build engines
cmake -B build -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo -DDASE_BUILD_TESTS=ON
cmake --build build --config RelWithDebInfo

# Profile each engine
echo "Profiling DASE..."
./build/bin/RelWithDebInfo/profile_dase > reports/profiling/dase_perf.txt

echo "Profiling IGSOA 2D..."
./build/bin/RelWithDebInfo/profile_igsoa_2d > reports/profiling/igsoa2d_perf.txt

echo "Profiling SATP..."
./build/bin/RelWithDebInfo/profile_satp > reports/profiling/satp_perf.txt

echo "Profiling complete. Results in reports/profiling/"
```

---

## Next Steps

After establishing baselines:

1. **Identify Bottlenecks**: Focus on functions taking >10% of time
2. **Prioritize**: High-impact, low-effort optimizations first
3. **Optimize**: Implement improvements (see [OPTIMIZATION_STRATEGY.md](../roadmap/OPTIMIZATION_STRATEGY.md))
4. **Re-profile**: Verify improvements
5. **Document**: Update baselines

---

## References

- [Optimization Strategy](../roadmap/OPTIMIZATION_STRATEGY.md)
- [Performance Baseline Document](PERFORMANCE_BASELINE.md) *(to be created)*
- [Intel Intrinsics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html)
- [Agner Fog's Optimization Manuals](https://www.agner.org/optimize/)

---

**Last Updated**: 2025-11-12
**Next Review**: After baseline profiling complete
