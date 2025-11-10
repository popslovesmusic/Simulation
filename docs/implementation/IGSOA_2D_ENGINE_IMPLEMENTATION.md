# IGSOA 2D Engine Implementation

**Status**: Core implementation complete, integration pending
**Date**: November 3, 2025
**Version**: 1.0

---

## Executive Summary

This document describes the 2D extension of the IGSOA (Informational Geometry Self-Organizing Automaton) engine, implementing SATP (Scalar Affine Toroid Physics) on a two-dimensional toroidal lattice.

**Key Achievement**: Complete 2D physics engine with circular non-local coupling, ready for CLI integration.

---

## Implementation Overview

### Files Created

1. **`src/cpp/igsoa_complex_engine_2d.h`** (318 lines)
   - 2D engine class
   - N_x × N_y toroidal lattice
   - Row-major memory layout
   - 2D coordinate system

2. **`src/cpp/igsoa_physics_2d.h`** (393 lines)
   - 2D physics evolution
   - Circular coupling region (R_c radius)
   - 2D Euclidean distance metric with wrapping
   - 2D gradient computation

3. **`src/cpp/igsoa_state_init_2d.h`** (323 lines)
   - 2D Gaussian initialization (elliptical and circular)
   - 2D plane wave initialization
   - Center of mass computation for 2D
   - Support for overwrite/add/blend modes

4. **`src/cpp/igsoa_capi_2d.h`** (195 lines)
   - C API interface for 2D engine
   - Compatible with CLI/Python bindings

5. **`src/cpp/igsoa_capi_2d.cpp`** (229 lines)
   - C API implementation
   - Engine lifecycle management

**Total**: ~1,460 lines of clean, documented C++ code

---

## Architecture

### 2D Lattice Topology

```
Toroidal Lattice (N_x × N_y):

    0   1   2  ...  N_x-1
  ┌───┬───┬───┬───┬───┐
0 │   │   │   │   │   │←→ wraps to 0
  ├───┼───┼───┼───┼───┤
1 │   │   │   │   │   │
  ├───┼───┼───┼───┼───┤
2 │   │ ● │   │   │   │  ● = sample node at (1, 2)
  ├───┼───┼───┼───┼───┤
  ⋮   ⋮   ⋮   ⋮   ⋮   ⋮
  └───┴───┴───┴───┴───┘
  ↑
  wraps to 0

Periodic boundaries in BOTH x and y directions.
```

**Memory Layout**: Row-major order
```
Index(x, y) = y * N_x + x

Sequential access pattern:
(0,0), (1,0), (2,0), ..., (N_x-1, 0),
(0,1), (1,1), (2,1), ..., (N_x-1, 1),
...
```

**Benefits**:
- Cache-friendly sequential access when iterating rows
- Compatible with standard 2D array indexing
- Efficient for AVX2 vectorization (future work)

---

### Non-Local Coupling: 2D Extension

#### 1D vs 2D Coupling

| Aspect | 1D | 2D |
|--------|----|----|
| **Distance metric** | `d = |i - j|` with wrapping | `d = sqrt(dx² + dy²)` with 2D wrapping |
| **Coupling region** | Linear segment `[-R_c, +R_c]` | Circular disk of radius R_c |
| **Neighbor count** | O(R_c) | O(πR_c²) |
| **Complexity per step** | O(N × R_c) | O(N × R_c²) |

#### 2D Distance Calculation

```cpp
// Wrapped distance in each dimension
double dx = wrappedDistance1D(x1, x2, N_x);
double dy = wrappedDistance1D(y1, y2, N_y);

// Euclidean distance
double distance = sqrt(dx² + dy²);

// Only couple if within R_c
if (distance <= R_c) {
    double K = exp(-distance / R_c) / R_c;  // Coupling kernel
    coupling += K * (psi_neighbor - psi_self);
}
```

#### Circular Coupling Region

For a node at (x₀, y₀) with R_c = 3:

```
     -3  -2  -1   0  +1  +2  +3
  -3  ·   ·   ○   ○   ○   ·   ·
  -2  ·   ○   ○   ○   ○   ○   ·
  -1  ○   ○   ○   ○   ○   ○   ○
   0  ○   ○   ○   ●   ○   ○   ○    ● = center node
  +1  ○   ○   ○   ○   ○   ○   ○
  +2  ·   ○   ○   ○   ○   ○   ·
  +3  ·   ·   ○   ○   ○   ·   ·

○ = coupled neighbor (distance ≤ R_c)
· = not coupled (distance > R_c)

Number of coupled neighbors ≈ π × R_c² ≈ 28 for R_c=3
```

---

