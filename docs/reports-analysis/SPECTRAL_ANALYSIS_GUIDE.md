# IGSOA Spectral Analysis Guide

**Date:** October 26, 2025
**Purpose:** Enable physics validation through spectral analysis of IGSOA quantum states

---

## Overview

The `get_state` command enables extraction of the complete quantum state $\Psi$ and realized field $\Phi$ from IGSOA engines, allowing rigorous spectral analysis to validate theoretical predictions about:

- Non-local causal coupling signatures
- Quantum coherence patterns
- Phase synchronization dynamics
- Informational entropy production
- Spectral imprints of the RH (Riemann Hypothesis) link

---

## Command Reference

### `get_state`

**Description:** Extract all node states from an IGSOA Complex engine for post-processing and spectral analysis.

**Input:**
```json
{
  "command": "get_state",
  "params": {
    "engine_id": "engine_001"
  }
}
```

**Output:**
```json
{
  "status": "success",
  "command": "get_state",
  "result": {
    "num_nodes": 256,
    "psi_real": [0.9997, 0.9997, ...],   // Real part of Ψ (N elements)
    "psi_imag": [-0.0229, -0.0223, ...],  // Imaginary part of Ψ (N elements)
    "phi": [32.846, 32.847, ...]          // Realized field Φ (N elements)
  },
  "execution_time_ms": 0.049
}
```

### Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `num_nodes` | integer | Number of nodes N in the system |
| `psi_real` | array[N] | Real part of quantum state Re[Ψ(x)] |
| `psi_imag` | array[N] | Imaginary part of quantum state Im[Ψ(x)] |
| `phi` | array[N] | Realized causal field Φ(x) |

---

## Spectral Analysis Workflow

### Step 1: Run IGSOA Mission

Create a mission file (e.g., `mission_spectral.json`) with appropriate parameters:

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":512,"R_c_default":2.0,"kappa":1.0,"gamma":0.1}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":500,"iterations_per_node":20}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
```

**Key Parameters:**
- `num_nodes`: Use powers of 2 for efficient FFT (256, 512, 1024, 2048)
- `R_c_default`: Causal radius controlling non-local coupling range
- `num_steps`: Evolution time steps (longer = more developed spectral features)

Run the mission:
```bash
cd dase_cli
./dase_cli.exe < mission_spectral.json > spectral_output.json 2>&1
```

### Step 2: Extract State Data

Parse the JSON output to extract the state arrays. Example Python script:

```python
import json
import numpy as np

# Read CLI output
with open('spectral_output.json', 'r') as f:
    lines = f.readlines()

# Find the get_state response (ignore diagnostic prints)
for line in lines:
    if '"command":"get_state"' in line:
        state_data = json.loads(line)
        break

# Extract arrays
result = state_data['result']
N = result['num_nodes']
psi_real = np.array(result['psi_real'])
psi_imag = np.array(result['psi_imag'])
phi = np.array(result['phi'])

# Construct complex wavefunction
psi = psi_real + 1j * psi_imag

print(f"Extracted state with N={N} nodes")
print(f"|Ψ|² range: [{np.min(np.abs(psi)**2):.6f}, {np.max(np.abs(psi)**2):.6f}]")
print(f"Φ range: [{np.min(phi):.6f}, {np.max(phi):.6f}]")
```

### Step 3: Compute Power Spectrum

Perform FFT to analyze spectral content:

```python
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# FFT of quantum state
psi_fft = fft(psi)
psi_power = np.abs(psi_fft)**2

# FFT of realized field
phi_fft = fft(phi - np.mean(phi))  # Remove DC component
phi_power = np.abs(phi_fft)**2

# Frequency axis
freq = fftfreq(N, d=1.0)  # Assuming spatial lattice spacing = 1

