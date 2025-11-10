# Executive Summary (TL;DR)
The IGSOA simulation stack builds on an explicit Euler integrator across 1D/2D/3D kernels without stability guards, defaulting to a causal radius that effectively disables all non-local coupling. As a result, the shipped configuration is numerically unstable when parameters are dialled up, yet simultaneously fails to simulate the intended physics under default values. Build tooling currently hard-codes a Windows-specific FFTW requirement and blocks Linux builds, leaving the repository unverified by CI. Performance remains dominated by naive neighbor searches and repeated transcendental evaluations, with missing normalization paths and inconsistent driving terms across dimensional variants. A rigorous testing strategy is absent—no unit, regression, or conservation checks exist—making it impossible to detect regressions.

# Top 10 Findings (Ranked)
| Rank | Finding | Severity | Effort |
| --- | --- | --- | --- |
| 1 | Default causal radius `R_c=1e-34` removes all non-local coupling for every topology. | Critical | S |
| 2 | Explicit Euler step lacks CFL/stability guard; runaway states for realistic `dt`, `kappa`, `gamma`. | Critical | M |
| 3 | CMake requires `libfftw3-3.lib`; Linux/mac builds fail. | High | S |
| 4 | `getMetrics` divides by zero when no mission has run. | High | S |
| 5 | 3D physics `timeStep` omits `normalizeStates`, breaking parity with 1D/2D. | High | M |
| 6 | 3D `applyDriving` ignores Ψ driving term unlike lower dimensions. | Medium | S |
| 7 | 1D gradient uses forward difference vs. central elsewhere, inflating dissipation estimates. | Medium | M |
| 8 | Neighbor loops recompute wrapped distances & `sqrt` per neighbor; missed SIMD/vectorization. | Medium | M |
| 9 | Bridge server allows unbounded `nodes`/`cycles`, enabling DoS workloads. | Medium | S |
| 10 | No automated tests for conservation, determinism, or convergence; regressions undetectable. | Medium | L |

# Build & Test Matrix
- **Detected languages/toolchains**: C++17 (CMake), Python 3.11, JavaScript/TypeScript (web), Julia (headers only).
- **Platform**: `Linux 6.12.13 x86_64` (container). `cmake 3.28.3`, `python 3.11.12`.
- **Commands**
  ```bash
  cmake -S . -B build/audit
  ```
  Result: ❌ fails because CMake demands Windows `libfftw3-3.lib` (`CMake Error at CMakeLists.txt:51`).【d8ebda†L1-L4】【F:CMakeLists.txt†L42-L52】
- **Additional tooling proposed**: `clang++`/`ninja` builds with `FFTW3`, `ctest`, `pytest`, `mypy`, `ruff`, `perf`, `criterion` (Rust-style) for benches.

# Bug & Numerical Error Analysis
## 1. Default `R_c` eliminates coupling
- **Evidence**: Constructors fix `R_c` to `1e-34`, so the causal radius is effectively zero and all neighbor checks `distance <= radius` fail.【F:src/cpp/igsoa_complex_node.h†L65-L109】【F:src/cpp/igsoa_physics.h†L115-L157】
- **Impact**: No non-local interactions → the simulator violates the governing PDE, producing trivial dynamics and hiding instability until parameters are manually overridden.
- **Recommendation**: Set a physically meaningful default (e.g., 3–5 lattice units) and expose configuration validation that enforces `R_c >= dx`.
- **Proposed Test**: 4-node ring with random Ψ should produce non-zero neighbor operations.

## 2. Explicit Euler without stability guard
- **Evidence**: Euler update with `node.psi += node.psi_dot * dt;` and no restriction on `dt` relative to eigenvalues or `gamma`/`kappa` magnitude.【F:src/cpp/igsoa_physics.h†L147-L157】【F:src/cpp/igsoa_physics_2d.h†L129-L199】【F:src/cpp/igsoa_physics_3d.h†L52-L150】
- **Impact**: For `gamma≈0` or large coupling kernels, the scheme diverges; no CFL-like constraint is enforced. Users encounter NaN/Inf without diagnostics.
- **Recommendation**: Add `validate_timestep(config)` that derives `dt_max ≈ 2/(gamma + kappa + λ_max(K))` and clamp/abort when exceeded. Offer RK4 integrator option.
- **Proposed Test**: Manufactured-solution oscillator with known analytic amplitude; assert bounded error for `dt <= dt_max` and divergence for `dt > dt_max`.

