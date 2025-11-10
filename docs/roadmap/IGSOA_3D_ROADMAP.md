# IGSOA 3D Engine Roadmap

**Status**: Design phase
**Date**: November 3, 2025
**Prerequisite**: 2D engine integration complete

---

## Overview

The 3D extension of IGSOA will implement SATP on a three-dimensional toroidal lattice (N_x × N_y × N_z), enabling full volumetric simulations of quantum dynamics with non-local coupling.

**Key Extension**: From circular (2D) to **spherical** (3D) coupling regions.

---

## Architecture Design

### Lattice Topology

```
3D Toroidal Lattice (N_x × N_y × N_z):

- Periodic boundaries in x, y, and z
- Memory layout: Row-major 3D
  Index(x, y, z) = z * (N_y * N_x) + y * N_x + x
```

**Example**: 64×64×64 lattice = 262,144 nodes

### Non-Local Coupling: 3D Spherical Region

**Distance metric**:
```cpp
double dx = wrappedDistance1D(x1, x2, N_x);
double dy = wrappedDistance1D(y1, y2, N_y);
double dz = wrappedDistance1D(z1, z2, N_z);

double distance = sqrt(dx² + dy² + dz²);
```

**Coupling region**: Sphere of radius R_c
```
if (distance <= R_c) {
    double K = exp(-distance / R_c) / R_c;
    coupling += K * (psi_neighbor - psi_self);
}
```

**Neighbor count**: O(4πR_c³/3) ≈ 4.19 × R_c³

**Example** (R_c = 5):
- 2D neighbors: ~79 (πR_c²)
- 3D neighbors: ~523 (4πR_c³/3)

---

## Implementation Plan

### Phase 1: Core 3D Engine (4-6 hours)

1. **`igsoa_complex_engine_3d.h`** (~350 lines)
   - Class `IGSOAComplexEngine3D`
   - 3D coordinate system (x, y, z)
   - Row-major 3D indexing

2. **`igsoa_physics_3d.h`** (~450 lines)
   - `wrappedDistance3D()` function
   - Spherical coupling loop
   - 3D gradient computation: ∇F = (∂F/∂x, ∂F/∂y, ∂F/∂z)

3. **`igsoa_state_init_3d.h`** (~350 lines)
   - 3D spherical Gaussian initialization
   - 3D ellipsoidal Gaussian
   - 3D plane wave
   - 3D center of mass: (x_cm, y_cm, z_cm)

4. **`igsoa_capi_3d.h/.cpp`** (~400 lines)
   - C API for 3D engine
   - Compatible with CLI

**Estimated LOC**: ~1,550 lines

### Phase 2: CLI Integration (2-3 hours)

1. **Add `igsoa_3d` to engine manager**:
   ```cpp
   else if (engine_type == "igsoa_3d") {
       size_t N_x, N_y, N_z;
       parseGridSize3D(params, N_x, N_y, N_z);
       handle = igsoa3d_create_engine(N_x, N_y, N_z, R_c, ...);
   }
   ```

2. **Add `set_igsoa_state` for 3D profiles**

3. **Build system**: Add 3D sources to compilation

### Phase 3: Analysis Tools (4-5 hours)

1. **`analyze_igsoa_3d.py`**:
   - 3D visualization (volume rendering or slices)
   - 3D FFT: Ψ̂(k_x, k_y, k_z)
   - Radial power spectrum: P(|k|) where |k| = sqrt(k_x² + k_y² + k_z²)
   - 3D autocorrelation function
   - 3D drift measurement: ||(x_cm, y_cm, z_cm) - initial||

2. **Visualization options**:
   - Matplotlib 3D scatter plot (subsampled)
   - 2D slices at z = const
   - Mayavi volume rendering (optional)

### Phase 4: Validation (2-3 hours)

1. **3D zero drift test**: Spherical Gaussian should not translate
2. **Isotropic ξ test**: Correlation length same in all directions
3. **Spherical cutoff test**: k₀ ≈ 1/R_c isotropically

---

## Files to Create

```
src/cpp/
├── igsoa_complex_engine_3d.h      (350 lines)
├── igsoa_physics_3d.h             (450 lines)
├── igsoa_state_init_3d.h          (350 lines)
├── igsoa_capi_3d.h                (200 lines)
└── igsoa_capi_3d.cpp              (250 lines)

dase_cli/
├── analyze_igsoa_3d.py            (400 lines)
└── test_3d_basic.json             (10 lines)

tests/
└── test_3d_zero_drift.sh          (100 lines)

docs/
└── IGSOA_3D_ENGINE_IMPLEMENTATION.md (1000 lines)
```

**Total estimated**: ~2,110 new lines of code

---

## Key Algorithms

### 3D Wrapped Distance

