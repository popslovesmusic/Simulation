# IGSOA State Analysis Guide

**Complete Documentation for Analyzing IGSOA Simulation Data**

Version: 1.0
Last Updated: November 2, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation & Requirements](#installation--requirements)
3. [Workflow Overview](#workflow-overview)
4. [Command Reference](#command-reference)
5. [Understanding the Outputs](#understanding-the-outputs)
6. [Analysis Features Explained](#analysis-features-explained)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)
9. [Examples & Tutorials](#examples--tutorials)

---

## Quick Start

### 1. Run a Simulation with State Extraction

```bash
cd dase_cli

# Create your simulation configuration
cat > my_simulation.json << 'EOF'
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

# Run simulation and save output
cat my_simulation.json | ./dase_cli.exe > output.json
```

### 2. Analyze the Results

```bash
# Basic analysis (R_c = 1.0 in this example)
python ../analyze_igsoa_state.py output.json 1.0

# Analysis complete! Check the 'igsoa_analysis' folder for results
```

### 3. View Results

Check the `igsoa_analysis/` directory for:
- `analysis_report_R1.0.txt` - Full text report
- `power_spectra_R1.0.png` - Frequency domain analysis
- `spatial_correlation_R1.0.png` - Correlation functions
- `state_profiles_R1.0.png` - Real-space state visualization

---

## Installation & Requirements

### Prerequisites

```bash
# Required Python packages
pip install numpy scipy matplotlib

# Verify installation
python -c "import numpy, scipy, matplotlib; print('All packages installed!')"
```

### System Requirements

- **Python**: 3.7 or higher
- **RAM**: ~200 MB for 4096-node simulations
- **Disk**: ~10 MB per analysis run (plots + reports)

---

## Workflow Overview

```
┌─────────────────┐
│  1. Configure   │  Create JSON with commands including
│   Simulation    │  get_state to extract final state
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. Run CLI     │  cat config.json | dase_cli.exe > output.json
│   Simulation    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. Analyze     │  python analyze_igsoa_state.py output.json <R_c>
│   Output        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Inspect     │  View plots and reports in output directory
│   Results       │
└─────────────────┘
```

---

## Command Reference

### Basic Syntax

```bash
python analyze_igsoa_state.py <json_file> <R_c> [options]
```

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `json_file` | Path to CLI output JSON | `output.json` |
| `R_c` | Causal radius used in simulation | `1.0`, `2.5`, `10.0` |

### Optional Arguments

| Option | Default | Description |
|--------|---------|-------------|
| `--output-dir DIR` | `igsoa_analysis` | Output directory for results |
| `--plot-format FMT` | `png` | Format: `png`, `pdf`, or `svg` |
| `--dpi DPI` | `300` | Plot resolution (72-600 typical) |
| `--no-plots` | `false` | Skip plot generation (report only) |
| `--verbose` | `false` | Enable detailed console output |
| `--timestamp` | `false` | Add timestamp to output directory |

### Examples

```bash
# Standard analysis
python analyze_igsoa_state.py results.json 2.0

# High-resolution PDF output
python analyze_igsoa_state.py results.json 2.0 --plot-format pdf --dpi 600

# Custom output directory
python analyze_igsoa_state.py results.json 1.5 --output-dir my_analysis

# Timestamped output (for batch processing)
python analyze_igsoa_state.py results.json 1.0 --timestamp

# Report only (no plots, fast)
python analyze_igsoa_state.py results.json 1.0 --no-plots

# Verbose mode (see detailed progress)
python analyze_igsoa_state.py results.json 1.0 --verbose
```

---

## Understanding the Outputs

### 1. Analysis Report (`analysis_report_R*.txt`)

A comprehensive text file with:

#### System Parameters
- Number of nodes (N)
- Causal radius (R_c)

#### State Statistics
```
|Ψ|² mean:       1.000000      # Average informational density
|Ψ|² std dev:    0.123456      # Spatial variation
|Ψ|² range:      [0.5, 1.8]    # Min/max values

Φ mean:          -60.840009    # Average realized field
Φ std dev:       0.000066      # Field fluctuations
Φ range:         [-61.2, -60.4]

Phase mean:      -2.299 rad    # Average quantum phase
Phase std dev:   0.000045 rad  # Phase coherence
```

#### Spectral Analysis
```
Spectral decay length (k₀):  0.9876    # Measured from FFT
Expected (1/R_c):            1.0000    # Theoretical prediction
Ratio k₀/(1/R_c):            0.988     # Validation check
```

#### Spatial Correlation
```
Correlation length (ξ):      12 lattice sites
Ratio ξ/R_c:                 1.200
```

#### Physics Validation
- ✓ = Passed validation
- ✗ = Failed validation
- ? = Could not measure

### 2. Power Spectra Plot (`power_spectra_R*.png`)

**Top Panel: Quantum State |Ψ̂(k)|²**
- X-axis: Spatial frequency k
- Y-axis: Power (log scale)
- Red dashed line: k ~ 1/R_c (expected cutoff)
- Red X marks: Top spectral peaks

**Interpretation:**
- Sharp peak at k=0: DC component (mean state)
- Decay beyond k ~ 1/R_c: Non-local cutoff
- Multiple peaks: Characteristic spatial modes
- Flat tail: Numerical noise floor

**Bottom Panel: Realized Field |Φ̂(k)|²**
- Similar interpretation for Φ field
- Usually more smooth than Ψ spectrum

### 3. Spatial Correlation Plot (`spatial_correlation_R*.png`)

Shows autocorrelation: ⟨F(x)F(x+Δx)⟩

- X-axis: Spatial lag Δx (lattice sites)
- Y-axis: Normalized correlation
- Orange dashed line: e⁻¹ decay threshold
- Red vertical lines: ±R_c bounds
- Green vertical line: Measured correlation length ξ

**Interpretation:**
- Peak at Δx=0: Perfect self-correlation
- Width ~ ξ: Correlation length
- ξ ≈ R_c: System obeys causal structure
- Long-range tail: Non-local effects

### 4. State Profiles Plot (`state_profiles_R*.png`)

**Top Panel: Informational Density F = |Ψ|²**
- Spatial distribution of quantum probability
- Gaussian → spreading → equilibration

**Middle Panel: Phase arg(Ψ)**
- Phase angle of quantum state
- Uniform phase → coherent state
- Random phase → decoherent state

**Bottom Panel: Realized Field Φ**
- Classical field configuration
- Coupled to Ψ via κ parameter
- Shows dissipation effects

---

## Analysis Features Explained

### 1. Power Spectrum Analysis (FFT)

**What it does:**
Decomposes spatial state into frequency components using Fast Fourier Transform.

**Why it matters:**
- Reveals characteristic length scales
- Validates R_c parameter via spectral cutoff
- Identifies dominant spatial modes

**Mathematical basis:**
```
Ψ̂(k) = FFT[Ψ(x)]
Power(k) = |Ψ̂(k)|²
```

**Expected behavior:**
```
Power(k) ~ {  High         for k < 1/R_c
           {  Exponential  for k > 1/R_c
           {  decay
```

### 2. Spatial Correlation Function

**What it does:**
Measures how strongly nodes at different distances are correlated.

**Why it matters:**
- Quantifies information spreading
- Measures effective interaction range
- Validates causal structure

**Mathematical basis:**
```
C(Δx) = ⟨F(x) F(x+Δx)⟩ / ⟨F²⟩
```

**Correlation length ξ:**
Distance where C(ξ) = e⁻¹ ≈ 0.368

**Expected result:**
ξ ≈ R_c (within 30%)

### 3. Spectral Decay Length

**What it does:**
Fits exponential decay to high-frequency tail:
```
Power(k) = A exp(-k/k₀) + B
```

**Why it matters:**
Independent validation of R_c via frequency domain.

**Expected result:**
k₀ ≈ 1/R_c

### 4. Peak Detection

**What it does:**
Finds prominent peaks in power spectrum.

**Why it matters:**
- Identifies resonant modes
- Shows system's natural frequencies
- Can indicate instabilities or wave patterns

**Threshold:**
Peaks must be above median power level.

### 5. Φ-Ψ Coupling Analysis

**What it does:**
Computes cross-correlation between Φ and Re[Ψ].

**Why it matters:**
- Measures strength of κ coupling
- Detects phase lags (causality)
- Validates coupled dynamics

**Interpretation:**
- Peak at lag=0: Synchronous coupling
- Peak at lag≠0: Delayed response

---

## Advanced Usage

### Batch Processing Multiple Runs

```bash
#!/bin/bash
# analyze_batch.sh - Process multiple R_c values

for Rc in 0.5 1.0 2.0 5.0 10.0; do
    echo "Analyzing R_c = $Rc..."

    # Generate simulation
    cat > sim_Rc${Rc}.json << EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096,"R_c":${Rc}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    # Run simulation
    cat sim_Rc${Rc}.json | ./dase_cli.exe > output_Rc${Rc}.json

    # Analyze
    python ../analyze_igsoa_state.py output_Rc${Rc}.json ${Rc} \
        --output-dir analysis_Rc${Rc} \
        --plot-format pdf --dpi 300
done

echo "Batch analysis complete!"
```

### Comparing Multiple Timesteps

```python
#!/usr/bin/env python3
"""Compare evolution across timesteps"""

import matplotlib.pyplot as plt
import json
import numpy as np

timesteps = [100, 200, 500, 1000]
R_c = 1.0

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

for idx, t in enumerate(timesteps):
    ax = axes[idx // 2, idx % 2]

    # Load state data
    with open(f'output_t{t}.json', 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('command') == 'get_state':
                    psi_real = np.array(data['result']['psi_real'])
                    psi_imag = np.array(data['result']['psi_imag'])
                    F = psi_real**2 + psi_imag**2

                    ax.plot(F, label=f't={t}')
                    ax.set_title(f'Timestep {t}')
                    ax.set_xlabel('Lattice Site')
                    ax.set_ylabel('|Ψ|²')
                    ax.grid(True, alpha=0.3)
                    break
            except json.JSONDecodeError:
                continue

plt.tight_layout()
plt.savefig('evolution_comparison.png', dpi=300)
print("Comparison plot saved!")
```

### Custom Analysis Script

```python
#!/usr/bin/env python3
"""Custom analysis: Measure entropy production"""

from analyze_igsoa_state import IGSOAStateAnalyzer
import numpy as np

# Load data
analyzer = IGSOAStateAnalyzer('output.json', R_c=1.0)

# Compute entropy density
F = analyzer.F
phi = analyzer.phi

# Von Neumann entropy (if normalized)
entropy = -np.sum(F * np.log(F + 1e-10))

# Classical field entropy
phi_prob = (phi - np.min(phi)) / (np.max(phi) - np.min(phi))
classical_entropy = -np.sum(phi_prob * np.log(phi_prob + 1e-10))

print(f"Quantum entropy: {entropy:.4f}")
print(f"Classical entropy: {classical_entropy:.4f}")
print(f"Total entropy: {entropy + classical_entropy:.4f}")
```

---

## Troubleshooting

### Problem: "No valid get_state response found"

**Cause:** JSON file doesn't contain `get_state` command output.

**Solution:**
```bash
# Make sure your simulation includes get_state:
{"command":"get_state","params":{"engine_id":"engine_001"}}
```

### Problem: "Spectral decay length: NOT MEASURED"

**Cause:** Insufficient data points in high-frequency region for fitting.

**Solutions:**
1. Use larger N (more nodes)
2. Use smaller R_c (wider k-space coverage)
3. This is normal for very uniform states

### Problem: "No significant peaks found"

**Cause:** State is very smooth (e.g., fully equilibrated).

**Interpretation:** Not an error! Means system has no resonant modes.

### Problem: Font warnings in console

**Cause:** Matplotlib can't find "Computer Modern Roman" font.

**Solutions:**
1. Ignore (plots still work, uses fallback font)
2. Install LaTeX fonts
3. Edit `analyze_igsoa_state.py` line 56: Set `text.usetex = False`

### Problem: High memory usage

**Cause:** Large N (many nodes).

**Solutions:**
```bash
# Use --no-plots to skip visualization
python analyze_igsoa_state.py large_data.json 1.0 --no-plots

# Process in chunks (custom script needed)
```

### Problem: Plots look different on Windows vs Linux

**Cause:** Different default matplotlib backends.

**Solution:** Specify backend explicitly:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
```

---

## Examples & Tutorials

### Example 1: Gaussian Wave Packet Spreading

**Objective:** Measure how fast a localized wavepacket spreads.

```bash
# 1. Create simulation with Gaussian initial state
cat > gaussian_spread.json << 'EOF'
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":2.0,"center_node":2048,"width":100,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1000,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

# 2. Run simulation
cat gaussian_spread.json | ./dase_cli.exe > gaussian_output.json

# 3. Analyze
python ../analyze_igsoa_state.py gaussian_output.json 1.0 --verbose

# 4. Check correlation length in report
# If ξ > initial width (100), wave packet has spread!
```

### Example 2: R_c Validation Study

**Objective:** Verify that correlation length scales with R_c.

```bash
# Test multiple R_c values
for Rc in 1.0 2.0 5.0 10.0; do
    # Create engine with specific R_c
    cat > validate_Rc${Rc}.json << EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096,"R_c":${Rc}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"uniform","params":{"psi_real":0.5,"psi_imag":0.5,"phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":200,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    cat validate_Rc${Rc}.json | ./dase_cli.exe > out_Rc${Rc}.json
    python ../analyze_igsoa_state.py out_Rc${Rc}.json ${Rc} \
        --output-dir validation_Rc${Rc}
done

# Compare ξ/R_c ratios across all reports
grep "Ratio ξ/R_c" validation_*/analysis_report_*.txt
```

Expected output:
```
validation_Rc1.0/analysis_report_R1.0.txt:Ratio ξ/R_c:  0.950
validation_Rc2.0/analysis_report_R2.0.txt:Ratio ξ/R_c:  1.020
validation_Rc5.0/analysis_report_R5.0.txt:Ratio ξ/R_c:  0.985
validation_Rc10.0/analysis_report_R10.0.txt:Ratio ξ/R_c: 1.005
```
✓ All ratios ≈ 1.0, R_c is correctly implemented!

### Example 3: Long-Time Equilibration

**Objective:** Track system evolution to equilibrium.

```bash
# Run simulations at multiple timesteps
for t in 100 200 500 1000 2000; do
    cat > equilibrate_t${t}.json << EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":5.0,"center_node":2048,"width":50,"baseline_phi":0.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":${t},"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    cat equilibrate_t${t}.json | ./dase_cli.exe > state_t${t}.json
    python ../analyze_igsoa_state.py state_t${t}.json 1.0 \
        --output-dir equilibrium_t${t}
done

# Compare state profiles over time
# Plots show: peaked → spreading → flat (equilibrium)
```

### Example 4: Publication-Quality Figures

**Objective:** Generate high-resolution figures for papers.

```bash
# Run analysis with PDF output at 600 DPI
python analyze_igsoa_state.py my_data.json 2.5 \
    --output-dir figures_paper \
    --plot-format pdf \
    --dpi 600

# Plots are now publication-ready!
# Use in LaTeX:
# \includegraphics{figures_paper/power_spectra_R2.5.pdf}
```

### Example 5: Scripted Parameter Scan

```python
#!/usr/bin/env python3
"""Automated parameter scan and analysis"""

import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt

# Parameter ranges
amplitudes = [0.5, 1.0, 2.0, 5.0]
widths = [50, 100, 200, 400]

results = []

for amp in amplitudes:
    for width in widths:
        # Create simulation
        config = [
            {"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096}},
            {"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian",
             "params":{"amplitude":amp,"center_node":2048,"width":width,"baseline_phi":0.0}}},
            {"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":30}},
            {"command":"get_state","params":{"engine_id":"engine_001"}},
            {"command":"destroy_engine","params":{"engine_id":"engine_001"}}
        ]

        # Write config
        with open('temp_config.json', 'w') as f:
            for cmd in config:
                f.write(json.dumps(cmd) + '\n')

        # Run simulation
        with open('temp_config.json', 'r') as f:
            result = subprocess.run(['./dase_cli.exe'], stdin=f,
                                  capture_output=True, text=True)

        output_file = f'scan_A{amp}_W{width}.json'
        with open(output_file, 'w') as f:
            f.write(result.stdout)

        # Analyze
        subprocess.run(['python', '../analyze_igsoa_state.py', output_file, '1.0',
                       '--output-dir', f'scan_A{amp}_W{width}',
                       '--no-plots'])

        # Extract key metric (correlation length)
        report_file = f'scan_A{amp}_W{width}/analysis_report_R1.0.txt'
        with open(report_file, 'r') as f:
            for line in f:
                if 'Correlation length' in line and 'lattice sites' in line:
                    xi = float(line.split(':')[1].split()[0])
                    results.append({'amp': amp, 'width': width, 'xi': xi})

# Plot results
fig, ax = plt.subplots()
for amp in amplitudes:
    data = [r for r in results if r['amp'] == amp]
    widths_plot = [d['width'] for d in data]
    xis = [d['xi'] for d in data]
    ax.plot(widths_plot, xis, 'o-', label=f'A={amp}')

ax.set_xlabel('Initial Width')
ax.set_ylabel('Final Correlation Length ξ')
ax.legend()
ax.grid(True, alpha=0.3)
plt.savefig('parameter_scan_results.png', dpi=300)
print("Parameter scan complete! See parameter_scan_results.png")
```

---

## Additional Resources

### Related Files
- `analyze_igsoa_state.py` - Main analysis script
- `SPECTRAL_ANALYSIS_GUIDE.md` - Detailed FFT theory
- `dase_cli/USAGE.md` - CLI command reference

### Physics Background
The analysis validates IGSOA theory predictions:
1. **Non-local cutoff**: Information propagation limited by R_c
2. **Φ-Ψ coupling**: Realized field follows quantum state
3. **Dissipation**: γ parameter controls equilibration

### Support
- GitHub Issues: Report bugs or request features
- Example data: See `examples/` directory
- Forum: Community discussions

---

**End of Analysis Guide**