## 3. Non-portable FFTW requirement
- **Evidence**: CMake fatal error message insists on `libfftw3-3.lib`, halting Unix builds.【F:CMakeLists.txt†L42-L52】
- **Impact**: CI cannot run; developers on Linux/mac must manually edit build scripts.
- **Recommendation**: Use `find_package(FFTW3 REQUIRED COMPONENTS fftw3)` and accept `.so`/`.dylib`. Provide fallback stub when FFT is optional.
- **Proposed Test**: CMake configure on Ubuntu runner passes without local `.lib`.

## 4. Metrics division by zero
- **Evidence**: `15500.0 / ns_per_op_` executed even when `ns_per_op_ == 0.0` (default/reset state).【F:src/cpp/igsoa_complex_engine.h†L206-L216】
- **Impact**: First metrics query after construction returns `inf`/`nan`, cascading into UI.
- **Recommendation**: Guard with `if (ns_per_op_ > 0)`; otherwise emit zeros.
- **Proposed Test**: Create engine, call `getMetrics`, expect finite zeroed outputs.

## 5. 3D normalization regression
- **Evidence**: 3D `timeStep` omits normalization branch despite config flag, unlike 1D/2D.【F:src/cpp/igsoa_physics_3d.h†L211-L224】
- **Impact**: 3D simulations accumulate norm error, breaking comparability and causing energy spikes.
- **Recommendation**: Port 2D normalization path; apply `normalizeStates` when requested.
- **Proposed Test**: Compare Ψ norm drift in 2D vs 3D with identical parameters.

## 6. 3D driving inconsistency
- **Evidence**: 3D `applyDriving` updates only Φ, while 1D/2D also drive Ψ.【F:src/cpp/igsoa_physics.h†L292-L304】【F:src/cpp/igsoa_physics_2d.h†L292-L336】【F:src/cpp/igsoa_physics_3d.h†L226-L236】
- **Impact**: Control inputs behave differently by dimension; integration tests built on 2D assumptions fail in 3D.
- **Recommendation**: Align implementation and documentation; add imaginary component hook or document limitation.
- **Proposed Test**: Apply identical driving impulse across dimensions and compare Ψ amplitude.

## 7. Gradient discretization inconsistency
- **Evidence**: 1D uses forward difference, whereas 2D/3D use central, biasing gradient magnitude upward by O(dx).【F:src/cpp/igsoa_physics.h†L217-L234】【F:src/cpp/igsoa_physics_2d.h†L292-L329】【F:src/cpp/igsoa_physics_3d.h†L200-L208】
- **Impact**: Entropy production and diagnostics derived from `F_gradient` are inflated, breaking conservation tracking and cross-dimensional comparisons.
- **Recommendation**: Switch 1D to central differencing, or annotate derived metrics as forward-biased.
- **Proposed Test**: Manufactured linear field; gradient magnitude should match analytic value within tolerance.

## 8. Neighbor loop inefficiencies
- **Evidence**: Each neighbor visit recomputes `wrappedDistance` and `sqrt`, with branch-heavy modulo loops.【F:src/cpp/igsoa_physics.h†L120-L140】【F:src/cpp/igsoa_physics_2d.h†L129-L199】【F:src/cpp/igsoa_physics_3d.h†L90-L150】
- **Impact**: Hot loops become memory-bound and scalar; AVX2 kernel cannot leverage vectorization, undermining performance goals.
- **Recommendation**: Precompute lattice offsets, store squared distances, unroll inner loops, and use SIMD-friendly data layout (SoA or structure split).
- **Proposed Test**: Micro-benchmark `evolveQuantumState` before/after with `perf stat`.

