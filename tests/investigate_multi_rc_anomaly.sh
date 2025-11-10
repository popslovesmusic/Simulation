#!/bin/bash
# Multi-R_c Anomaly Investigation Suite
# Tests three hypotheses:
# 1. Discretization limit (ξ cannot resolve below 1 lattice site)
# 2. Measurement artifact (exponential fit inappropriate)
# 3. Early-time effect (structure not yet developed at T=1)

set -e

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$TEST_DIR")"
CLI_DIR="${ROOT_DIR}/dase_cli"

echo "======================================================================="
echo "MULTI-R_c ANOMALY INVESTIGATION"
echo "======================================================================="
echo "Testing hypotheses for why ξ ≈ 1 site for all R_c ≠ 1.0"
echo "======================================================================="
echo

cd "${CLI_DIR}" || exit 1

# Test parameters
AMPLITUDE=100.0
BASELINE_PHI=0.0
MODE="blend"
BETA=1.0
ITERATIONS=30

# R_c values to test
RC_VALUES=(0.5 1.0 2.0 5.0 10.0)

# ============================================================================
# HYPOTHESIS 1: Discretization Limit (Finer Lattice)
# ============================================================================

echo "-----------------------------------------------------------------------"
echo "HYPOTHESIS 1: Discretization Limit"
echo "-----------------------------------------------------------------------"
echo "Testing with 2× lattice density (N=8192 vs N=4096)"
echo

for RC in "${RC_VALUES[@]}"; do
    echo "=== R_c = $RC (Fine Lattice N=8192) ==="

    CENTER=4096
    WIDTH=512  # 2× the width for fine lattice

    cat > test_fine_Rc${RC}.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":8192,"R_c":${RC}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":${AMPLITUDE},"center_node":${CENTER},"width":${WIDTH},"baseline_phi":${BASELINE_PHI},"mode":"${MODE}","beta":${BETA}}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1,"iterations_per_node":${ITERATIONS}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    cat test_fine_Rc${RC}.json | ./dase_cli.exe > output_fine_Rc${RC}_t1.json 2>&1

    # Analyze
    python analyze_igsoa_state.py output_fine_Rc${RC}_t1.json ${RC} --output-dir analysis_fine_Rc${RC}_t1 > /dev/null 2>&1

    # Extract ξ/R_c ratio
    XI_RC=$(grep "Ratio ξ/R_c:" analysis_fine_Rc${RC}_t1/analysis_report_R${RC}.txt | awk '{print $NF}')

    echo "Fine lattice (N=8192): ξ/R_c = $XI_RC"
done

echo

# ============================================================================
# HYPOTHESIS 2: Measurement Artifact (Multiple Times)
# ============================================================================

echo "-----------------------------------------------------------------------"
echo "HYPOTHESIS 2: Early-Time Effect"
echo "-----------------------------------------------------------------------"
echo "Testing evolution at T=1,2,3,5,10 for R_c=0.5 and R_c=5.0"
echo

# Test R_c = 0.5 at multiple times
RC=0.5
CENTER=2048
WIDTH=256
NUM_NODES=4096

for T in 1 2 3 5 10; do
    echo "=== R_c = $RC, T = $T ==="

    cat > test_time_Rc${RC}_t${T}.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":${NUM_NODES},"R_c":${RC}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":${AMPLITUDE},"center_node":${CENTER},"width":${WIDTH},"baseline_phi":${BASELINE_PHI},"mode":"${MODE}","beta":${BETA}}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":${T},"iterations_per_node":${ITERATIONS}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    cat test_time_Rc${RC}_t${T}.json | ./dase_cli.exe > output_time_Rc${RC}_t${T}.json 2>&1

    # Analyze
    python analyze_igsoa_state.py output_time_Rc${RC}_t${T}.json ${RC} --output-dir analysis_time_Rc${RC}_t${T} > /dev/null 2>&1

    # Extract ξ/R_c ratio
    XI_RC=$(grep "Ratio ξ/R_c:" analysis_time_Rc${RC}_t${T}/analysis_report_R${RC}.txt | awk '{print $NF}')

    echo "T=$T: ξ/R_c = $XI_RC"
done

echo

# Test R_c = 5.0 at multiple times
RC=5.0

for T in 1 2 3 5 10; do
    echo "=== R_c = $RC, T = $T ==="

    cat > test_time_Rc${RC}_t${T}.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":${NUM_NODES},"R_c":${RC}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":${AMPLITUDE},"center_node":${CENTER},"width":${WIDTH},"baseline_phi":${BASELINE_PHI},"mode":"${MODE}","beta":${BETA}}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":${T},"iterations_per_node":${ITERATIONS}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    cat test_time_Rc${RC}_t${T}.json | ./dase_cli.exe > output_time_Rc${RC}_t${T}.json 2>&1

    # Analyze
    python analyze_igsoa_state.py output_time_Rc${RC}_t${T}.json ${RC} --output-dir analysis_time_Rc${RC}_t${T} > /dev/null 2>&1

    # Extract ξ/R_c ratio
    XI_RC=$(grep "Ratio ξ/R_c:" analysis_time_Rc${RC}_t${T}/analysis_report_R${RC}.txt | awk '{print $NF}')

    echo "T=$T: ξ/R_c = $XI_RC"
done

echo

# ============================================================================
# HYPOTHESIS 3: Autocorrelation Function Analysis
# ============================================================================

echo "-----------------------------------------------------------------------"
echo "HYPOTHESIS 3: Alternative Correlation Metric"
echo "-----------------------------------------------------------------------"
echo "Computing autocorrelation for all R_c values at T=1"
echo

