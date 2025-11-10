#!/usr/bin/env python3
"""
Extract Gaussian Center Drift from IGSOA State Data

Given mode C (overwrite) semantics:
- Initial: Ψ has Gaussian shape, Φ = 0.0 (baseline)
- After evolution: Φ develops structure from Ψ-Φ coupling
- Center extraction: Find center of mass of Φ field

This measures translation drift in the realized field.
"""

import json
import numpy as np
import sys

def load_state_from_json(json_file):
    """Extract state arrays from CLI output JSON"""
    with open(json_file, 'r') as f:
        lines = f.readlines()

    for line in lines:
        try:
            data = json.loads(line)
            if data.get('command') == 'get_state' and data.get('status') == 'success':
                result = data['result']
                N = result['num_nodes']
                psi_real = np.array(result['psi_real'])
                psi_imag = np.array(result['psi_imag'])
                phi = np.array(result['phi'])

                return N, psi_real, psi_imag, phi
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid get_state response found in {json_file}")


def compute_center_of_mass(field, method='absolute'):
    """
    Compute center of mass of field

    Methods:
    - 'absolute': Use |field| (for fields with arbitrary offset)
    - 'squared': Use field² (for positive-definite densities)
    - 'raw': Use raw field values (assumes positive or symmetric)
    """
    N = len(field)
    x = np.arange(N)

    if method == 'absolute':
        weights = np.abs(field)
    elif method == 'squared':
        weights = field**2
    elif method == 'raw':
        weights = field
    else:
        raise ValueError(f"Unknown method: {method}")

    # Normalize weights
    total_weight = np.sum(weights)
    if total_weight < 1e-12:
        return None  # No structure

    weights_norm = weights / total_weight

    # Center of mass
    x_cm = np.sum(x * weights_norm)

    return x_cm


def compute_center_from_peak(field):
    """Find center by locating maximum value"""
    return np.argmax(np.abs(field))


def analyze_drift(json_file, initial_center=2048, verbose=True):
    """
    Analyze drift of Gaussian center from initial to final state

    Args:
        json_file: Path to output.json from dase_cli
        initial_center: Expected initial center node
        verbose: Print detailed output

    Returns:
        dict with drift analysis results
    """
    # Load data
    N, psi_real, psi_imag, phi = load_state_from_json(json_file)

    # Compute |Ψ|² (informational density)
    F = psi_real**2 + psi_imag**2

    # Compute centers using different methods
    results = {
        'N': N,
        'initial_center': initial_center,
        'methods': {}
    }

    # Method 1: Center of mass of |Ψ|²
    cm_psi_squared = compute_center_of_mass(F, method='squared')
    results['methods']['psi_squared_cm'] = cm_psi_squared

    # Method 2: Center of mass of |Φ|
    cm_phi_abs = compute_center_of_mass(phi, method='absolute')
    results['methods']['phi_abs_cm'] = cm_phi_abs

    # Method 3: Center of mass of Φ² (if Φ has structure)
    cm_phi_squared = compute_center_of_mass(phi, method='squared')
    results['methods']['phi_squared_cm'] = cm_phi_squared

    # Method 4: Peak detection
    peak_psi = compute_center_from_peak(F)
    results['methods']['psi_peak'] = peak_psi

    peak_phi = compute_center_from_peak(phi)
    results['methods']['phi_peak'] = peak_phi

    # Compute drifts
    results['drifts'] = {}
    for method_name, center in results['methods'].items():
        if center is not None:
            drift = center - initial_center
            results['drifts'][method_name] = drift
        else:
            results['drifts'][method_name] = None

    # Statistics
    results['stats'] = {
        'psi_mean': np.mean(F),
        'psi_std': np.std(F),
        'psi_min': np.min(F),
        'psi_max': np.max(F),
        'phi_mean': np.mean(phi),
        'phi_std': np.std(phi),
        'phi_min': np.min(phi),
        'phi_max': np.max(phi),
    }

    if verbose:
        print("=" * 70)
        print("GAUSSIAN CENTER DRIFT ANALYSIS")
        print("=" * 70)
        print(f"\nFile: {json_file}")
        print(f"Nodes: {N}")
        print(f"Initial center (expected): {initial_center}")
        print()

        print("-" * 70)
        print("STATE STATISTICS")
        print("-" * 70)
        print(f"|Psi|^2 mean:  {results['stats']['psi_mean']:.6f}")
        print(f"|Psi|^2 std:   {results['stats']['psi_std']:.6f}")
        print(f"|Psi|^2 range: [{results['stats']['psi_min']:.6f}, {results['stats']['psi_max']:.6f}]")
        print()
        print(f"Phi mean:    {results['stats']['phi_mean']:.6f}")
        print(f"Phi std:     {results['stats']['phi_std']:.6f}")
        print(f"Phi range:   [{results['stats']['phi_min']:.6f}, {results['stats']['phi_max']:.6f}]")
        print()

        print("-" * 70)
        print("MEASURED CENTERS")
        print("-" * 70)
        print(f"{'Method':<25} {'Center':<15} {'Drift':<15}")
        print("-" * 70)
        for method_name, center in results['methods'].items():
            drift = results['drifts'][method_name]
            if center is not None and drift is not None:
                print(f"{method_name:<25} {center:>10.2f}     {drift:>+10.2f}")
            else:
                print(f"{method_name:<25} {'N/A':<15} {'N/A':<15}")
        print()

        print("-" * 70)
        print("DRIFT VERDICT")
        print("-" * 70)

        # Get consensus drift (use Ψ squared as reference)
        reference_drift = results['drifts']['psi_squared_cm']

        if reference_drift is not None:
            abs_drift = abs(reference_drift)

            print(f"Reference method: Center of mass of |Psi|^2")
            print(f"Measured center:  {results['methods']['psi_squared_cm']:.2f}")
            print(f"Initial center:   {initial_center}")
            print(f"Drift:            {reference_drift:+.2f} nodes")
            print(f"Absolute drift:   {abs_drift:.2f} nodes")
            print()

            # Threshold for "zero drift": within 1% of system size
            threshold = N * 0.01

            if abs_drift < threshold:
                print(f"[PASS] ZERO DRIFT CONFIRMED (drift < {threshold:.0f} nodes = 1% of N)")
            else:
                print(f"[FAIL] DRIFT DETECTED (drift = {abs_drift:.2f} nodes > {threshold:.0f} nodes threshold)")

                # Classify drift type
                if abs_drift < N * 0.05:
                    print("  Magnitude: Small drift (~{:.1f}% of N)".format(100 * abs_drift / N))
                elif abs_drift < N * 0.1:
                    print("  Magnitude: Moderate drift (~{:.1f}% of N)".format(100 * abs_drift / N))
                else:
                    print("  Magnitude: Large drift (~{:.1f}% of N)".format(100 * abs_drift / N))

                if reference_drift > 0:
                    print(f"  Direction: Rightward (+{reference_drift:.2f} nodes)")
                else:
                    print(f"  Direction: Leftward ({reference_drift:.2f} nodes)")
        else:
            print("[ERROR] Could not measure drift (no structure in state)")

        print()
        print("=" * 70)

    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_drift.py <output.json> [initial_center]")
        print()
        print("Example:")
        print("  python extract_drift.py satp_t500_state.json 2048")
        sys.exit(1)

    json_file = sys.argv[1]
    initial_center = int(sys.argv[2]) if len(sys.argv) > 2 else 2048

    results = analyze_drift(json_file, initial_center=initial_center, verbose=True)