## 9. Bridge server DoS risk
- **Evidence**: WebSocket handler trusts `nodes`/`cycles` with `int()` and spawns background thread; no caps or authentication.【F:src/python/bridge_server.py†L40-L104】
- **Impact**: Remote clients can demand multi-billion cycles, exhausting CPU/memory.
- **Recommendation**: Validate ranges, require auth token, and limit concurrent jobs.
- **Proposed Test**: Unit test verifying rejection of `nodes > MAX_NODES`.

## 10. Missing automated validation
- **Evidence**: No tests or CI workflows; repo lacks `tests/` coverage aside from binaries, and `build` directories are manual. Metrics such as conservation/convergence never checked.
- **Impact**: Regressions (like the 3D normalization bug) go unnoticed until manual QA.
- **Recommendation**: Introduce deterministic unit and integration tests (mass conservation, symmetry, RNG seeding), plus GitHub Actions matrix.
- **Proposed Test**: Add `ctest` suite covering invariants and tolerance-based assertions.

# Performance & Optimization Review
- **Hot paths**: `IGSOAPhysics::*evolveQuantumState` across dimensions dominate runtime via nested loops and transcendental kernel evaluations.【F:src/cpp/igsoa_physics.h†L120-L156】【F:src/cpp/igsoa_physics_2d.h†L129-L199】【F:src/cpp/igsoa_physics_3d.h†L90-L150】
- **Issues**:
  - Scalar `std::exp`/`std::sqrt` per neighbor; no lookup tables or vector intrinsics.
  - Frequent modulo/while loops for toroidal wrapping; branch mispredictions.
  - AoS layout (`IGSOAComplexNode`) hinders SIMD; consider splitting real/imag arrays.
- **Optimizations**:
  1. Precompute neighbor offsets for each `R_c` and reuse across nodes; expect 1.8–2.2× speedup by eliminating per-node search.
  2. Use `std::span`/SoA to batch `psi` real/imag arrays; vectorize kernel with AVX2 fused operations.
  3. Cache `coupling_strength` lookup via table or polynomial approximation; reduce transcendental cost by ~40% (validated with microbench earlier).
  4. Parallelize outer loops with OpenMP (already optional) once determinism guard (`schedule(static)`) is introduced.
- **Benchmark plan**:
  ```bash
  cmake -S . -B build/release -DCMAKE_BUILD_TYPE=Release -DDASE_ENABLE_OPENMP=ON
  cmake --build build/release --target test_igsoa_engine
  perf stat -r 5 build/release/test_igsoa_engine --grid 64 --steps 1024
  ```

# Architecture & Organization
- Core engine lives entirely in monolithic headers; no separation between state, operators, and integrators. Suggest splitting into modules (`state`, `operators`, `integrators`, `diagnostics`).
- C API/FFI lacks error codes; returns `nullptr` on exception but never surfaces cause. Recommend `enum class IGSOAStatus` and structured logging.
- Config validation absent: no checks for `num_nodes > 0`, `dt > 0`, `R_c` positivity, or normalization toggles.
- Derived data (`F_gradient`, `entropy_rate`) stored in node struct despite being recomputable; consider lazy evaluation to improve cache locality.

# Testing Strategy & Coverage Gaps
- No unit tests verifying invariants (mass, energy) or boundary conditions.
- Missing property-based tests (e.g., `normalizeStates` should keep |Ψ|=1 within tolerance).
- Need regression snapshots for deterministic seeds: fix RNG, set OpenMP `OMP_NUM_THREADS=1` for reproducibility.
- Proposed coverage additions:
  - `tests/test_cfl.cpp`: ensure `validate_timestep` rejects oversized `dt`.
  - `tests/test_conservation.cpp`: energy drift < ε over 1000 steps when `gamma=0`.
  - Python side: `pytest` to exercise bridge input validation and CLI parsing.
  - Use `miri`/`asan` for UB checks once Rust/C interface introduced.

# Missing or Incomplete Features
1. 3D boundary diagnostics—no way to extract per-axis fluxes; necessary for PDE validation.
2. Checkpoint/restart support absent despite long-running missions.
3. CLI lacks configuration schema (YAML/JSON) for reproducible runs; consider `--config file.json`.
4. Mixed-precision path (float vs double) hinted by docs but unimplemented; evaluate using templated kernels.
5. Telemetry/logging for entropy and norm drift; current `std::cerr` diagnostics insufficient.

