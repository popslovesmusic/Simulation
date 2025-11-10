# Derived Data Storage Optimization Analysis

**Date**: November 4, 2025
**Status**: Analysis Complete - Recommendations Provided

---

## Executive Summary

Analyzed derived data storage in `IGSOAComplexNode` struct. Found:
- **F_gradient**: Dead storage (8 bytes/node wasted) - **RECOMMEND REMOVAL**
- **entropy_rate**: Actively used - **KEEP AS-IS**

**Memory Impact**: Removing F_gradient saves ~8% node memory (8/120 bytes)

---

## Analysis Details

### 1. F_gradient (DEAD STORAGE)

**Current State**:
```cpp
double F_gradient;  // Line 48, igsoa_complex_node.h
```

**Write Locations**:
- `igsoa_physics.h:227` - 1D gradient computation
- `igsoa_physics_2d.h:276` - 2D gradient computation
- `igsoa_physics_3d.h:205` - 3D gradient computation
- `igsoa_complex_engine.h:268` - Zero initialization
- `igsoa_complex_engine_2d.h:289` - Zero initialization

**Read Locations**: **NONE** (dead storage)

**Comment Discrepancy**:
- Line 37 says: `entropy_rate: Entropy production Ṡ = R_c(∇F)²`
- Line 103 implementation: `Ṡ = R_c(Φ - Re[Ψ])²`
- **F_gradient is NOT used in entropy calculation**

**Recommendation**: **REMOVE** from node struct

**Rationale**:
1. Never read, only written
2. Wastes 8 bytes per node (8% of 120-byte struct)
3. Cache pollution (loads unused data during node access)
4. If needed in future, compute on-demand in dedicated function

**Impact**:
- Memory savings: 8 bytes × N nodes
  - 64×64 lattice: 32 KB saved
  - 128×128 lattice: 128 KB saved
  - 1M nodes: 8 MB saved
- Cache locality improvement: 6.7% reduction in struct size

---

### 2. entropy_rate (ACTIVELY USED)

**Current State**:
```cpp
double entropy_rate;  // Line 52, igsoa_complex_node.h
```

**Write Locations**:
- `igsoa_complex_node.h:110` - updateEntropyRate() method
- `igsoa_complex_engine.h:269` - Zero initialization
- `igsoa_complex_engine_2d.h:290` - Zero initialization

**Read Locations**:
- `igsoa_physics.h:330` - computeTotalEntropyRate() summation
- `igsoa_physics_2d.h:375` - computeTotalEntropyRate() summation
- `test_igsoa_complex_node.cpp:134,140,145` - Unit tests

**C API Exposure**:
- `igsoa_capi.h:190` - igsoa_get_total_entropy_rate()
- `igsoa_capi_2d.h:264` - igsoa2d_get_entropy_rate()

**Recommendation**: **KEEP AS-IS**

**Rationale**:
1. Actually used for summation in computeTotalEntropyRate()
2. Exposed via C API (breaking change to remove)
3. Called frequently, so storage justified over recomputation
4. Only 8 bytes per node

**Alternative (NOT RECOMMENDED)**:
- Lazy evaluation: Recompute in computeTotalEntropyRate()
- Would save 8 bytes/node but add O(N) computation every call
- Current approach is optimal for access pattern

---

## Recommended Optimizations

### Option 1: Remove F_gradient (Recommended)

**Changes Required**:
1. Remove from IGSOAComplexNode struct (line 48)
2. Remove computeGradients() calls in physics files
3. If gradient needed in future, create separate compute function:

```cpp
// On-demand gradient computation (no storage)
static double computeGradientMagnitude(
    const std::vector<IGSOAComplexNode>& nodes,
    size_t i, size_t N_x, size_t N_y
) {
    // Compute and return immediately (no storage)
    double dF_dx = /* ... */;
    double dF_dy = /* ... */;
    return std::sqrt(dF_dx * dF_dx + dF_dy * dF_dy);
}
```