### Physics Equations (Unchanged from 1D)

The 2D extension preserves the same IGSOA evolution equations:

**Quantum State Evolution**:
```
iℏ ∂Ψ/∂t = Ĥ_eff Ψ

where Ĥ_eff = -𝒦[Ψ] + κΦ + iγ

𝒦[Ψ] = ∑_{j: |r_j - r_i| ≤ R_c} K(|r_j - r_i|, R_c) (Ψ_j - Ψ_i)

K(r, R_c) = exp(-r/R_c) / R_c
```

**Realized Field Evolution**:
```
∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
```

**Key Point**: Only the **spatial coupling** 𝒦[Ψ] changes from 1D to 2D. The rest of the physics is dimension-agnostic.

---

## API Reference

### Engine Creation

```cpp
IGSOA2DEngineHandle handle = igsoa2d_create_engine(
    N_x,           // Width (e.g., 128)
    N_y,           // Height (e.g., 128)
    R_c,           // Causal radius (e.g., 1.0)
    kappa,         // Coupling strength (e.g., 1.0)
    gamma,         // Dissipation (e.g., 0.1)
    dt             // Time step (e.g., 0.01)
);
```

### State Initialization

#### Circular Gaussian

```cpp
igsoa2d_init_circular_gaussian(
    handle,
    100.0,         // amplitude
    64.0,          // center_x
    64.0,          // center_y
    16.0,          // sigma (isotropic)
    0.0,           // baseline_phi
    "blend",       // mode
    1.0            // beta
);
```

#### Elliptical Gaussian

```cpp
igsoa2d_init_gaussian(
    handle,
    100.0,         // amplitude
    64.0,          // center_x
    64.0,          // center_y
    20.0,          // sigma_x
    10.0,          // sigma_y (ellipse)
    0.0,           // baseline_phi
    "overwrite",   // mode
    1.0            // beta
);
```

### Time Evolution

```cpp
// Run 10 timesteps
igsoa2d_run_mission(handle, 10);
```

### State Extraction

```cpp
size_t N_total = igsoa2d_get_total_nodes(handle);  // N_x * N_y

double* psi_real = new double[N_total];
double* psi_imag = new double[N_total];
double* phi = new double[N_total];

igsoa2d_get_all_states(handle, psi_real, psi_imag, phi);

// Access node (x, y): index = y * N_x + x
double value_at_32_16 = psi_real[16 * N_x + 32];
```

### Center of Mass (2D Drift Measurement)

```cpp
double x_cm, y_cm;
igsoa2d_compute_center_of_mass(handle, &x_cm, &y_cm);

// Expected for zero drift: (x_cm, y_cm) ≈ (center_x, center_y)
```

---

## SATP Predictions in 2D

### Prediction 1: Zero Translational Drift (2D)

**Claim**: Gaussian packets do NOT drift in ANY direction.

**Test**:
1. Initialize 2D Gaussian at center (N_x/2, N_y/2)
2. Evolve for T timesteps
3. Measure center of mass: (x_cm, y_cm)
4. Expected drift: ||(x_cm, y_cm) - (N_x/2, N_y/2)|| < 1% × √(N_x² + N_y²)

**Status**: Awaiting validation (integration incomplete)

### Prediction 2: Isotropic Correlation Length

**Claim**: ξ ≈ R_c in ALL directions for isotropic initial conditions.

**Test**:
1. Compute 2D autocorrelation function C(Δx, Δy)
2. Extract decay length in x-direction: ξ_x
3. Extract decay length in y-direction: ξ_y
4. Expected: ξ_x ≈ ξ_y ≈ R_c

**Status**: Requires 2D analysis tool (not yet implemented)

### Prediction 3: Circular Spectral Cutoff

**Claim**: Power spectrum decays at |k| ≈ 1/R_c in Fourier space.

**Test**:
1. Compute 2D FFT: Ψ̂(k_x, k_y)
2. Compute radial power spectrum: P(|k|) where |k| = √(k_x² + k_y²)
3. Identify cutoff wavenumber k₀
4. Expected: k₀ ≈ 1/R_c (isotropic cutoff)

**Status**: Requires 2D FFT analysis (not yet implemented)

---

## Performance Characteristics

### Computational Complexity

**Per timestep**:
- **1D**: O(N × R_c)
- **2D**: O(N_x × N_y × π × R_c²)

**Example** (N=128×128, R_c=5):
- Total nodes: 16,384
- Neighbors per node: ~79 (π × 5²)
- Operations per step: ~1.3 million

**Scaling**:
- Memory: O(N_x × N_y) ← Linear in total nodes
- Time: O(N_x × N_y × R_c²) ← Quadratic in R_c