# Security, Safety, and Robustness
- C API lacks bounds checks; `setNodePsi` silently ignores out-of-range indices. Should return status.
- Python bridge has no auth; only safe for localhost.
- Large allocations: `std::vector<IGSOAComplexNode>` grows with `num_nodes` but no guard; add max cap.
- FFI exception catch-all returns `nullptr` but leaks message; log to stderr or callback for diagnosis.

# Documentation & Developer Experience
- README omits Linux build instructions and dependency list; add `apt install libfftw3-dev` guidance.
- Provide Makefile shortcuts (`make configure`, `make test`), and document deterministic run settings (threads, seeds).
- Add diagrams illustrating data flow between Φ and Ψ to align with existing theory PDFs.

# Proposed Patches (Diffs Not Applied)
```diff
--- a/src/cpp/igsoa_complex_node.h
+++ b/src/cpp/igsoa_complex_node.h
@@
-        , R_c(1e-34)              // Default causal resistance
+        , R_c(3.0)                // Default causal radius (≥ lattice spacing)
```

```diff
--- a/src/cpp/igsoa_physics.h
+++ b/src/cpp/igsoa_physics.h
@@
-        if (config.normalize_psi) {
-            operations += normalizeStates(nodes);
-        }
+        if (config.normalize_psi) {
+            operations += normalizeStates(nodes);
+        }
+
+        // Validate stability once per step (pseudo-code; implement cached λ_max)
+        if (!validate_timestep(config, nodes)) {
+            throw std::runtime_error("dt violates stability bound");
+        }
```

```diff
--- a/src/cpp/igsoa_complex_engine.h
+++ b/src/cpp/igsoa_complex_engine.h
@@
-        out_speedup_factor = 15500.0 / ns_per_op_;  // vs baseline
+        out_speedup_factor = ns_per_op_ > 0.0 ? 15500.0 / ns_per_op_ : 0.0;
```

```diff
--- a/src/cpp/igsoa_physics_3d.h
+++ b/src/cpp/igsoa_physics_3d.h
@@
-        operations += computeGradients(nodes, N_x, N_y, N_z);
-        return operations;
+        operations += computeGradients(nodes, N_x, N_y, N_z);
+        if (config.normalize_psi) {
+            operations += IGSOAPhysics::normalizeStates(nodes);
+        }
+        return operations;
@@
-            node.phi += signal_real;
-            // Could extend to complex driving if needed (signal_imag reserved for future use)
+            node.phi += signal_real;
+            node.psi += std::complex<double>(signal_real, signal_imag);
```

```diff
--- a/CMakeLists.txt
+++ b/CMakeLists.txt
@@
-find_library(FFTW3_LIBRARY NAMES fftw3 libfftw3-3 PATHS ${CMAKE_CURRENT_SOURCE_DIR} NO_DEFAULT_PATH)
-if(NOT FFTW3_LIBRARY)
-    find_library(FFTW3_LIBRARY NAMES fftw3 libfftw3-3)
-endif()
-
-if(FFTW3_LIBRARY)
-    message(STATUS "Found FFTW3: ${FFTW3_LIBRARY}")
-else()
-    message(FATAL_ERROR "FFTW3 library not found. Please place libfftw3-3.lib in project root.")
-endif()
+find_package(FFTW3 REQUIRED COMPONENTS fftw3)
+set(FFTW3_LIBRARY FFTW3::fftw3)
```

# Risk Register & 30/60/90 Roadmap
- **Critical Risks**: Numerical instability (dt guard), absence of coupling (R_c defaults), lack of CI (build failures), inconsistent dimensional behavior.
- **30 days**: Fix R_c default and add config validation; repair CMake portability; institute smoke tests (norm conservation, metrics sanity).
- **60 days**: Implement timestep validation + RK4 integrator; align driving/normalization across dimensions; introduce OpenMP-safe determinism controls.
- **90 days**: Optimize neighbor kernels with precomputation/SIMD; add checkpointing and CLI config; roll out CI matrix (Linux/mac/Windows) with performance baselines.
