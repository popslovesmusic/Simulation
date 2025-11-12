# DASE/IGSOA Cache System

**Purpose:** High-performance computational cache for reusing expensive calculations across missions.

**Expected Speedup:** 50-80% for repeated missions, 10-30% for FFT operations.

---

## Directory Structure

```
cache/
├── fractional_kernels/    # Caputo/SOE fractional derivative coefficients
├── stencils/              # Laplacian finite-difference matrices
├── fftw_wisdom/           # Optimized FFT plans
├── echo_templates/        # Prime-gap echo schedules (IGSOA GW)
├── state_profiles/        # Pre-computed initial states
├── source_maps/           # Spatial masks for multi-zone sources
├── mission_graph/         # DAG-level intermediate results
└── surrogates/            # Trained ML surrogate models
    ├── models/            # .pt PyTorch model files
    └── metadata/          # Model training metadata
```

---

## Usage

### Python API

```python
from backend.cache import CacheManager

# Initialize cache manager
cache = CacheManager(root="./cache")

# Save data
import numpy as np
kernel = np.random.rand(1000)
cache.save("fractional_kernels", "kernel_1.5_0.01_1000", kernel)

# Load data
loaded = cache.load("fractional_kernels", "kernel_1.5_0.01_1000")

# Check existence
if cache.exists("stencils", "laplacian_2d_64_64"):
    stencil = cache.load("stencils", "laplacian_2d_64_64")

# Get statistics
stats = cache.get_stats()
print(f"Total cache size: {stats['total_size_mb']:.1f} MB")

# Clear category
cache.clear_category("mission_graph")
```

### C++ API (FFTW Wisdom)

```cpp
#include "cache/fftw_wisdom_manager.h"

// Load or create optimized FFT plans
dase::cache::FFTWWisdomManager wisdom;
wisdom.loadOrCreate(grid_nx, grid_ny, grid_nz);

// Now create FFT plans - they use cached wisdom
fftw_plan forward = fftw_plan_dft_3d(
    grid_nx, grid_ny, grid_nz,
    field_in, field_out,
    FFTW_FORWARD, FFTW_ESTIMATE
);

// First run: ~5 seconds to create wisdom
// Subsequent runs: <0.1 seconds with optimized plans
```

---

## Cache Categories

### 1. Fractional Kernels
**Purpose:** Reuse Caputo/SOE fractional derivative coefficients
**Key Format:** `kernel_{alpha}_{dt}_{num_steps}`
**Storage:** `.npz` compressed NumPy arrays
**Benefit:** 50-80% speedup on fractional engine startup

### 2. Laplacian Stencils
**Purpose:** Reuse finite-difference matrices for identical grids
**Key Format:** `laplacian_{dim}_{Nx}_{Ny}_{Nz}_{boundary}`
**Storage:** `.npz` sparse matrices
**Benefit:** Zero recomputation cost

### 3. FFTW Wisdom
**Purpose:** Preserve optimized FFT plans per grid size
**Key Format:** `fftw_{Nx}_{Ny}_{Nz}_{cpu_model}.dat`
**Storage:** Binary FFTW wisdom files
**Benefit:** 10-30% FFT speedup, 1-5s initialization → <0.1s

### 4. Echo Templates
**Purpose:** Reuse prime-structured echo schedules (IGSOA GW)
**Key Format:** `echo_template_{alpha}_{tau0}_{num_echoes}`
**Storage:** `.json` with timings and envelopes
**Benefit:** Constant-time echo generation

### 5. State Profiles
**Purpose:** Pre-computed initial states (Gaussian, soliton, etc.)
**Key Format:** `state_{profile_type}_{amplitude}_{sigma}_{grid_shape}`
**Storage:** `.npz` field arrays
**Benefit:** Fast mission startup, deterministic initialization

### 6. Source Maps
**Purpose:** Spatial masks for SATP multi-zone sources
**Key Format:** `source_map_{hash(layout)}_{grid_shape}`
**Storage:** `.npz` binary or float masks
**Benefit:** Reusable zone configurations

### 7. Mission Graph
**Purpose:** DAG-level reuse of computational subgraphs
**Key Format:** SHA256 hash of command + dependencies
**Storage:** `.json` or `.npz` depending on data type
**Benefit:** Skip redundant computation in multi-step missions

### 8. Surrogates
**Purpose:** Trained ML models for fast inference
**Key Format:** `{engine_type}_v{version}.pt`
**Storage:** PyTorch model files + JSON metadata
**Benefit:** 10-100x speedup for predictions in known regimes

---

## Maintenance

### Viewing Cache Stats

```bash
# Python script
python -c "from backend.cache import CacheManager; cm = CacheManager(); print(cm.get_stats())"
```

### Clearing Cache

```python
from backend.cache import CacheManager
cache = CacheManager()

# Clear specific category
cache.clear_category("mission_graph")

# Clear all
cache.clear_all()
```

### Manual Cleanup

Cache files can be safely deleted manually:
```bash
# Remove old mission graph cache
rm cache/mission_graph/*.json

# Remove all FFTW wisdom (force re-optimization)
rm cache/fftw_wisdom/*.dat
```

---

## Performance Tips

1. **Keep cache on SSD** - Faster I/O for large arrays
2. **Monitor cache size** - Set up eviction if >500GB
3. **Use checksums** - Enable with `CacheManager(enable_checksums=True)`
4. **Backup trained models** - Copy `cache/surrogates/` to safe location

---

## Troubleshooting

**Issue: Cache not being used**
- Check cache hit rate with `cache.get_stats()`
- Verify key generation is deterministic
- Enable debug logging

**Issue: Cache corruption**
- Delete corrupted category: `cache.clear_category("category_name")`
- Checksums will detect corruption automatically

**Issue: Out of disk space**
- Check `cache.get_stats()` for sizes
- Clear old mission graph entries
- Implement eviction policy (Phase D)

---

## References

- **Implementation Plan:** `docs/implementation/CACHE_IMPLEMENTATION_PLAN_PHASE_A.md`
- **Cost/Benefit:** `docs/implementation/CACHE_COST_BENEFIT_ANALYSIS.md`
- **Feature Analysis:** `docs/implementation/PROPOSED_FEATURES_ANALYSIS.md`

---

**Created:** 2025-11-11
**Version:** 1.0
**Status:** Phase A - Foundation