# Create Python script for autocorrelation analysis
cat > compute_autocorrelation.py <<'PYEOF'
#!/usr/bin/env python3
"""
Compute autocorrelation function and extract correlation length
using multiple fitting methods.
"""

import json
import numpy as np
import sys
from scipy.optimize import curve_fit
from scipy.signal import correlate

def exponential_decay(x, xi):
    """Exponential decay: exp(-x/ξ)"""
    return np.exp(-x / xi)

def power_law_decay(x, xi, alpha):
    """Power law decay: (1 + x/ξ)^(-α)"""
    return (1 + x / xi)**(-alpha)

def compute_autocorrelation(psi_real, psi_imag):
    """Compute autocorrelation of |Ψ|²"""
    F = psi_real**2 + psi_imag**2
    F = F - np.mean(F)  # Remove DC component

    # Compute autocorrelation using FFT
    autocorr = correlate(F, F, mode='same', method='fft')
    autocorr = autocorr / autocorr[len(autocorr)//2]  # Normalize to 1 at zero lag

    # Take positive lags only
    N = len(F)
    lags = np.arange(0, N//2)
    autocorr_positive = autocorr[N//2:]

    return lags, autocorr_positive

def fit_exponential(lags, autocorr, max_lag=100):
    """Fit exponential decay to extract ξ"""
    # Use only first max_lag points
    mask = lags < max_lag
    x_fit = lags[mask]
    y_fit = autocorr[mask]

    # Remove non-positive values
    positive_mask = y_fit > 0
    x_fit = x_fit[positive_mask]
    y_fit = y_fit[positive_mask]

    if len(x_fit) < 10:
        return None, None

    try:
        # Fit exponential
        popt, _ = curve_fit(exponential_decay, x_fit, y_fit, p0=[10.0], maxfev=10000)
        xi = popt[0]

        # Compute R²
        y_pred = exponential_decay(x_fit, xi)
        ss_res = np.sum((y_fit - y_pred)**2)
        ss_tot = np.sum((y_fit - np.mean(y_fit))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return xi, r_squared
    except:
        return None, None

def fit_power_law(lags, autocorr, max_lag=100):
    """Fit power law decay to extract ξ"""
    mask = lags < max_lag
    x_fit = lags[mask]
    y_fit = autocorr[mask]

    # Remove non-positive values
    positive_mask = y_fit > 0
    x_fit = x_fit[positive_mask]
    y_fit = y_fit[positive_mask]

    if len(x_fit) < 10:
        return None, None, None

    try:
        # Fit power law
        popt, _ = curve_fit(power_law_decay, x_fit, y_fit, p0=[10.0, 2.0], maxfev=10000)
        xi, alpha = popt

        # Compute R²
        y_pred = power_law_decay(x_fit, xi, alpha)
        ss_res = np.sum((y_fit - y_pred)**2)
        ss_tot = np.sum((y_fit - np.mean(y_fit))**2)
        r_squared = 1 - (ss_res / ss_tot)

        return xi, alpha, r_squared
    except:
        return None, None, None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: compute_autocorrelation.py <input.json> <R_c>")
        sys.exit(1)

    input_file = sys.argv[1]
    R_c = float(sys.argv[2])

    # Load state
    with open(input_file, 'r') as f:
        lines = f.readlines()

    state = None
    for line in lines:
        try:
            data = json.loads(line)
            if data.get('command') == 'get_state' and data.get('status') == 'success':
                state = data['result']
                break
        except:
            continue

    if state is None:
        print("ERROR: No valid get_state response found")
        sys.exit(1)

    psi_real = np.array(state['psi_real'])
    psi_imag = np.array(state['psi_imag'])

    # Compute autocorrelation
    lags, autocorr = compute_autocorrelation(psi_real, psi_imag)

    # Fit exponential
    xi_exp, r2_exp = fit_exponential(lags, autocorr)

    # Fit power law
    xi_pow, alpha, r2_pow = fit_power_law(lags, autocorr)

    # Print results
    print(f"R_c = {R_c}")
    print(f"Exponential fit: ξ = {xi_exp:.3f}, R² = {r2_exp:.4f}" if xi_exp else "Exponential fit: FAILED")
    print(f"Power law fit: ξ = {xi_pow:.3f}, α = {alpha:.3f}, R² = {r2_pow:.4f}" if xi_pow else "Power law fit: FAILED")

    if xi_exp:
        print(f"ξ/R_c (exponential) = {xi_exp/R_c:.3f}")
    if xi_pow:
        print(f"ξ/R_c (power law) = {xi_pow/R_c:.3f}")
PYEOF

chmod +x compute_autocorrelation.py

for RC in "${RC_VALUES[@]}"; do
    echo "=== R_c = $RC (Autocorrelation Analysis) ==="
    python compute_autocorrelation.py output_Rc${RC}_t1.json ${RC} 2>&1 || true
    echo
done

# ============================================================================
# SUMMARY
# ============================================================================

echo "======================================================================="
echo "INVESTIGATION COMPLETE"
echo "======================================================================="
echo
echo "Generated files:"
echo "  - Fine lattice outputs: output_fine_Rc*_t1.json"
echo "  - Time evolution outputs: output_time_Rc*_t*.json"
echo "  - Autocorrelation analysis: (printed above)"
echo
echo "Next steps:"
echo "  1. Review fine lattice results to check if ξ can resolve below 1 site"
echo "  2. Check time evolution to see if ξ develops over time"
echo "  3. Compare exponential vs power-law fits"
echo "======================================================================="

# Cleanup temporary test files
rm -f test_fine_Rc*.json
rm -f test_time_Rc*.json
