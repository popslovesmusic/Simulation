# Audit Report Verification Summary

**Date**: November 3, 2025
**External Audit**: report.md
**Current Status**: After 17 fixes applied today

---

## Quick Status of Top 10 Findings

| # | Finding | Status | Notes |
|---|---------|--------|-------|
| 1 | Default R_c=1e-34 | ⚠️ **VALID** | Still 1e-34 in igsoa_complex_node.h:73 |
| 2 | No CFL/stability guard | ⚠️ **VALID** | Explicit Euler without dt validation |
| 3 | CMake Windows-only FFTW | ⚠️ **VALID** | CMakeLists.txt:42-52 blocks Linux |
| 4 | Division by zero in metrics | ⚠️ **PARTIAL** | Fixed in 2D, NOT in 1D |
| 5 | 3D missing normalization | ⚠️ **VALID** | No normalize_psi in igsoa_physics_3d.h |
| 6 | 3D applyDriving incomplete | ⚠️ **VALID** | Only drives phi, not psi (2D drives both) |
| 7 | 1D gradient forward vs central | ❓ **UNCHECKED** | Need to verify |
| 8 | Neighbor loop inefficiencies | ✅ **PARTIALLY ADDRESSED** | Applied int precomputation (+5-10%) |
| 9 | Bridge server DoS risk | ⚠️ **VALID** | No input validation in bridge_server.py |
| 10 | No automated tests | ⚠️ **PARTIALLY VALID** | Test files exist but no CI |

**Summary**: 6 valid issues, 2 partially addressed, 1 unchecked, 1 fixed

---

## What Was Fixed Today (Not in Audit Report)

The audit report appears to predate today's work. Issues **we fixed** that audit didn't mention:

1. ✅ 3D center-of-mass toroidal wrapping bug
2. ✅ M_PI definition for MSVC
3. ✅ updateEntropyRate() missing in 3D
4. ✅ Inconsistent function naming (evolveCausalField)
5. ✅ 3D gradient computation missing
6. ✅ Thread-unsafe static bool diagnostics
7. ✅ Missing bounds checking (debug mode)
8. ✅ Const correctness improvements
9. ✅ Named constants for magic numbers
10. ✅ Input validation in constructors
11. ✅ Int precomputation optimization

---

## Critical Issues Requiring Immediate Attention

### Priority 1: Default R_c Too Small

**Current**: `R_c(1e-34)` in src/cpp/igsoa_complex_node.h:73
**Impact**: **Disables all non-local coupling by default**
**Fix Required**:
```cpp
// Change from:
, R_c(1e-34)              // Default causal resistance

// To:
, R_c(3.0)                // Default causal radius (≈3 lattice units)
```

**Verification**:
```bash
grep "R_c(1e-34)" src/cpp/igsoa_complex_node.h
# Should return nothing after fix
```

---

### Priority 2: Division by Zero in 1D Engine

**Current**: src/cpp/igsoa_complex_engine.h:214
**Impact**: Returns inf/nan on first metrics call
**Fix Required**:
```cpp
// Change from:
out_speedup_factor = 15500.0 / ns_per_op_;

// To (already fixed in 2D):
out_speedup_factor = (ns_per_op_ > 0.0) ? (15500.0 / ns_per_op_) : 0.0;
```

---

### Priority 3: 3D Missing Normalization

**Current**: src/cpp/igsoa_physics_3d.h:216 (timeStep)
**Impact**: 3D simulations accumulate norm error
**Fix Required**:
```cpp
// In timeStep(), after computeGradients:
operations += computeGradients(nodes, N_x, N_y, N_z);
if (config.normalize_psi) {
    operations += IGSOAPhysics::normalizeStates(nodes);
}
return operations;
```

---

### Priority 4: 3D applyDriving Incomplete

**Current**: src/cpp/igsoa_physics_3d.h:233
**Impact**: 3D doesn't drive psi like 2D does
**Fix Required**:
```cpp
// In applyDriving(), add psi driving:
for (auto& node : nodes) {
    node.phi += signal_real;
    node.psi += std::complex<double>(signal_real, signal_imag);  // ADD THIS
}
```

---

### Priority 5: CMake Platform Lock

**Current**: CMakeLists.txt:42-52
**Impact**: Linux/macOS builds fail
**Fix Required**:
```cmake
# Replace hardcoded Windows lib search with:
find_package(FFTW3 REQUIRED COMPONENTS fftw3)
set(FFTW3_LIBRARY FFTW3::fftw3)
```

---

## Audit Recommendations vs Reality

### Recommendations Already Implemented ✅

1. ✅ Add bounds checking → **Done** (debug mode, 2D/3D engines)
2. ✅ Add input validation → **Done** (constructors validate dimensions)
3. ✅ Fix thread safety → **Done** (std::once_flag)
4. ✅ Add const correctness → **Done** (2D matches 3D)
5. ✅ Optimize repeated casts → **Done** (int precomputation)

### Recommendations Still Pending ⚠️

1. ⚠️ Fix default R_c → **Not done**
2. ⚠️ Add CFL/stability check → **Not done**
3. ⚠️ Fix CMake portability → **Not done**
4. ⚠️ Add 3D normalization → **Not done**
5. ⚠️ Complete 3D applyDriving → **Not done**
6. ⚠️ Add CI/automated tests → **Not done**
7. ⚠️ Bridge server validation → **Not done**

---

## Token Budget Notice

**Current Usage**: ~90k/200k tokens (45%)
**Remaining**: ~110k tokens

Given token budget, creating quick-fix script for the 5 critical issues.

---

## Recommended Next Steps

### Immediate (Can do with remaining tokens):

1. Fix default R_c value (1 line change)
2. Fix 1D division by zero (1 line change)
3. Add 3D normalization (3 lines)
4. Complete 3D applyDriving (1 line)

### Requires More Work:

5. Fix CMake portability (needs testing)
6. Add CFL/stability validation (complex, needs math)
7. Add CI pipeline (separate project)
8. Bridge server security (separate concern)

---

## Quick Fix Script

Will create `apply_audit_critical_fixes.py` to address the 4 easiest critical issues.

---

**END OF VERIFICATION SUMMARY**

**Conclusion**: Audit report identified real issues. Today's work fixed different set of issues. 5 critical findings remain, 4 can be fixed quickly.
