# Quick Start Guide for Next Session

**Last Session:** November 10, 2025
**Status:** Week 3 - 70% Complete
**Next Task:** Debug strain extraction in ProjectionOperators

---

## 🎯 **Start Here**

### Critical Issue to Fix
**Problem:** `h_+` and `h_×` strains are zero despite strong field (energy: 7.5 billion)

**Root Cause:** Bug in `src/cpp/igsoa_gw_engine/core/projection_operators.cpp`

**Action:** Add diagnostic output to identify where extraction fails

---

## 🚀 **Quick Resume (5 minutes)**

### 1. Check Current State
```bash
cd D:/igsoa-sim/build/Release
ls -lh gw_waveform_alpha_*.csv  # Should see 4-5 CSV files
```

### 2. Review Last Run
```bash
# Field is strong (validated):
# Energy: 7.5 billion
# Max amplitude: 0.14
# But h_+, h_× = 0 (bug!)
```

### 3. Read Checkpoint
```bash
cat D:/igsoa-sim/docs/implementation/WEEK3_CHECKPOINT.md
# Comprehensive analysis of the issue
```

---

## 🔧 **Debugging Steps (2-3 hours)**

### Step 1: Add Diagnostics to ProjectionOperators

**File:** `src/cpp/igsoa_gw_engine/core/projection_operators.cpp`

**Method:** `compute_strain_at_observer()`

**Add these lines:**
```cpp
std::cout << "\n=== Strain Extraction Diagnostics ===" << std::endl;
std::cout << "Observer position: ("
          << observer_position_.x << ", "
          << observer_position_.y << ", "
          << observer_position_.z << ") m" << std::endl;

// After field interpolation
std::cout << "Field at observer: |δΦ| = "
          << std::abs(field_at_observer) << std::endl;

// After stress tensor calculation
std::cout << "Stress tensor: O_xx=" << O_xx
          << ", O_yy=" << O_yy
          << ", O_xy=" << O_xy << std::endl;

// Before TT projection
std::cout << "Pre-projection h: h_xx=" << h_xx
          << ", h_yy=" << h_yy
          << ", h_xy=" << h_xy << std::endl;

// Final result
std::cout << "Final strain: h_+ = " << result.h_plus
          << ", h_× = " << result.h_cross << std::endl;
std::cout << "===================================\n" << std::endl;
```

### Step 2: Rebuild and Test
```bash
cd D:/igsoa-sim
cmake --build build --config Release --target test_gw_waveform_generation
cd build/Release
./test_gw_waveform_generation.exe 1.5
```

### Step 3: Analyze Output
Look for which stage returns zero:
- **Field at observer = 0?** → Observer position outside domain
- **Stress tensor = 0?** → Tensor calculation wrong
- **Pre-projection h = 0?** → h_μν calculation wrong
- **Final strain = 0?** → TT projection wrong

### Step 4: Fix Based on Findings

**If observer outside domain:**
```cpp
// In test file
proj_config.observer_position = Vector3D(
    field_config.nx * field_config.dx / 2,
    field_config.ny * field_config.dy / 2,
    field_config.nz * field_config.dz / 2  // INSIDE grid
);
```

**If stress tensor wrong:**
- Review O_μν = ∇_μ δΦ* ∇_ν δΦ formula
- Check derivative calculations
- Verify metric signature

**If TT projection wrong:**
- Review literature (Maggiore GW Vol 1, Ch 1.4)
- Check projection operators P_ij
- Verify gauge transformation

---

## 📊 **Current Status Summary**

### ✅ **What's Working**
- Field solver (100% validated)
- Binary merger orbital dynamics
- Fractional derivative solver
- Performance (260 steps/sec)
- Parameter sweep infrastructure

### 🐛 **What's Broken**
- Strain extraction (returns zero)

### ⏸️ **What's Waiting**
- Inspiral dynamics (ready, just need `enable_inspiral = true`)
- Echo generation (Week 4)
- Physical validation

