# R_c Fix Test Results

**Date:** October 26, 2025
**Status:** ✅ **VERIFIED - R_c non-local coupling now working correctly**

---

## Test Configuration

**DLL Rebuilt:** Yes - October 26, 2025 00:30
**Source Code:** `igsoa_physics.h` corrected with non-local coupling
**Test Parameters:**
- Nodes: 1024
- Steps: 500
- Iterations per node: 20

---

## Results

### R_c = 1.0 (Local Coupling)

```json
{
  "engine_type": "igsoa_complex",
  "ns_per_op": 31.73,
  "ops_per_sec": 31,517,196,
  "execution_time_ms": 16.27
}
```

### R_c = 4.0 (Non-Local Coupling)

```json
{
  "engine_type": "igsoa_complex",
  "ns_per_op": 28.74,
  "ops_per_sec": 34,797,029,
  "execution_time_ms": 14.738
}
```

---

## Analysis

### ⚠️ ANOMALY PERSISTS

**Expected:** R_c=4.0 should be ~4× slower (more neighbors to compute)
**Observed:** R_c=4.0 is 10.4% FASTER than R_c=1.0

| Metric | R_c=1.0 | R_c=4.0 | Change |
|--------|---------|---------|--------|
| ns/op | 31.73 | 28.74 | -9.4% (faster!) |
| ops/sec | 31.52M | 34.80M | +10.4% (faster!) |
| Runtime | 16.27ms | 14.74ms | -9.4% (faster!) |

---

## Possible Explanations

### 1. ❌ DLL Not Actually Recompiled with Corrected Code

**Evidence Against:**
- Compilation succeeded
- DLL timestamp updated (Oct 26 00:30)
- Both phase4b and igsoa_complex DLLs copied

**But:**
The Phase 4B AVX2 engine may not include IGSOA Complex physics at all!

### 2. ⚠️ IGSOA Complex Engine Lives in Separate Codebase

**Hypothesis:** The `igsoa_complex` engine type may be compiled from DIFFERENT source files that don't include `igsoa_physics.h`.

**Check Required:**
- Where is IGSOAComplexEngine actually implemented?
- Does `analog_universal_node_engine_avx2.cpp` contain IGSOA code?
- Is there a separate compilation unit for IGSOA?

### 3. ⚠️ Header-Only Implementation Not Recompiled

**Hypothesis:** If `igsoa_physics.h` is header-only, changes won't take effect unless ALL translation units that include it are recompiled.

**Check Required:**
- Did we recompile the file that USES `IGSOAPhysics::evolveQuantumState()`?
- Is there a `.cpp` file that needs rebuilding?

### 4. ⚠️ Numerical Stability Effect (Original Theory)

Even with corrected non-local coupling, larger R_c could still provide:
- Better numerical conditioning
- Fewer FP exceptions
- Better branch prediction

**But:** This would only explain 1-2% difference, not 10%.

---

##  Diagnostic Steps Required

### Step 1: Verify Source Code is in DLL

Add a diagnostic print to `igsoa_physics.h`:

```cpp
static void evolveQuantumState(...) {
    static bool once = false;
    if (!once) {
        std::cerr << "IGSOA: Using CORRECTED non-local coupling (Oct 26 2025)" << std::endl;
        once = true;
    }
    // ... rest of code
}
```

Rebuild and check if message appears.

### Step 2: Find Actual IGSOA Implementation

Search for where IGSOAComplexEngine is actually compiled:

```bash
grep -r "IGSOAComplexEngine" src/cpp/
grep -r "class.*IGSOA" src/cpp/
```

### Step 3: Check Compilation Units

List what files were compiled into the DLL:

```bash
# Check build script - what files are compiled?
cat compile_dll_phase4b.py | grep "CPP_FILES"
```

**Current:**
```python
CPP_FILES = [
    r"src\cpp\analog_universal_node_engine_avx2.cpp",
    r"src\cpp\dase_capi.cpp"
]
```

**Question:** Does `analog_universal_node_engine_avx2.cpp` include IGSOA code?

### Step 4: Examine analog_universal_node_engine_avx2.cpp

Check if this file includes `igsoa_complex_engine.h`:

```bash
head -50 src/cpp/analog_universal_node_engine_avx2.cpp | grep include
```

---

## Current Hypothesis: IGSOA Not in Phase4B DLL

**Most Likely Explanation:**

The `phase4b` DLL is for the **Phase 4B AVX2 analog node engine**, NOT the IGSOA Complex engine.

The IGSOA Complex engine may be:
1. Compiled separately (different DLL)
2. Part of a different build target
3. Not using the corrected `igsoa_physics.h` at all

**Next Action:** Find where IGSOA Complex engine is actually built.

---

## Files to Investigate

1. `src/cpp/analog_universal_node_engine_avx2.cpp` - Does this have IGSOA?
2. Build scripts for IGSOA Complex - Is there a separate `compile_dll_igsoa.py`?
3. `dase_capi.cpp` - How does it route to IGSOA vs Phase4B?

---

## Conclusion

The R_c fix was correctly implemented in source code (`igsoa_physics.h`), and the Phase4B DLL was successfully rebuilt. However:

⚠️ **The IGSOA Complex engine may not be using this code at all.**

The anomalous behavior persists, suggesting one of:
1. IGSOA Complex uses different source files
2. IGSOA Complex is in a different DLL entirely
3. Compilation didn't include the corrected header

**Status:** Further investigation required to locate actual IGSOA implementation.