### Optimization Opportunities

1. **Spatial hashing**: Pre-compute neighbor lists for static R_c
2. **AVX2 vectorization**: Process 4 neighbors simultaneously
3. **Sparse coupling**: Skip far-away nodes early
4. **GPU acceleration**: Embarrassingly parallel over nodes

**Expected speedup**: 5-10× with AVX2, 50-100× with GPU

---

## Differences from 1D

| Feature | 1D | 2D |
|---------|----|----|
| **Lattice** | Ring (N nodes) | Torus (N_x × N_y) |
| **Distance** | Linear wrapped | Euclidean 2D wrapped |
| **Coupling** | Segment [-R_c, +R_c] | Circle (radius R_c) |
| **Neighbor count** | 2R_c | πR_c² |
| **Gradient** | 1D finite diff | 2D central diff (∇ = (∂/∂x, ∂/∂y)) |
| **Initialization** | 1D Gaussian | 2D circular/elliptical Gaussian |
| **Drift measurement** | Scalar x_cm | Vector (x_cm, y_cm) |
| **Correlation** | C(Δx) | C(Δx, Δy) or C(r) radially |

**Physics**: Identical evolution equations, only spatial geometry changes.

---

## Integration Status

### ✅ Completed

- [x] 2D engine core (`IGSOAComplexEngine2D`)
- [x] 2D physics evolution (`IGSOAPhysics2D`)
- [x] 2D state initialization (Gaussian, plane wave, uniform, random)
- [x] C API for 2D engine
- [x] Center of mass computation (2D drift measurement)

### ⏳ Pending

- [x] **CLI integration**: Add `igsoa_2d` engine type to command router
- [x] **Engine manager**: Register 2D engine in `createEngine()`
- [x] **Build system**: Add 2D source files to compilation *(header-only integration; no additional sources required)*
- [x] **Test suite**: 2D zero-drift validation *(see `tests/test_igsoa_2d.cpp`)*
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
- [x] **Python analysis**: 2D visualization, FFT, correlation *(initial visualization + drift tooling via `tools/analyze_igsoa_2d.py`; FFT pending future work)*
=======
- [x] **Python analysis**: 2D visualization, FFT, correlation *(`tools/analyze_igsoa_2d.py` now exports density heatmaps, FFT spectra, and autocorrelation diagnostics)*
>>>>>>> theirs
=======
- [x] **Python analysis**: 2D visualization, FFT, correlation *(`tools/analyze_igsoa_2d.py` now exports density heatmaps, FFT spectra, and autocorrelation diagnostics)*
>>>>>>> theirs
=======
- [x] **Python analysis**: 2D visualization, FFT, correlation *(`tools/analyze_igsoa_2d.py` now exports density heatmaps, FFT spectra, and autocorrelation diagnostics)*
>>>>>>> theirs
=======
- [x] **Python analysis**: 2D visualization, FFT, correlation *(`tools/analyze_igsoa_2d.py` now exports density heatmaps, FFT spectra, and autocorrelation diagnostics)*
>>>>>>> theirs

### 🔮 Future (3D Extension)

- [ ] `IGSOAComplexEngine3D` (N_x × N_y × N_z)
- [ ] Spherical coupling region in 3D
- [ ] 3D Gaussian initialization
- [ ] 3D visualization tools

---

## Next Steps

### Immediate (to complete 2D)

1. ✅ **Engine lifecycle** – `EngineManager::createEngine` accepts `igsoa_complex_2d`
   with explicit `N_x`, `N_y`, and full physics parameters (`R_c`, `kappa`,
   `gamma`, `dt`).  Lifecycle helpers (`destroyEngine`, `runMission`,
   `getMetrics`, state extraction) now dispatch to the 2D engine.
2. ✅ **Command router** – `create_engine`, `set_igsoa_state`, `get_state`, and
   `get_metrics` return lattice metadata for 2D engines.  A dedicated
   `get_center_of_mass` command exposes drift measurement straight from the CLI.
3. ✅ **State initialization** – The router forwards 2D Gaussian, circular
   Gaussian, plane-wave, uniform, random, and reset profiles to
   `IGSOAStateInit2D` (blend/add/overwrite modes supported).
4. ✅ **Validation** – `tests/test_igsoa_2d.cpp` executes an 8-step evolution and
   fails if the informational center of mass drifts by more than 0.5 lattice
   units.
5. ✅ **Analysis tooling** – `tools/analyze_igsoa_2d.py` reshapes CLI dumps,
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
   computes drift metrics, and optionally renders a heatmap (matplotlib if
   available).  FFT/correlation are earmarked for a future enhancement.