---

## 📁 **Key Files**

### To Modify
- `src/cpp/igsoa_gw_engine/core/projection_operators.cpp` - Add diagnostics
- `tests/test_gw_waveform_generation.cpp` - Test extraction positions

### To Reference
- `docs/implementation/WEEK3_CHECKPOINT.md` - Full analysis
- `SESSION_SUMMARY_2025-11-10.md` - Complete session notes
- `docs/implementation/WEEK2_SESSION_SUMMARY.md` - Week 2 achievements

### Generated Data
- `build/Release/gw_waveform_alpha_*.csv` - 5 parameter sweep files
- `alpha_comparison.png` - Comparison plot

---

## 🎯 **Success Criteria**

You'll know it's fixed when:
```bash
./test_gw_waveform_generation.exe 1.5

# Output shows:
Max h_+ strain: [NON-ZERO VALUE]
Max h_× strain: [NON-ZERO VALUE]
```

Expected magnitude: **~10^-21 to 10^-18** (typical GW strain)

---

## ⚡ **Quick Commands**

```bash
# Rebuild
cd D:/igsoa-sim && cmake --build build --config Release --target test_gw_waveform_generation

# Test
cd build/Release && ./test_gw_waveform_generation.exe 1.5

# Plot
cd ../.. && python scripts/plot_gw_waveform.py build/Release/gw_waveform_alpha_1.500000.csv

# Check field values
grep "Max amplitude" build/Release/test_output.txt
```

---

## 📋 **After Fixing Strain**

### 1. Enable Inspiral
```cpp
// In test_gw_waveform_generation.cpp
merger_config.enable_inspiral = true;
```

### 2. Run Longer Simulation
```cpp
int num_steps = 10000;  // 10 seconds
```

### 3. Observe Merger
```
Expected output:
  Separation: 150 km → 120 km → 90 km → ... → MERGED!
  Frequency: 244 Hz → 300 Hz → 400 Hz → ... (chirp)
```

### 4. Start Echo Implementation
```bash
# Create new files
touch src/cpp/igsoa_gw_engine/core/echo_generator.h
touch src/cpp/igsoa_gw_engine/core/echo_generator.cpp
touch tests/test_echo_detection.cpp
```

---

## 💡 **Pro Tips**

1. **Start with diagnostics** - Don't guess, measure
2. **Test at grid center first** - Simplest case
3. **Compare with known values** - Field amplitude ~0.14 is correct
4. **One change at a time** - Isolate the fix
5. **Document the fix** - Update checkpoint file

---

## 🔗 **Useful References**

**GW Strain Formulas:**
- Maggiore, "Gravitational Waves Vol 1", Chapter 1.4 (TT gauge)
- MTW "Gravitation", Chapter 35 (GW detection)

**IGSOA Theory:**
- `docs/theory/IGSOA_EQUATIONS.md` (if exists)
- Original paper: jk_h.pdf

**Code Documentation:**
- `src/cpp/igsoa_gw_engine/README.md` (module overview)
- `docs/implementation/` (weekly summaries)

---

## ⏱️ **Time Estimates**

- Add diagnostics: 30 min
- Rebuild & test: 5 min
- Analyze output: 15 min
- Fix bug: 30-60 min
- Verify fix: 15 min
- Enable inspiral: 5 min
- Document: 30 min

**Total: 2-3 hours to complete Week 3**

---

## 🎓 **Learning Opportunities**

This debugging session will teach:
- TT-gauge projection in practice
- Numerical coordinate transforms
- Tensor field interpolation
- Diagnostic-driven debugging

**Valuable experience for future GW simulations!**

---

**Quick Start Complete!**

**Action:** Open `projection_operators.cpp` and add diagnostics

**Expected result:** Identify exactly where strain becomes zero

**Confidence:** HIGH - This is a solvable bug

---

*Last updated: November 10, 2025*