# Plot power spectra
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Ψ spectrum
ax1.semilogy(freq[:N//2], psi_power[:N//2])
ax1.set_xlabel('Spatial Frequency k')
ax1.set_ylabel('Power |Ψ̂(k)|²')
ax1.set_title('Quantum State Power Spectrum')
ax1.grid(True, alpha=0.3)

# Φ spectrum
ax2.semilogy(freq[:N//2], phi_power[:N//2])
ax2.set_xlabel('Spatial Frequency k')
ax2.set_ylabel('Power |Φ̂(k)|²')
ax2.set_title('Realized Field Power Spectrum')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('igsoa_power_spectra.png', dpi=300)
plt.show()
```

### Step 4: Analyze Spectral Features

#### 4.1 Non-Local Coupling Signature

The causal radius R_c should manifest as a characteristic decay length in k-space:

```python
# Expected: Power should decay beyond k ~ 1/R_c
k_cutoff = 1.0 / R_c_value  # From mission config

# Find spectral decay
k_positive = freq[:N//2]
spectral_decay_idx = np.where(k_positive > k_cutoff)[0]

if len(spectral_decay_idx) > 0:
    decay_start = spectral_decay_idx[0]
    decay_power = psi_power[decay_start:N//4]

    # Fit exponential decay
    from scipy.optimize import curve_fit

    def exp_decay(k, A, B, k0):
        return A * np.exp(-k / k0) + B

    k_fit = k_positive[decay_start:N//4]
    popt, _ = curve_fit(exp_decay, k_fit, decay_power[:len(k_fit)])

    print(f"Spectral decay length k₀ = {popt[2]:.4f}")
    print(f"Expected from R_c={R_c_value}: k₀ ~ {1/R_c_value:.4f}")
```

#### 4.2 Phase Coherence Length

Measure spatial correlation function:

```python
from scipy.signal import correlate

# Spatial autocorrelation of |Ψ|²
F = np.abs(psi)**2
F_corr = correlate(F - np.mean(F), F - np.mean(F), mode='same') / N

# Normalize
F_corr /= F_corr[N//2]

# Plot correlation
lags = np.arange(-N//2, N//2)
plt.figure(figsize=(10, 5))
plt.plot(lags, F_corr)
plt.xlabel('Spatial Lag Δx')
plt.ylabel('Correlation ⟨F(x)F(x+Δx)⟩')
plt.title(f'Spatial Correlation of Informational Density (R_c={R_c_value})')
plt.axvline(-R_c_value, color='r', linestyle='--', label=f'±R_c')
plt.axvline(R_c_value, color='r', linestyle='--')
plt.axhline(np.exp(-1), color='g', linestyle='--', label='e⁻¹ decay')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('spatial_correlation.png', dpi=300)
plt.show()

# Find correlation length
corr_decay_idx = np.where(F_corr[N//2:] < np.exp(-1))[0]
if len(corr_decay_idx) > 0:
    xi = corr_decay_idx[0]
    print(f"Correlation length ξ ≈ {xi} lattice sites")
    print(f"R_c = {R_c_value} (expected: ξ ~ R_c)")
```

#### 4.3 RH Spectral Signature (Advanced)

For validating predictions about Riemann Hypothesis connections, analyze peak structure:

```python
from scipy.signal import find_peaks

# Find spectral peaks in Ψ power spectrum
peaks, properties = find_peaks(psi_power[:N//4], height=np.median(psi_power[:N//4]))

peak_freqs = freq[peaks]
peak_powers = psi_power[peaks]

# Sort by power
sorted_idx = np.argsort(peak_powers)[::-1]
top_peaks = peaks[sorted_idx[:10]]  # Top 10 peaks

print("Top spectral peaks:")
print("k\t\t|Ψ̂(k)|²")
print("-" * 40)
for pk in top_peaks:
    print(f"{freq[pk]:.4f}\t\t{psi_power[pk]:.6e}")

# Plot peak locations
plt.figure(figsize=(10, 5))
plt.semilogy(freq[:N//2], psi_power[:N//2], alpha=0.5)
plt.scatter(freq[top_peaks], psi_power[top_peaks], c='r', s=100, marker='x', label='Top Peaks')
plt.xlabel('Spatial Frequency k')
plt.ylabel('Power |Ψ̂(k)|²')
plt.title('Spectral Peak Structure')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('spectral_peaks.png', dpi=300)
plt.show()
```

---

## Example: Complete Spectral Analysis Script

Here's a complete Python script for automated spectral analysis:

```python
#!/usr/bin/env python3
"""
IGSOA Spectral Analysis Script
Processes output from mission_spectral.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import correlate, find_peaks
from scipy.optimize import curve_fit
import sys

def load_state_from_json(filename):
    """Extract state arrays from CLI JSON output"""
    with open(filename, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if '"command":"get_state"' in line:
            state_data = json.loads(line)
            result = state_data['result']

            N = result['num_nodes']
            psi = np.array(result['psi_real']) + 1j * np.array(result['psi_imag'])
            phi = np.array(result['phi'])

            return N, psi, phi

    raise ValueError("No get_state response found in JSON output")

def compute_power_spectrum(signal, N):
    """Compute power spectrum via FFT"""
    signal_fft = fft(signal)
    power = np.abs(signal_fft)**2
    freq = fftfreq(N, d=1.0)
    return freq, power

def measure_correlation_length(F, N):
    """Measure spatial correlation length"""
    F_norm = F - np.mean(F)
    corr = correlate(F_norm, F_norm, mode='same') / N
    corr /= corr[N//2]

    # Find e^{-1} decay point
    decay_idx = np.where(corr[N//2:] < np.exp(-1))[0]
    if len(decay_idx) > 0:
        return decay_idx[0]
    return None

def main(json_file, R_c, output_prefix='igsoa_spectral'):
    print(f"Loading state from {json_file}...")
    N, psi, phi = load_state_from_json(json_file)

    print(f"Loaded N={N} nodes")
    print(f"R_c = {R_c}")
    print(f"|Ψ|² range: [{np.min(np.abs(psi)**2):.6f}, {np.max(np.abs(psi)**2):.6f}]")
    print(f"Φ range: [{np.min(phi):.6f}, {np.max(phi):.6f}]")
    print()

    # Compute power spectra
    print("Computing power spectra...")
    freq_psi, power_psi = compute_power_spectrum(psi, N)
    freq_phi, power_phi = compute_power_spectrum(phi - np.mean(phi), N)

    # Plot power spectra
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.semilogy(freq_psi[:N//2], power_psi[:N//2])
    ax1.axvline(1/R_c, color='r', linestyle='--', label=f'k ~ 1/R_c = {1/R_c:.3f}')
    ax1.set_xlabel('Spatial Frequency k')
    ax1.set_ylabel('Power |Ψ̂(k)|²')
    ax1.set_title(f'Quantum State Power Spectrum (R_c={R_c})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.semilogy(freq_phi[:N//2], power_phi[:N//2])
    ax2.set_xlabel('Spatial Frequency k')
    ax2.set_ylabel('Power |Φ̂(k)|²')
    ax2.set_title('Realized Field Power Spectrum')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_prefix}_power.png', dpi=300)
    print(f"Saved power spectra to {output_prefix}_power.png")

    # Spatial correlation
    print("\nComputing spatial correlation...")
    F = np.abs(psi)**2
    xi = measure_correlation_length(F, N)

    if xi:
        print(f"Correlation length ξ ≈ {xi} lattice sites")
        print(f"Expected from R_c: ξ ~ {R_c}")
        print(f"Ratio ξ/R_c = {xi/R_c:.3f}")

    # Find spectral peaks
    print("\nFinding spectral peaks...")
    peaks, _ = find_peaks(power_psi[:N//4], height=np.median(power_psi[:N//4]))

    if len(peaks) > 0:
        sorted_idx = np.argsort(power_psi[peaks])[::-1]
        top_peaks = peaks[sorted_idx[:5]]

        print("Top 5 spectral peaks:")
        print("k\t\t|Ψ̂(k)|²")
        print("-" * 40)
        for pk in top_peaks:
            print(f"{freq_psi[pk]:.4f}\t\t{power_psi[pk]:.6e}")

    print(f"\nAnalysis complete! Plots saved with prefix '{output_prefix}_'")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python spectral_analysis.py <json_file> <R_c> [output_prefix]")
        sys.exit(1)

    json_file = sys.argv[1]
    R_c = float(sys.argv[2])
    output_prefix = sys.argv[3] if len(sys.argv) > 3 else 'igsoa_spectral'

    main(json_file, R_c, output_prefix)
```

**Usage:**
```bash
# Run mission and save output
cd dase_cli
./dase_cli.exe < mission_spectral.json > spectral_output.json 2>&1

# Analyze
python spectral_analysis.py spectral_output.json 2.0 igsoa_R2
```

---

## Validation Tests

### Test 1: R_c Scaling

Run missions with different R_c values and verify spectral cutoff scales correctly:

```bash
# R_c = 1.0
./dase_cli.exe < mission_spectral_R1.json > output_R1.json 2>&1
python spectral_analysis.py output_R1.json 1.0 R1

# R_c = 2.0
./dase_cli.exe < mission_spectral_R2.json > output_R2.json 2>&1
python spectral_analysis.py output_R2.json 2.0 R2

# R_c = 4.0
./dase_cli.exe < mission_spectral_R4.json > output_R4.json 2>&1
python spectral_analysis.py output_R4.json 4.0 R4
```

**Expected:** Spectral cutoff k_c ≈ 1/R_c

### Test 2: System Size Convergence

Run with increasing N to verify spectral features converge:

```json
{"num_nodes": 256, ...}   // Coarse
{"num_nodes": 512, ...}   // Medium
{"num_nodes": 1024, ...}  // Fine
{"num_nodes": 2048, ...}  // Very fine
```

**Expected:** Peak locations should stabilize for N ≥ 512

### Test 3: Evolution Time

Run with different num_steps to observe spectral development:

```json
{"num_steps": 50, ...}    // Early time
{"num_steps": 200, ...}   // Medium time
{"num_steps": 500, ...}   // Long time
{"num_steps": 1000, ...}  // Very long time
```

**Expected:** Spectral features sharpen and stabilize with longer evolution

---

## Theoretical Predictions to Validate

### 1. Non-Local Coupling Signature

**Prediction:** Power spectrum should exhibit exponential decay for k > 1/R_c:

$|\\hat{\\Psi}(k)|^2 \\sim \\exp(-k/k_0)$ where $k_0 \\sim 1/R_c$

**Test:** Fit exponential to high-k tail and verify $k_0 \\approx 1/R_c$

### 2. Correlation Length Scaling

**Prediction:** Spatial correlation function should decay as:

$C(r) = \\langle F(x) F(x+r) \\rangle \\sim \\exp(-r/\\xi)$ where $\\xi \\sim R_c$

**Test:** Measure correlation length and verify $\\xi / R_c \\approx 1$

### 3. Φ-Ψ Phase Relationship

**Prediction:** Realized field should lag quantum state by phase shift:

$\\Phi(x) \\sim \\text{Re}[\\Psi(x - \\delta x)]$ where $\\delta x \\sim 1/\\kappa$

**Test:** Cross-correlate Φ and Re[Ψ] to measure phase lag

### 4. Entropy Production Scaling

**Prediction:** Total entropy production rate should scale as:

$\\dot{S}_{\\text{total}} \\sim N \\times R_c \\times (\\Phi - \\text{Re}[\\Psi])^2$

**Test:** Compute from state arrays and verify R_c dependence

---

## Files

| File | Purpose |
|------|---------|
| `mission_spectral.json` | Mission definition for spectral analysis |
| `spectral_output.json` | Raw CLI output with state data |
| `spectral_analysis.py` | Python analysis script |
| `igsoa_spectral_power.png` | Power spectrum plots |
| `spatial_correlation.png` | Correlation function plot |
| `spectral_peaks.png` | Peak structure visualization |

---

## Next Steps

1. **Run systematic R_c scan** with R_c ∈ [0.5, 1.0, 2.0, 4.0, 8.0]
2. **Compare with theoretical predictions** from IGSOA papers
3. **Publish spectral signatures** as physics validation
4. **Search for RH-related peak structures** in large-N simulations

---

## Summary

The `get_state` command provides complete access to IGSOA quantum states, enabling:

✅ **FFT-based spectral analysis** of Ψ and Φ
✅ **Spatial correlation measurements** to verify R_c effects
✅ **Peak structure analysis** for theoretical validation
✅ **Physics-driven validation** of IGSOA framework predictions

This transforms DASE from a computational benchmark into a **scientific instrument** for exploring quantum-classical hybrid dynamics and testing fundamental physics predictions.
