# Quick Start Guide

**Get up and running with IGSOA simulations in 5 minutes**

Version: 1.0
Date: November 3, 2025

---

## Prerequisites

- IGSOA CLI built (`dase_cli/dase_cli.exe`)
- Python 3.x with NumPy, Matplotlib, SciPy
- Bash shell (Git Bash on Windows)

---

## Your First Simulation (60 seconds)

### Step 1: Create Configuration (10 seconds)

```bash
cd dase_cli
cat > my_first_sim.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024,"R_c":1.0}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"center_node":512,"width":100}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":10,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF
```

### Step 2: Run Simulation (20 seconds)

```bash
cat my_first_sim.json | ./dase_cli.exe > output.json
```

### Step 3: Analyze Results (30 seconds)

```bash
python analyze_igsoa_state.py output.json 1.0 --output-dir my_analysis
```

### Step 4: View Results

Open `my_analysis/analysis_report_R1.0.txt` to see:
- Drift measurement
- Correlation length ξ
- State statistics
- Spectral analysis

---

## Common Workflows

### Test Zero Drift

**Goal**: Verify Gaussian packet doesn't translate

**Command**:
```bash
cd dase_cli
cat > test_drift.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096,"R_c":1.0}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":100.0,"center_node":2048,"width":256}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
EOF

cat test_drift.json | ./dase_cli.exe > output_drift.json
python extract_drift.py output_drift.json 2048
```

**Expected**: Drift < 1% of N (< 41 nodes for N=4096)

---

### Compare Different R_c Values

**Goal**: See how causal radius affects correlation length

**Commands**:
```bash
cd dase_cli

# Test R_c = 0.5
echo '{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096,"R_c":0.5}}' > test.json
echo '{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":100.0,"center_node":2048,"width":256}}}' >> test.json
echo '{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1,"iterations_per_node":30}}' >> test.json
echo '{"command":"get_state","params":{"engine_id":"engine_001"}}' >> test.json

cat test.json | ./dase_cli.exe > output_Rc0.5.json
python analyze_igsoa_state.py output_Rc0.5.json 0.5 --output-dir analysis_Rc0.5

# Check correlation length
grep "Ratio ξ/R_c" analysis_Rc0.5/analysis_report_R0.5.txt

# Repeat for R_c = 1.0, 2.0, 5.0, 10.0
```

---

### Capture Time Evolution with Snapshots

**Goal**: See state at multiple timesteps

**Command**:
```bash
cd dase_cli
cat > test_snapshots.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024,"R_c":1.0}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":10.0,"center_node":512,"width":100}}}
{"command":"run_mission_with_snapshots","params":{"engine_id":"engine_001","num_steps":10,"snapshot_interval":2}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

cat test_snapshots.json | ./dase_cli.exe > output_snapshots.json
```

**Output**: JSON with snapshots at T=2,4,6,8,10

---

### Test Three Initialization Modes

**Goal**: Compare overwrite, add, and blend modes

**Command**:
```bash
cd dase_cli
cat > test_modes.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"center_node":512,"width":100,"mode":"overwrite"}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":0.5,"center_node":256,"width":50,"mode":"add"}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":2.0,"center_node":512,"width":150,"mode":"blend","beta":0.3}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
EOF

cat test_modes.json | ./dase_cli.exe
```

**Result**: Three different state configurations

---

## Running the Validation Suite

**Goal**: Verify all physics tests pass

**Command**:
```bash
cd tests
./test_physics_validation.sh
```

**Expected Output**:
```
[PASS] Zero Drift
[PASS] Correlation Length Scaling
[PASS] State Normalization
[PASS] Three-Mode Initialization
[PASS] Snapshot Feature

ALL TESTS PASSED
```

**If Tests Fail**: Check that:
1. `dase_cli/dase_cli.exe` is built
2. Python scripts are in `dase_cli/`
3. You have Python with NumPy, Matplotlib, SciPy

---

## Parameter Reference

### Engine Creation

```json
{"command":"create_engine","params":{
  "engine_type": "igsoa_complex",   // or "phase4b"
  "num_nodes": 4096,                // lattice size
  "R_c": 1.0                        // causal radius
}}
```

**Common Values**:
- `num_nodes`: 1024 (fast), 4096 (standard), 8192 (large)
- `R_c`: 0.5 to 10.0 (test range)

---

### Gaussian Initialization

```json
{"command":"set_igsoa_state","params":{
  "engine_id": "engine_001",
  "profile_type": "gaussian",
  "params": {
    "amplitude": 100.0,            // field strength
    "center_node": 2048,           // center position
    "width": 256,                  // Gaussian width (σ)
    "baseline_phi": 0.0,           // background Φ value
    "mode": "blend",               // "overwrite", "add", or "blend"
    "beta": 1.0                    // blend factor (0-1)
  }
}}
```

**Recommended**:
- **Low amplitude** (A=1-10): Fast equilibration, testing
- **High amplitude** (A=100): Spectral analysis, extended dynamics
- **Mode**: "overwrite" (default), "add" (perturbations), "blend" (smooth transition)

