# Performance Baseline - IGSOA-SIM

**Date Established**: 2025-11-12 (Week 1 Day 2)
**Status**: 🔄 In Progress - Collecting baseline data
**Purpose**: Comprehensive performance baseline for optimization tracking

---

## Executive Summary

This document serves as the single source of truth for IGSOA-SIM performance baselines. All optimization efforts will be measured against these baselines to track improvement.

**Current Status**:
- ✅ Profiling infrastructure established
- 🔄 Python baseline: In progress
- ⏳ C++ baseline: Pending
- ⏳ Frontend baseline: Pending

---

## Table of Contents

1. [Python Backend Baseline](#1-python-backend-baseline)
2. [C++ Engines Baseline](#2-c-engines-baseline)
3. [Frontend Baseline](#3-frontend-baseline)
4. [Integration Baseline](#4-integration-baseline)
5. [Optimization Targets](#5-optimization-targets)
6. [Historical Data](#6-historical-data)

---

## 1. Python Backend Baseline

### Test Environment

```
Python Version: 3.11.x
NumPy Version: 1.24.x
PyTorch Version: 2.0.x
CPU: [To be filled]
RAM: [To be filled]
OS: Windows 11
```

### 1.1 Cache Operations

**Test**: Save/Load 1000x1000 NumPy array (8 MB)

| Operation | Time (ms) | Throughput (MB/s) | Target |
|-----------|-----------|-------------------|--------|
| Save | TBD | TBD | <50 ms |
| Load | TBD | TBD | <20 ms |
| Metadata Query | TBD | - | <5 ms |

**Command to measure**:
```bash
python scripts/profile_backend.py
```

**Bottlenecks** (to be identified):
- [ ] Serialization overhead
- [ ] Disk I/O
- [ ] Metadata JSON operations

### 1.2 Profile Generation

**Test**: Generate initial state profiles

| Profile Type | Size | Time (ms) | Target |
|--------------|------|-----------|--------|
| Gaussian 2D | 256x256 | TBD | <10 ms |
| Gaussian 3D | 64x64x64 | TBD | <50 ms |
| Soliton 2D | 256x256 | TBD | <15 ms |
| Field Triplet 3D | 64³ × 3 | TBD | <150 ms |

**Cache Hit Rate**: TBD% (target: >90%)

**Bottlenecks** (to be identified):
- [ ] NumPy array operations
- [ ] Function evaluation overhead
- [ ] Cache lookup time

### 1.3 Echo Template Generation

**Test**: Generate prime-gap echo templates

| Operation | Parameters | Time (ms) | Target |
|-----------|------------|-----------|--------|
| Single Template | 100 echoes | TBD | <20 ms |
| Parameter Sweep | 9 templates | TBD | <100 ms |
| Prime Gap Calculation | 1000 gaps | TBD | <50 ms |

**Bottlenecks** (to be identified):
- [ ] Prime number generation (sieve)
- [ ] Gap computation
- [ ] Envelope calculation

### 1.4 Mission Planning

**Test**: Mission dry-run and validation

| Operation | Complexity | Time (ms) | Target |
|-----------|-----------|-----------|--------|
| Load Mission JSON | 1 KB | TBD | <5 ms |
| Validate Schema | Basic | TBD | <10 ms |
| Build DAG | 10 commands | TBD | <20 ms |
| Dry Run | Simple mission | TBD | <50 ms |

**Bottlenecks** (to be identified):
- [ ] JSON parsing
- [ ] Schema validation
- [ ] Dependency resolution

### 1.5 Memory Usage

| Operation | Memory (MB) | Target |
|-----------|-------------|--------|
| Array Creation (1000x1000x10) | TBD (~80 MB) | <100 MB |
| Cache Save/Load | TBD | <20 MB overhead |
| Peak Usage | TBD | <500 MB |

---

## 2. C++ Engines Baseline

### Test Environment

```
Compiler: MSVC 2022 / GCC 11+
Build Type: Release (with AVX2)
Optimization: /O2 (MSVC) / -O3 (GCC)
CPU: [To be filled]
Cores: [To be filled]
```

### 2.1 DASE Engine

**Test Configuration**:
- Nodes: 10,000
- Time steps: 1,000
- dt: 0.01
- Alpha: 1.5 (fractional order)

| Metric | Value | Target |
|--------|-------|--------|
| Total Time | TBD | <1000 ms |
| Time per Step | TBD | <1 ms |
| Memory Usage | TBD | <100 MB |

**Function Breakdown** (% of total time):
| Function | Time % | Time (ms) | Notes |
|----------|--------|-----------|-------|
| `update_nodes()` | TBD% | TBD | Main loop |
| `compute_fractional_derivative()` | TBD% | TBD | Core computation |
| `apply_avx2_vectorization()` | TBD% | TBD | SIMD |
| Overhead | TBD% | TBD | Includes allocation, etc. |

**AVX2 Utilization**: TBD% (target: >80%)

**Bottlenecks** (to be identified):
- [ ] Cache misses
- [ ] Non-vectorized loops
- [ ] Memory bandwidth
- [ ] Branch mispredictions

**Profiling Command**:
```bash
# Build with profiling info
cmake -B build -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo -DDASE_ENABLE_AVX2=ON
cmake --build build --config RelWithDebInfo

# Run profiler (Visual Studio)
# Debug → Performance Profiler → CPU Usage
```

### 2.2 IGSOA Engine

#### 2D Complex Field

**Test Configuration**:
- Grid: 256 × 256
- Time steps: 100
- dt: 0.01
- R_c: 1.0

| Metric | Value | Target |
|--------|-------|--------|
| Total Time | TBD | <5000 ms |
| Time per Step | TBD | <50 ms |
| Memory Usage | TBD | <200 MB |

**Function Breakdown**:
| Function | Time % | Time (ms) | Notes |
|----------|--------|-----------|-------|
| `updateComplexField()` | TBD% | TBD | Field evolution |
| `compute_interactions()` | TBD% | TBD | Node-node |
| `apply_boundary_conditions()` | TBD% | TBD | Boundaries |
| Spatial hash lookup | TBD% | TBD | Neighbor finding |

#### 3D Complex Field

**Test Configuration**:
- Grid: 64 × 64 × 64
- Time steps: 100
- dt: 0.01

| Metric | Value | Target |
|--------|-------|--------|
| Total Time | TBD | <50000 ms |
| Time per Step | TBD | <500 ms |
| Memory Usage | TBD | <500 MB |

**Bottlenecks** (to be identified):
- [ ] Memory bandwidth (3D grids are large)
- [ ] Interaction calculation (O(N²) naive)
- [ ] Cache efficiency
- [ ] Vectorization opportunities

### 2.3 SATP Higgs Engine

#### 1D Simulation

**Test Configuration**:
- Nodes: 1,024
- Time steps: 1,000
- dt: 0.01
- FFTW wisdom: Yes

| Metric | Value | Target |
|--------|-------|--------|
| Total Time | TBD | <5000 ms |
| Time per Step | TBD | <5 ms |
| Memory Usage | TBD | <50 MB |

**Function Breakdown**:
| Function | Time % | Time (ms) | Notes |
|----------|--------|-----------|-------|
| `evolveField()` | TBD% | TBD | Field update |
| FFTW operations | TBD% | TBD | Should be fast |
| `computeGWWaveform()` | TBD% | TBD | GW generation |

**FFTW Performance**: TBD ms for 1024-point FFT (target: <1 ms with wisdom)

**Bottlenecks** (to be identified):
- [ ] Asynchronous update overhead
- [ ] FFTW planning (should be eliminated with wisdom)
- [ ] Memory copies

---

## 3. Frontend Baseline

### Test Environment

```
Browser: Chrome 120+ / Firefox 121+
React Version: 18.2
Vite Version: 5.1
Node Version: 20.x
Hardware: [To be filled]
```

### 3.1 Bundle Size

**Build Configuration**: Production (`npm run build`)

| Asset Type | Size (KB) | Gzipped (KB) | Target |
|------------|-----------|--------------|--------|
| JavaScript (total) | TBD | TBD | <500 KB |
| CSS (total) | TBD | TBD | <100 KB |
| Fonts | TBD | TBD | <200 KB |
| Images | TBD | TBD | <500 KB |
| **Total** | **TBD** | **TBD** | **<2 MB** |

**Largest Files**:
1. TBD
2. TBD
3. TBD

**Analysis Command**:
```bash
cd web/command-center
npm run build
node ../../scripts/analyze_bundle.js
```

### 3.2 Initial Load Performance

**Test**: Load homepage (cold start)

| Metric | Value | Target |
|--------|-------|--------|
| First Contentful Paint (FCP) | TBD | <1.5s |
| Largest Contentful Paint (LCP) | TBD | <2.5s |
| Time to Interactive (TTI) | TBD | <3.0s |
| Total Blocking Time (TBT) | TBD | <300ms |

**Measurement**: Chrome DevTools Lighthouse

### 3.3 Component Render Performance

**Test**: Render WaveformPlot with 10,000 data points

| Metric | Value | Target |
|--------|-------|--------|
| Initial Render | TBD | <100ms |
| Re-render (data update) | TBD | <50ms |
| Memory Usage | TBD | <50MB |

**Test**: Render MissionSelection with 100 missions

| Metric | Value | Target |
|--------|-------|--------|
| Initial Render | TBD | <100ms |
| Scroll Performance (FPS) | TBD | 60 FPS |

**Profiling**:
- Chrome DevTools → Performance tab
- Record interaction
- Analyze flame graph

### 3.4 API Call Performance

**Test**: Fetch mission data (simulated)

| Endpoint | Payload Size | Time (ms) | Target |
|----------|--------------|-----------|--------|
| GET /api/missions | 100 KB | TBD | <100ms |
| GET /api/waveform | 1 MB | TBD | <200ms |
| POST /api/run-mission | 10 KB | TBD | <50ms |

**Note**: Actual API not implemented yet. Using mock data.

---

## 4. Integration Baseline

### End-to-End Workflow

**Test**: Complete mission workflow

1. **Load Mission**: Load mission definition (JSON)
   - Time: TBD (target: <50ms)

2. **Validate**: Validate mission parameters
   - Time: TBD (target: <100ms)

3. **Initialize Cache**: Load cached profiles/kernels
   - Time: TBD (target: <200ms)
   - Cache hit rate: TBD% (target: >80%)

4. **Run Simulation**: Execute 100 time steps
   - Time: TBD (depends on engine)
   - C++ computation time: TBD

5. **Export Results**: Save waveform data
   - Time: TBD (target: <500ms)

**Total Workflow Time**: TBD (target: <10s for simple mission)

---

## 5. Optimization Targets

### Phase 1 Targets (Quick Wins)

**Python**:
- Cache operations: 2x faster (vectorization, better serialization)
- Profile generation: 1.5x faster (caching improvements)

**C++**:
- DASE: 2-3x faster (more SIMD, loop optimization)
- IGSOA: 1.5-2x faster (SoA layout, cache optimization)
- SATP: 1.2-1.5x faster (reduce overhead)

**Frontend**:
- Bundle size: -30% (code splitting, tree shaking)
- Initial load: 2x faster (lazy loading)
- Render time: 1.5x faster (memoization)

**Overall**: 2-3x end-to-end speedup

### Phase 2 Targets (Deep Optimizations)

**Python**:
- Hot paths: 10-100x faster (Cython)
- Parallelization: 4-8x on 8-core (multiprocessing)

**C++**:
- Full SIMD: 3-4x (AVX2 everywhere)
- OpenMP: 4-8x (parallelization)
- Algorithms: 2-10x (Fast Multipole, adaptive stepping)

**Frontend**:
- Web Workers: Keeps UI responsive
- Virtualization: 10-100x for large lists

**Overall**: 5-10x end-to-end speedup

---

## 6. Historical Data

### Baseline Versions

| Date | Version | Overall Performance | Notes |
|------|---------|---------------------|-------|
| 2025-11-12 | v1.0-baseline | 1.0x (reference) | Initial baseline |
| TBD | v1.1-quickwins | TBD | After Phase 1 optimizations |
| TBD | v1.2-deep | TBD | After Phase 2 optimizations |

### Performance Trends

*Charts to be added as data is collected*

---

## Data Collection Procedure

### Python Profiling

```bash
# Run profiling script
python scripts/profile_backend.py

# Output: reports/profiling/backend_profile_*.json
```

### C++ Profiling

```bash
# Build with profiling
cmake -B build -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --config RelWithDebInfo

# Profile with Visual Studio Profiler
# Or use Intel VTune / perf

# Document results in this file
```

### Frontend Profiling

```bash
# Build production bundle
cd web/command-center
npm run build

# Analyze bundle
node ../../scripts/analyze_bundle.js

# Profile in browser
# Chrome DevTools → Performance → Record

# Document results in this file
```

---

## Reporting Template

When updating baselines, use this template:

```markdown
### Update: YYYY-MM-DD

**Changed**: [What was optimized]

**Before**:
- Metric 1: X ms
- Metric 2: Y MB/s

**After**:
- Metric 1: X ms (Speedup: Nx)
- Metric 2: Y MB/s (Speedup: Nx)

**How**:
- Optimization technique 1
- Optimization technique 2

**Verification**:
- Tests passing: Yes/No
- Correctness verified: Yes/No
- No regressions: Yes/No
```

---

## Next Steps

### Immediate (Week 1 Day 2-3)

1. [ ] Run `python scripts/profile_backend.py` → Fill Python baseline
2. [ ] Profile DASE engine → Fill DASE baseline
3. [ ] Profile IGSOA engines → Fill IGSOA baseline
4. [ ] Profile SATP engine → Fill SATP baseline
5. [ ] Build and analyze frontend → Fill frontend baseline
6. [ ] Document all findings in this file

### Short-term (Week 3-4)

1. [ ] Identify top 10 bottlenecks
2. [ ] Implement quick-win optimizations
3. [ ] Re-baseline after optimizations
4. [ ] Calculate actual speedup

### Long-term (Week 5-10)

1. [ ] Implement deep optimizations
2. [ ] Continuous performance monitoring (CI/CD)
3. [ ] Maintain this baseline document

---

## References

- [Optimization Strategy](../roadmap/OPTIMIZATION_STRATEGY.md)
- [C++ Profiling Guide](CPP_PROFILING_GUIDE.md)
- [Python Profiling Script](../../scripts/profile_backend.py)
- [Frontend Analysis Script](../../scripts/analyze_bundle.js)

---

**Last Updated**: 2025-11-12
**Next Update**: After profiling complete (Week 1 Day 3)
**Status**: 🔄 Collecting baseline data
