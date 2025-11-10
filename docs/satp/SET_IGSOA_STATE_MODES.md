# set_igsoa_state Mode Reference

**Three selectable modes for IGSOA state initialization**

Version: 2.0
Updated: November 2, 2025

---

## Overview

The `set_igsoa_state` command now supports three different modes for applying Gaussian profiles to IGSOA complex engines:

1. **`overwrite`** - Complete replacement (default, backwards compatible)
2. **`add`** - Additive delta on existing field
3. **`blend`** - Weighted interpolation toward target state

---

## Mode Selection

Add a `"mode"` field to the `params` object:

```json
{
  "command": "set_igsoa_state",
  "params": {
    "engine_id": "engine_001",
    "profile_type": "gaussian",
    "params": {
      "amplitude": 1.5,
      "center_node": 2048,
      "width": 256,
      "baseline_phi": 0.0,
      "mode": "overwrite"     ← Mode selector
    }
  }
}
```

**If `mode` is omitted**, defaults to `"overwrite"` (backwards compatible).

---

## Mode Details

### Mode 1: `"overwrite"` (Default)

**Behavior:** Complete replacement of field with Gaussian profile.

**Formula:**
```
Ψ(x) = G(x)              (Gaussian magnitude, zero phase)
Φ(x) = baseline_phi      (uniform baseline)
```

**Use when:**
- Starting fresh simulation
- Resetting to known initial condition
- First call to `set_igsoa_state`

**Example:**
```json
{
  "command": "set_igsoa_state",
  "params": {
    "engine_id": "engine_001",
    "profile_type": "gaussian",
    "params": {
      "amplitude": 1.0,
      "center_node": 512,
      "width": 100,
      "baseline_phi": 0.0,
      "mode": "overwrite"
    }
  }
}
```

**Result:** Ψ and Φ are completely replaced with new Gaussian centered at node 512.

---

### Mode 2: `"add"`

**Behavior:** Add Gaussian shape on top of existing field values.

**Formula:**
```
Ψ(x) = Ψ_old(x) + G(x)
Φ(x) = Φ_old(x) + G(x)
```

Where G(x) = amplitude × exp(-distance² / (2 × width²))

**Use when:**
- Injecting additional energy/excitation
- Creating multi-peaked distributions
- Simulating external perturbations

**Example:**
```json
{
  "command": "set_igsoa_state",
  "params": {
    "engine_id": "engine_001",
    "profile_type": "gaussian",
    "params": {
      "amplitude": 0.5,
      "center_node": 256,
      "width": 50,
      "baseline_phi": 0.0,
      "mode": "add"
    }
  }
}
```

**Result:** A Gaussian bump with amplitude 0.5 is **added** to whatever Ψ and Φ currently exist.

**Note:** `baseline_phi` parameter is ignored in `add` mode (only Gaussian shape is added, not baseline).

---

### Mode 3: `"blend"`

**Behavior:** Weighted interpolation between current state and target Gaussian.

**Formula:**
```
Ψ(x) = (1 - β) × Ψ_old(x) + β × G(x)
Φ(x) = (1 - β) × Φ_old(x) + β × (baseline_phi + G(x))
```

Where β = blend factor (0 to 1)

**Parameters:**
- `beta`: Blend weight (0 = no change, 1 = full overwrite). Default: 0.1

**Use when:**
- Gradually transitioning between states
- Smooth field shaping over multiple calls
- Avoiding numerical shocks from sudden changes

**Example:**
```json
{
  "command": "set_igsoa_state",
  "params": {
    "engine_id": "engine_001",
    "profile_type": "gaussian",
    "params": {
      "amplitude": 2.0,
      "center_node": 512,
      "width": 150,
      "baseline_phi": 0.0,
      "mode": "blend",
      "beta": 0.3
    }
  }
}
```

**Result:** Current state is 70% retained, 30% moved toward the target Gaussian.

**Typical beta values:**
- `0.01` - Very gradual (1% per call)
- `0.1` - Default (10% per call)
- `0.5` - Halfway blend
- `1.0` - Full overwrite (equivalent to `"overwrite"` mode)

---

## Comparison Table