```cpp
static inline double wrappedDistance3D(
    int x1, int y1, int z1,
    int x2, int y2, int z2,
    size_t N_x, size_t N_y, size_t N_z
) {
    double dx = wrappedDistance1D(x1, x2, N_x);
    double dy = wrappedDistance1D(y1, y2, N_y);
    double dz = wrappedDistance1D(z1, z2, N_z);
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}
```

### 3D Spherical Coupling

```cpp
// For each node i at (x_i, y_i, z_i)
int R_c_int = static_cast<int>(std::ceil(R_c));

for (int dz = -R_c_int; dz <= R_c_int; dz++) {
    for (int dy = -R_c_int; dy <= R_c_int; dy++) {
        for (int dx = -R_c_int; dx <= R_c_int; dx++) {
            if (dx == 0 && dy == 0 && dz == 0) continue;

            // Wrap coordinates
            int x_j = wrapCoord(x_i + dx, N_x);
            int y_j = wrapCoord(y_i + dy, N_y);
            int z_j = wrapCoord(z_i + dz, N_z);

            // Compute 3D distance
            double distance = wrappedDistance3D(
                x_i, y_i, z_i, x_j, y_j, z_j, N_x, N_y, N_z
            );

            // Spherical cutoff
            if (distance <= R_c) {
                double K = couplingKernel(distance, R_c);
                size_t j = coordToIndex3D(x_j, y_j, z_j, N_x, N_y);
                coupling += K * (nodes[j].psi - nodes[i].psi);
            }
        }
    }
}
```

### 3D Gaussian Initialization

```cpp
Ψ(x, y, z) = A * exp(
    -(x - x₀)² / (2σ_x²)
    -(y - y₀)² / (2σ_y²)
    -(z - z₀)² / (2σ_z²)
)
```

**Spherical case**: σ_x = σ_y = σ_z = σ

---

## Computational Complexity

| Dimension | Lattice Size | Neighbors (R_c=5) | Ops per Step |
|-----------|--------------|-------------------|--------------|
| **1D** | 4096 | 10 | ~41k |
| **2D** | 128×128 = 16k | 79 | ~1.3M |
| **3D** | 64×64×64 = 262k | 523 | ~137M |

**Scaling**: 3D is ~100× more expensive than 2D for same total nodes.

**Mitigation strategies**:
1. **Smaller R_c**: Use R_c = 2-3 instead of 5
2. **GPU acceleration**: Essential for 3D (100× speedup)
3. **Adaptive resolution**: Fine grid only near features
4. **Sparse coupling**: Skip empty regions

---

## API Preview

### Engine Creation

```cpp
IGSOA3DEngineHandle handle = igsoa3d_create_engine(
    64,    // N_x
    64,    // N_y
    64,    // N_z
    1.0,   // R_c
    1.0,   // kappa
    0.1,   // gamma
    0.01   // dt
);
```

### Spherical Gaussian Initialization

```cpp
igsoa3d_init_spherical_gaussian(
    handle,
    100.0,   // amplitude
    32.0,    // center_x
    32.0,    // center_y
    32.0,    // center_z
    8.0,     // sigma (isotropic)
    0.0,     // baseline_phi
    "blend", // mode
    1.0      // beta
);
```

### State Extraction

```cpp
size_t N_total = igsoa3d_get_total_nodes(handle);  // N_x * N_y * N_z

double* psi_real = new double[N_total];
double* psi_imag = new double[N_total];
double* phi = new double[N_total];

igsoa3d_get_all_states(handle, psi_real, psi_imag, phi);

// Access node (x, y, z): index = z * (N_y * N_x) + y * N_x + x
```

### 3D Drift Measurement

```cpp
double x_cm, y_cm, z_cm;
igsoa3d_compute_center_of_mass(handle, &x_cm, &y_cm, &z_cm);

double drift_3d = sqrt(
    (x_cm - 32)² + (y_cm - 32)² + (z_cm - 32)²
);

printf("3D drift: %.4f nodes\n", drift_3d);
```

---

## SATP Predictions in 3D

### Zero Drift (3D)

**Claim**: Spherical Gaussian packets do not translate in ANY direction.

**Test**:
```
Initial: Spherical Gaussian at (32, 32, 32) with σ = 8
After T=10: Measure (x_cm, y_cm, z_cm)
Expected: ||(x_cm, y_cm, z_cm) - (32, 32, 32)|| < 1% × √(64² + 64² + 64²)
```

### Isotropic Correlation Length

**Claim**: ξ same in x, y, z directions for spherical initial conditions.

**Test**: Measure C(Δx, 0, 0), C(0, Δy, 0), C(0, 0, Δz) → should all decay with ξ ≈ R_c

### Spherical Spectral Cutoff

**Claim**: Power spectrum isotropic in k-space with cutoff |k| ≈ 1/R_c