---

### Running Simulation

```json
{"command":"run_mission","params":{
  "engine_id": "engine_001",
  "num_steps": 10,                 // timesteps
  "iterations_per_node": 30        // integration density
}}
```

**Common Values**:
- `num_steps`: 1 (early time), 10 (short), 50 (medium), 200+ (long)
- `iterations_per_node`: 30 (standard)

---

### Snapshots

```json
{"command":"run_mission_with_snapshots","params":{
  "engine_id": "engine_001",
  "num_steps": 10,
  "snapshot_interval": 2            // capture every 2 steps
}}
```

**Use When**: Need state at multiple times for spectral evolution

---

## Analysis Tools

### analyze_igsoa_state.py

**Purpose**: Full state analysis (FFT, correlations, statistics)

**Usage**:
```bash
python analyze_igsoa_state.py <input.json> <R_c> --output-dir <dir>
```

**Outputs**:
- `analysis_report_R*.txt` - Text report
- `power_spectra_R*.png` - Fourier transform plot
- `spatial_correlation_R*.png` - Correlation function
- `state_profiles_R*.png` - Real-space fields

---

### extract_drift.py

**Purpose**: Measure center-of-mass drift

**Usage**:
```bash
python extract_drift.py <input.json> <initial_center>
```

**Example**:
```bash
python extract_drift.py output.json 2048
```

**Output**: Drift in nodes, verdict (PASS/FAIL)

---

## Troubleshooting

### Simulation runs but produces no output

**Issue**: Missing `get_state` command

**Fix**: Add to JSON:
```json
{"command":"get_state","params":{"engine_id":"engine_001"}}
```

---

### Analysis fails with "No valid get_state response"

**Issue**: Simulation didn't complete or no state extracted

**Check**:
1. Look for `"status":"success"` in output JSON
2. Verify `get_state` command was included
3. Check for error messages in JSON output

---

### Drift measurement shows "No structure in state"

**Issue**: State is completely uniform (fully equilibrated)

**Fix**: Run shorter simulation (T=1-10) or use higher amplitude

---

### "findfont" warnings during analysis

**Not an Error**: Matplotlib font warnings, safe to ignore

**Suppress**: Add `2>&1 | grep -v "findfont"` to command

---

### Tests fail with "bc: command not found"

**Issue**: `bc` calculator not installed (Windows Git Bash)

**Fixed**: Test suite now uses Python for calculations (no `bc` needed)

---

## Next Steps

### Learn the Theory
Read `docs/SATP_THEORY_PRIMER.md` for comprehensive background

### Explore High-Amplitude Dynamics
Read `docs/HIGH_AMPLITUDE_COMPARISON.md` for spectral studies

### Advanced Usage
See `docs/IGSOA_ANALYSIS_GUIDE.md` for detailed analysis options

### Development
Check `docs/FUTURE_ADDITIONS_ROADMAP.md` for extension ideas

---

## Quick Reference Card

| Task | Command |
|------|---------|
| **Run simulation** | `cat config.json \| ./dase_cli.exe > output.json` |
| **Analyze** | `python analyze_igsoa_state.py output.json 1.0 --output-dir results` |
| **Measure drift** | `python extract_drift.py output.json 2048` |
| **Run tests** | `cd tests && ./test_physics_validation.sh` |
| **Build CLI** | `cd dase_cli && ./rebuild.bat` |

---

## Example Output

### Successful Simulation

```json
{"command":"create_engine","status":"success","result":{"engine_id":"engine_001"}}
{"command":"set_igsoa_state","status":"success","result":{"applied":true}}
{"command":"run_mission","status":"success","result":{"steps_completed":10}}
{"command":"get_state","status":"success","result":{"num_nodes":4096,"psi_real":[...]}}
```

### Analysis Report (excerpt)

```
======================================================================
IGSOA STATE ANALYSIS REPORT
======================================================================
Number of nodes (N):        4096
Causal radius (R_c):        1.0

STATE STATISTICS
|Ψ|² mean:                   1.000000
Correlation length (ξ):     1 lattice sites
Ratio ξ/R_c:                1.000

✓ Correlation length validates R_c parameter
✓ State approximately normalized
======================================================================
```

### Drift Analysis (excerpt)

```
======================================================================
GAUSSIAN CENTER DRIFT ANALYSIS
======================================================================
Measured center:  2047.50
Initial center:   2048
Drift:            -0.50 nodes

[PASS] ZERO DRIFT CONFIRMED (drift < 41 nodes = 1% of N)
======================================================================
```

---

**Need Help?**

- Theory questions → `docs/SATP_THEORY_PRIMER.md`
- API reference → `docs/SET_IGSOA_STATE_MODES.md`
- Validation results → `docs/SATP_VALIDATION_REPORT.md`
- Implementation details → `docs/IMPLEMENTATION_SUMMARY.md`

---

**END OF QUICK START GUIDE**