**Impact**:
- Memory: -8 bytes/node (6.7% reduction)
- Performance: Neutral (removes dead code)
- Complexity: Simplifies codebase

### Option 2: Make F_gradient Optional (Alternative)

If there's concern about future use:

```cpp
struct IGSOAComplexNode {
    // ... existing fields ...

    #ifdef IGSOA_STORE_GRADIENTS
    double F_gradient;  // Optional: Enable with compiler flag
    #endif
};
```

**Impact**:
- Memory: -8 bytes/node by default
- Flexibility: Can enable if needed
- Complexity: Adds conditional compilation

### Option 3: Lazy Compute entropy_rate (NOT RECOMMENDED)

Replace storage with on-demand computation:

```cpp
// In IGSOAComplexNode: Remove entropy_rate field

// In computeTotalEntropyRate:
static double computeTotalEntropyRate(const nodes) {
    double total = 0.0;
    for (const auto& node : nodes) {
        // Compute instead of read
        double diff = node.phi - node.psi.real();
        total += node.R_c * diff * diff;
    }
    return total;
}
```

**Why NOT RECOMMENDED**:
- entropy_rate is used (unlike F_gradient)
- Called frequently via C API
- Only 8 bytes, storage is cheaper than recomputation

---

## Implementation Priority

### High Priority (Recommended)
✅ **Remove F_gradient** - Dead storage, no downside

### Low Priority (Optional)
⏸️ **Lazy entropy_rate** - Not worthwhile, keep as-is

---

## Memory Impact Summary

| System | Current | Without F_gradient | Savings |
|--------|---------|-------------------|---------|
| 64×64 (2D) | 491 KB | 459 KB | 32 KB (6.5%) |
| 128×128 (2D) | 1.96 MB | 1.84 MB | 128 KB (6.5%) |
| 256×256 (2D) | 7.86 MB | 7.36 MB | 512 KB (6.5%) |
| 32³ (3D) | 3.93 MB | 3.68 MB | 256 KB (6.5%) |
| 1M nodes | 114 MB | 107 MB | 8 MB (6.5%) |

**Cache Impact**:
- Current struct: 120 bytes (15 cache lines on 64-byte systems)
- Optimized: 112 bytes (14 cache lines)
- **7% better cache utilization**

---

## Proposed Changes

### File: src/cpp/igsoa_complex_node.h

**Remove**:
```cpp
double F_gradient;  // Line 48 - REMOVE (dead storage)
```

### File: src/cpp/igsoa_physics_3d.h

**Remove** lines 162-203 (computeGradients function)
**Remove** line 153 call to computeGradients

### File: src/cpp/igsoa_physics_2d.h

**Remove** lines 251-278 (gradient computation in evolveQuantumState)

### File: src/cpp/igsoa_physics.h

**Remove** lines 219-229 (gradient computation)

---

## Testing Requirements

If F_gradient is removed:

1. **Compile test**: Verify no errors
2. **Unit tests**: Update tests that reference F_gradient
3. **Integration tests**: Run full simulation suite
4. **Benchmark**: Measure memory reduction
5. **C API**: Verify no breakage (F_gradient not exposed)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| F_gradient needed in future | Low | Medium | Easy to recompute on-demand |
| Breaking change | None | None | Not exposed in C API |
| Performance regression | None | None | Removes dead code only |

**Overall Risk**: **VERY LOW**

---

## Conclusion

**Recommendation**: Remove F_gradient from IGSOAComplexNode struct.

**Benefits**:
- Saves 8 bytes per node (6-7% memory reduction)
- Improves cache locality
- Simplifies codebase (removes dead code)
- No downside (never used)

**entropy_rate**: Keep as-is (actively used, worthwhile storage)

**Next Steps**:
1. Remove F_gradient field
2. Remove gradient computation code
3. Update any tests that reference it
4. Verify compilation and tests pass

---

**END OF ANALYSIS**

**Date**: November 4, 2025
**Status**: Analysis Complete
**Recommendation**: Proceed with F_gradient removal