| Mode | Ψ Update | Φ Update | Use Case |
|------|----------|----------|----------|
| **overwrite** | `Ψ = G` | `Φ = baseline` | Initialize fresh state |
| **add** | `Ψ += G` | `Φ += G` | Add perturbation |
| **blend** | `Ψ = (1-β)Ψ + βG` | `Φ = (1-β)Φ + β(baseline+G)` | Smooth transition |

---

## Multi-Mode Workflow Examples

### Example 1: Build Multi-Peaked Distribution

```json
# Start with first Gaussian (overwrite)
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"center_node":256,"width":50,"baseline_phi":0.0,"mode":"overwrite"}}}

# Add second peak (add mode)
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":0.8,"center_node":768,"width":60,"baseline_phi":0.0,"mode":"add"}}}

# Add third peak (add mode)
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.2,"center_node":512,"width":80,"baseline_phi":0.0,"mode":"add"}}}
```

**Result:** Three Gaussian peaks superimposed.

---

### Example 2: Smooth State Transition

```json
# Start with wide Gaussian
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"center_node":512,"width":200,"baseline_phi":0.0,"mode":"overwrite"}}}

# Run simulation for 100 steps
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":100,"iterations_per_node":30}}

# Gradually transition to narrow Gaussian (10% per call)
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":2.0,"center_node":512,"width":50,"baseline_phi":0.0,"mode":"blend","beta":0.1}}}

# Run more...
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":100,"iterations_per_node":30}}
```

**Result:** Smooth reshaping without numerical shocks.

---

### Example 3: Repeated Perturbations

```json
# Initialize
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"uniform","params":{"psi_real":0.1,"psi_imag":0.0,"phi":0.0}}}

# Add perturbation at t=0
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":0.5,"center_node":256,"width":30,"baseline_phi":0.0,"mode":"add"}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":50,"iterations_per_node":30}}

# Add another perturbation at t=50
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":0.5,"center_node":768,"width":30,"baseline_phi":0.0,"mode":"add"}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":50,"iterations_per_node":30}}
```

**Result:** Study how system responds to sequential perturbations.

---

## Technical Notes

### Implementation Location
- File: `dase_cli/src/engine_manager.cpp`
- Function: `EngineManager::setIgsoaState()`
- Lines: 370-439

### Gaussian Formula
```cpp
double distance = (double)i - (double)center_node;
double G = amplitude * exp(-(distance * distance) / (2.0 * width * width));
```

### Mode Selection Logic
```cpp
std::string mode = params.value("mode", "overwrite");

if (mode == "overwrite") {
    // Replace
} else if (mode == "add") {
    // Add
} else if (mode == "blend") {
    // Interpolate
} else {
    // Unknown mode → fail
}
```

### Error Handling
- Unknown mode string → command fails with `status: "error"`
- Missing `beta` in blend mode → defaults to 0.1
- Missing `mode` → defaults to `"overwrite"`

---

## Validation

All modes work correctly as verified by test:

```bash
cd dase_cli
cat test_modes.json | ./dase_cli.exe
```

Expected output:
```
{"command":"set_igsoa_state","status":"success"} # overwrite mode
{"command":"set_igsoa_state","status":"success"} # add mode
{"command":"set_igsoa_state","status":"success"} # blend mode
```

---

## API Summary

### Overwrite Mode
```json
{
  "params": {
    "amplitude": <float>,
    "center_node": <int>,
    "width": <float>,
    "baseline_phi": <float>,
    "mode": "overwrite"      // or omit for default
  }
}
```

### Add Mode
```json
{
  "params": {
    "amplitude": <float>,
    "center_node": <int>,
    "width": <float>,
    "baseline_phi": <ignored>,
    "mode": "add"
  }
}
```

### Blend Mode
```json
{
  "params": {
    "amplitude": <float>,
    "center_node": <int>,
    "width": <float>,
    "baseline_phi": <float>,
    "mode": "blend",
    "beta": <float 0-1>      // default 0.1 if omitted
  }
}
```

---

## Backwards Compatibility

✅ **Old JSON configs work unchanged**

If you have existing configs without `"mode"`, they still work:

```json
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256,"baseline_phi":0.0}}}
```

This automatically uses `mode: "overwrite"` (the original behavior).

---

**For more details, see:**
- Full API Reference: `docs/API_REFERENCE.md`
- Analysis Guide: `docs/IGSOA_ANALYSIS_GUIDE.md`
- Usage Examples: `dase_cli/USAGE.md`
