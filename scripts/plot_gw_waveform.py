#!/usr/bin/env python3
"""
IGSOA GW Waveform Visualization
Plots gravitational wave strain from binary merger simulation
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def plot_waveform(filename):
    """Plot waveform from CSV file"""

    # Check if file exists
    if not os.path.exists(filename):
        print(f"Error: File not found: {filename}")
        return

    # Load data
    print(f"Loading: {filename}")
    data = np.loadtxt(filename, delimiter=',', skiprows=1)

    time = data[:, 0]
    h_plus = data[:, 1]
    h_cross = data[:, 2]
    amplitude = data[:, 3]

    print(f"Data points: {len(time)}")
    print(f"Time range: {time[0]:.3f} to {time[-1]:.3f} seconds")
    print(f"Max h_+ strain: {np.max(np.abs(h_plus)):.3e}")
    print(f"Max h_× strain: {np.max(np.abs(h_cross)):.3e}")
    print(f"Max amplitude: {np.max(amplitude):.3e}")

    # Create figure
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    # Plot h_+
    axes[0].plot(time * 1000, h_plus, 'b-', linewidth=1.5, label='h_+')
    axes[0].set_ylabel('h_+ strain', fontsize=12)
    axes[0].set_title(f'IGSOA Gravitational Waveform - {os.path.basename(filename)}', fontsize=14, fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    # Plot h_×
    axes[1].plot(time * 1000, h_cross, 'r-', linewidth=1.5, label='h_×')
    axes[1].set_ylabel('h_× strain', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    # Plot amplitude
    axes[2].plot(time * 1000, amplitude, 'k-', linewidth=2, label='Total amplitude')
    axes[2].set_xlabel('Time (ms)', fontsize=12)
    axes[2].set_ylabel('Total amplitude', fontsize=12)

    # Use log scale if non-zero values exist
    if np.max(amplitude) > 0:
        axes[2].set_yscale('log')

    axes[2].grid(True, alpha=0.3)
    axes[2].legend()

    plt.tight_layout()

    # Save figure
    output_file = filename.replace('.csv', '.png')
    plt.savefig(output_file, dpi=300)
    print(f"Saved figure: {output_file}")

    plt.show()

def compare_waveforms(filenames):
    """Compare multiple waveforms with different alpha values"""

    fig, ax = plt.subplots(figsize=(12, 6))

    for filename in filenames:
        if not os.path.exists(filename):
            print(f"Warning: File not found: {filename}")
            continue

        data = np.loadtxt(filename, delimiter=',', skiprows=1)
        time = data[:, 0] * 1000  # Convert to ms
        h_plus = data[:, 1]

        # Extract alpha from filename
        alpha = filename.split('alpha_')[1].split('.csv')[0]

        ax.plot(time, h_plus, linewidth=1.5, label=f'α = {alpha}', alpha=0.8)

    ax.set_xlabel('Time (ms)', fontsize=12)
    ax.set_ylabel('GW Strain h_+', fontsize=12)
    ax.set_title('IGSOA Waveforms: Effect of Fractional Memory (α)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('alpha_comparison.png', dpi=300)
    print("Saved comparison: alpha_comparison.png")
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python plot_gw_waveform.py <waveform.csv> [<waveform2.csv> ...]")
        print("Example: python plot_gw_waveform.py gw_waveform_alpha_1.5.csv")
        sys.exit(1)

    if len(sys.argv) == 2:
        # Single waveform
        plot_waveform(sys.argv[1])
    else:
        # Multiple waveforms - comparison
        compare_waveforms(sys.argv[1:])