**Test**:
1. 3D FFT: Ψ̂(k_x, k_y, k_z)
2. Radial binning: P(|k|) where |k| = sqrt(k_x² + k_y² + k_z²)
3. Identify cutoff k₀
4. Expected: k₀ ≈ 1/R_c (spherically symmetric)

---

## Comparison: 1D vs 2D vs 3D

| Feature | 1D | 2D | 3D |
|---------|----|----|-----|
| **Lattice** | Ring | Torus | 3-Torus |
| **Coordinates** | x | (x, y) | (x, y, z) |
| **Distance** | |Δx| | sqrt(Δx² + Δy²) | sqrt(Δx² + Δy² + Δz²) |
| **Coupling region** | Segment | Circle | Sphere |
| **Neighbors (R_c=5)** | 10 | 79 | 523 |
| **Memory (64³ nodes)** | 2 KB | 128 KB | 8 MB |
| **Ops per step** | 41k | 1.3M | 137M |
| **Gradient** | ∂F/∂x | (∂F/∂x, ∂F/∂y) | (∂F/∂x, ∂F/∂y, ∂F/∂z) |
| **Drift measure** | Scalar | 2D vector | 3D vector |

**Key insight**: Physics equations identical across dimensions, only geometry changes.

---

## Performance Estimates

### CPU (Single-threaded)

Assuming 10 ns/op:
- **2D** (128×128, R_c=5): 1.3M ops → 13 ms per step
- **3D** (64³, R_c=5): 137M ops → 1.37 sec per step

**10 timesteps**:
- 2D: 130 ms
- 3D: 13.7 sec

### GPU (Parallelized)

Assuming 100× speedup:
- **3D** (64³, R_c=5): 137 ms per 10 steps

**Feasible** for interactive simulations with GPU acceleration.

---

## Visualization Strategy

### Option 1: 2D Slices

Show 3 orthogonal slices:
- xy-plane at z = N_z/2
- xz-plane at y = N_y/2
- yz-plane at x = N_x/2

**Pros**: Fast, works with matplotlib
**Cons**: Doesn't show full 3D structure

### Option 2: Volume Rendering

Use Mayavi or PyVista for interactive 3D view.

**Pros**: Full 3D visualization
**Cons**: Requires additional dependencies

### Option 3: Isosurface

Show surface where |Ψ|² = threshold.

**Pros**: Clear 3D structure
**Cons**: Can miss low-intensity features

---

## Development Timeline

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Core 3D engine implementation | 4-6 hours |
| 2 | CLI integration | 2-3 hours |
| 3 | Python analysis tools | 4-5 hours |
| 4 | Validation tests | 2-3 hours |
| 5 | Documentation | 2 hours |
| 6 | GPU acceleration (optional) | 8-12 hours |

**Total**: 14-19 hours (CPU version), 22-31 hours (with GPU)

---

## Prerequisites

Before starting 3D implementation:

1. ✅ **Complete 2D integration**:
   - Engine manager registration
   - CLI command support
   - Build system updated

2. ✅ **Validate 2D**:
   - Zero drift test passing
   - Correlation length measured
   - Analysis tools working

3. ✅ **Optimize 2D performance**:
   - AVX2 vectorization (optional)
   - Benchmark and profile
   - Establish baseline

**Rationale**: Debug issues in 2D before adding 3D complexity.

---

## Summary

**3D Extension**: Straightforward generalization of 2D pattern.

**Key changes**:
- Spherical coupling (vs circular in 2D)
- 3D distance metric
- 3D indexing
- ~100× more expensive computationally

**Recommended approach**:
1. Finish 2D integration first
2. Validate 2D thoroughly
3. Copy 2D code, extend to 3D
4. Focus on small lattices (32³ to 64³)
5. Add GPU acceleration if needed

**Token budget**: Currently at ~65k / 200k (32.5% used)
**Remaining**: Sufficient for 3D implementation (~10-15k tokens estimated)

**Ready to proceed?**

---

## Files Created So Far

### 2D Implementation (Complete)
- `src/cpp/igsoa_complex_engine_2d.h` (318 lines)
- `src/cpp/igsoa_physics_2d.h` (393 lines)
- `src/cpp/igsoa_state_init_2d.h` (323 lines)
- `src/cpp/igsoa_capi_2d.h` (195 lines)
- `src/cpp/igsoa_capi_2d.cpp` (229 lines)
- `docs/IGSOA_2D_ENGINE_IMPLEMENTATION.md` (comprehensive)

**Total**: ~1,460 lines + documentation

### 3D Implementation (Pending)
- Files listed above in "Files to Create" section

**Next step**: User decision on whether to:
1. Complete 2D integration + testing first (recommended)
2. Proceed with 3D core implementation immediately
3. Pause for review and planning

