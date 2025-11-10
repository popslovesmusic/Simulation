#!/usr/bin/env python3
"""
SATP+Higgs Field Visualization Script

Usage:
    python visualize_satp.py state.json

Or pipe from CLI:
    echo '{"command":"get_satp_state",...}' | dase_cli.exe | tail -1 | python visualize_satp.py -
"""

import json
import sys
import matplotlib.pyplot as plt
import numpy as np

def plot_satp_state(data):
    """Plot SATP+Higgs field states"""

    # Extract field data
    phi = np.array(data['phi'])
    phi_dot = np.array(data['phi_dot'])
    h = np.array(data['h'])
    h_dot = np.array(data['h_dot'])
    num_nodes = data['num_nodes']

    # Extract diagnostics
    diag = data.get('diagnostics', {})
    phi_rms = diag.get('phi_rms', 0)
    h_rms = diag.get('h_rms', 0)
    energy = diag.get('total_energy', 0)
    time = data.get('time', 0)

    # Create x-axis (lattice positions)
    x = np.arange(num_nodes)

    # Create figure with 4 subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'SATP+Higgs Field State (t={time:.3f})', fontsize=14, fontweight='bold')

    # Plot φ field
    ax = axes[0, 0]
    ax.plot(x, phi, 'b-', linewidth=1.5, label='φ(x)')
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('Lattice Position')
    ax.set_ylabel('φ (Scale Field)')
    ax.set_title(f'Scale Field φ (RMS: {phi_rms:.4f})')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot φ̇ field (velocity)
    ax = axes[0, 1]
    ax.plot(x, phi_dot, 'c-', linewidth=1.5, label='∂φ/∂t')
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('Lattice Position')
    ax.set_ylabel('∂φ/∂t (Scale Velocity)')
    ax.set_title('Scale Field Velocity')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot h field (Higgs)
    ax = axes[1, 0]
    # Compute VEV from average (should be ~1.0)
    h_vev = np.mean(h)
    h_deviation = h - h_vev
    ax.plot(x, h, 'r-', linewidth=1.5, label='h(x)', alpha=0.7)
    ax.plot(x, h_deviation, 'orange', linewidth=1.5, label=f'h - VEV (VEV≈{h_vev:.4f})', alpha=0.7)
    ax.axhline(y=h_vev, color='k', linestyle='--', alpha=0.3, label='VEV')
    ax.set_xlabel('Lattice Position')
    ax.set_ylabel('h (Higgs Field)')
    ax.set_title(f'Higgs Field h (RMS: {h_rms:.4f})')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Plot ḣ field (Higgs velocity)
    ax = axes[1, 1]
    ax.plot(x, h_dot, 'm-', linewidth=1.5, label='∂h/∂t')
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('Lattice Position')
    ax.set_ylabel('∂h/∂t (Higgs Velocity)')
    ax.set_title('Higgs Field Velocity')
    ax.grid(True, alpha=0.3)
    ax.legend()

    # Add text box with diagnostics
    textstr = f'Diagnostics:\n'
    textstr += f'Nodes: {num_nodes}\n'
    textstr += f'φ RMS: {phi_rms:.4f}\n'
    textstr += f'h RMS: {h_rms:.4f}\n'
    textstr += f'Total Energy: {energy:.4f}\n'
    textstr += f'Time: {time:.4f}'

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    fig.text(0.98, 0.02, textstr, fontsize=10, verticalalignment='bottom',
             horizontalalignment='right', bbox=props, family='monospace')

    plt.tight_layout()
    return fig

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filename = sys.argv[1]

    # Read JSON data
    if filename == '-':
        # Read from stdin
        data = json.load(sys.stdin)
    else:
        with open(filename, 'r') as f:
            data = json.load(f)

    # Handle response format (extract result if present)
    if 'result' in data:
        state_data = data['result']
    else:
        state_data = data

    # Plot the state
    fig = plot_satp_state(state_data)

    # Save or show
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Figure saved to {output_file}")
    else:
        plt.show()

if __name__ == '__main__':
    main()