=======
   computes drift metrics, renders informational density heatmaps, and (with
   NumPy) exports FFT spectra plus 2D autocorrelation summaries/heatmaps.
>>>>>>> theirs
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
   computes drift metrics, renders informational density heatmaps, and (with
   NumPy) exports FFT spectra plus 2D autocorrelation summaries/heatmaps.

### Operational Verification & Tooling

The following smoke checks validate that the 2D stack builds, runs, and emits
state dumps that downstream tooling can ingest:

1. **Compile and run the drift regression test**

   ```bash
   mkdir -p build/tests
   g++ -std=c++17 -O2 -I src/cpp tests/test_igsoa_2d.cpp -o build/tests/test_igsoa_2d
   ./build/tests/test_igsoa_2d
   ```

   The executable prints the initial/final centers of mass and terminates with a
   non-zero status if the drift exceeds the 0.5 lattice-unit guard band.

2. **Generate a JSON snapshot and analyze it**

   ```bash
   python tools/analyze_igsoa_2d.py --state-json build/tests/sample_state.json \
       --expect-center 16 16
   ```

   Replace `build/tests/sample_state.json` with a `get_state` dump captured from
   the CLI (or the synthetic Gaussian snapshot generated during regression
   testing).  `tools/analyze_igsoa_2d.py` reports lattice dimensions, density
   statistics, and center-of-mass drift.  When NumPy (and optionally
   matplotlib) is installed you can add `--fft-json`, `--fft-heatmap`, and
   `--autocorr-heatmap` to export spectral diagnostics; without NumPy those
   flags exit early with an explanatory message so the baseline metrics remain
   usable.
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs

---

## Example Usage (When Integrated)

### Create 2D Engine and Run Simulation

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex_2d","N_x":128,"N_y":128,"R_c":1.0,"kappa":1.0,"gamma":0.1,"dt":0.01}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian_2d","amplitude":100.0,"center_x":64.0,"center_y":64.0,"sigma_x":16.0,"sigma_y":16.0,"baseline_phi":0.0,"mode":"blend","beta":1.0}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":10,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"get_center_of_mass","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
```

### Expected Output

```json
{
  "command": "get_state",
  "status": "success",
  "result": {
    "num_nodes": 16384,
    "engine_type": "igsoa_complex_2d",
    "dimensions": {"N_x": 128, "N_y": 128},
    "psi_real": [...],  // 16384 values (row-major)
    "psi_imag": [...],
    "phi": [...]
  }
}
```

### Python Analysis

```python
import numpy as np
import matplotlib.pyplot as plt
import json

# Load state
with open('output_2d.json') as f:
    data = json.load(f)

psi_real = np.array(data['result']['psi_real'])
psi_imag = np.array(data['result']['psi_imag'])

# Reshape to 2D
N_x = N_y = 128
psi_real_2d = psi_real.reshape(N_y, N_x)
psi_imag_2d = psi_imag.reshape(N_y, N_x)

# Compute |Ψ|²
F = psi_real_2d**2 + psi_imag_2d**2

# Visualize
plt.figure(figsize=(10, 8))
plt.imshow(F, cmap='hot', origin='lower')
plt.colorbar(label='|Ψ|²')
plt.title('2D Informational Density')
plt.xlabel('x')
plt.ylabel('y')
plt.savefig('igsoa_2d_heatmap.png', dpi=150)

# Measure center of mass
y_indices, x_indices = np.meshgrid(np.arange(N_y), np.arange(N_x), indexing='ij')
total_F = np.sum(F)
x_cm = np.sum(x_indices * F) / total_F
y_cm = np.sum(y_indices * F) / total_F

print(f"Center of mass: ({x_cm:.2f}, {y_cm:.2f})")
print(f"Expected: (64.00, 64.00)")
print(f"Drift: {np.sqrt((x_cm - 64)**2 + (y_cm - 64)**2):.4f} nodes")
```

---

## Summary

**Status**: 2D engine core **complete and ready for integration**.

**Deliverables**:
- 5 new C++ files (~1,460 LOC)
- Full 2D physics implementation
- Circular non-local coupling
- 2D state initialization (Gaussian, plane wave, etc.)
- C API for external interfacing

**Remaining Work** (to make it usable):
1. CLI integration (engine_manager, command_router)
2. Build system updates
3. Python analysis tools (visualization, FFT, correlation)
4. Validation tests (2D zero drift, isotropic ξ)

**Estimated Completion**: ~4-6 hours of development + testing

**Token Budget Remaining**: ~138,600 / 200,000 (69%)

---

**Ready to proceed with 3D or complete 2D integration first?**

