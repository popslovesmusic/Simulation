#!/usr/bin/env python3
"""
IGSOA State Analysis Tool
==========================

Comprehensive spectral analysis of IGSOA quantum states extracted via get_state command.

Features:
- Power spectrum analysis (FFT)
- Spatial correlation functions
- R_c validation via spectral cutoff
- Peak detection and characterization
- Φ-Ψ coupling analysis
- Publication-quality plots
- Automated report generation

Usage:
    python analyze_igsoa_state.py <json_output> <R_c> [options]

    json_output: Output from `dase_cli.exe < mission_spectral.json`
    R_c: Causal radius parameter used in the mission

Options:
    --output-dir DIR      Output directory for plots and reports (default: igsoa_analysis)
    --plot-format FMT     Plot format: png, pdf, svg (default: png)
    --dpi DPI             Plot resolution (default: 300)
    --no-plots            Skip plot generation
    --verbose             Enable verbose output

Example:
    python analyze_igsoa_state.py spectral_output.json 2.0
    python analyze_igsoa_state.py output.json 4.0 --output-dir results_R4 --dpi 600
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq, fftshift
from scipy.signal import correlate, find_peaks
from scipy.optimize import curve_fit
import argparse
import os
import sys
from datetime import datetime

# Configure stdout encoding for Unicode support on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure matplotlib for publication-quality plots
plt.rcParams['font.size'] = 11
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Computer Modern Roman']
plt.rcParams['text.usetex'] = False  # Set to True if LaTeX is available
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14


class IGSOAStateAnalyzer:
    """Analyzer for IGSOA quantum states"""

    def __init__(self, json_file, R_c, verbose=False):
        """
        Initialize analyzer

        Args:
            json_file: Path to JSON output from dase_cli
            R_c: Causal radius parameter
            verbose: Enable verbose output
        """
        self.json_file = json_file
        self.R_c = R_c
        self.verbose = verbose

        # Load state data
        self.N, self.psi, self.phi = self._load_state()

        # Derived quantities
        self.F = np.abs(self.psi)**2  # Informational density
        self.phase = np.angle(self.psi)  # Phase

        # Analysis results (computed on demand)
        self.freq_psi = None
        self.power_psi = None
        self.freq_phi = None
        self.power_phi = None
        self.correlation = None
        self.correlation_length = None
        self.spectral_decay_length = None
        self.peaks = None

    def _load_state(self):
        """Load state arrays from JSON output"""
        if self.verbose:
            print(f"Loading state from {self.json_file}...")

        with open(self.json_file, 'r') as f:
            lines = f.readlines()

        # Find the get_state response (ignore diagnostic output)
        for line in lines:
            try:
                data = json.loads(line)
                if data.get('command') == 'get_state' and data.get('status') == 'success':
                    result = data['result']

                    N = result['num_nodes']
                    psi_real = np.array(result['psi_real'])
                    psi_imag = np.array(result['psi_imag'])
                    phi = np.array(result['phi'])

                    psi = psi_real + 1j * psi_imag

                    if self.verbose:
                        print(f"  Loaded N={N} nodes")
                        print(f"  |Ψ|² range: [{np.min(np.abs(psi)**2):.6f}, {np.max(np.abs(psi)**2):.6f}]")
                        print(f"  Φ range: [{np.min(phi):.6f}, {np.max(phi):.6f}]")

                    return N, psi, phi

            except json.JSONDecodeError:
                continue  # Skip non-JSON lines (e.g., diagnostic prints)

        raise ValueError(f"No valid get_state response found in {self.json_file}")

    def compute_power_spectra(self):
        """Compute power spectra via FFT"""
        if self.verbose:
            print("\nComputing power spectra...")

        # Ψ power spectrum
        psi_fft = fft(self.psi)
        self.power_psi = np.abs(psi_fft)**2
        self.freq_psi = fftfreq(self.N, d=1.0)

        # Φ power spectrum (remove DC component)
        phi_centered = self.phi - np.mean(self.phi)
        phi_fft = fft(phi_centered)
        self.power_phi = np.abs(phi_fft)**2
        self.freq_phi = fftfreq(self.N, d=1.0)

        if self.verbose:
            total_power_psi = np.sum(self.power_psi)
            total_power_phi = np.sum(self.power_phi)
            print(f"  Total Ψ power: {total_power_psi:.3e}")
            print(f"  Total Φ power: {total_power_phi:.3e}")

    def compute_spatial_correlation(self):
        """Compute spatial correlation function"""
        if self.verbose:
            print("\nComputing spatial correlation...")

        # Autocorrelation of informational density F
        F_centered = self.F - np.mean(self.F)
        self.correlation = correlate(F_centered, F_centered, mode='same') / self.N

        # Normalize
        self.correlation /= self.correlation[self.N // 2]

        # Find correlation length (e^{-1} decay point)
        corr_right = self.correlation[self.N // 2:]
        decay_idx = np.where(corr_right < np.exp(-1))[0]

        if len(decay_idx) > 0:
            self.correlation_length = decay_idx[0]
            if self.verbose:
                print(f"  Correlation length ξ = {self.correlation_length} lattice sites")
                print(f"  R_c = {self.R_c} → ξ/R_c = {self.correlation_length / self.R_c:.3f}")
        else:
            self.correlation_length = None
            if self.verbose:
                print("  Warning: Correlation length not found (no e^{-1} decay)")

    def measure_spectral_decay(self):
        """Measure spectral decay length from high-k tail"""
        if self.verbose:
            print("\nMeasuring spectral decay...")

        if self.power_psi is None:
            self.compute_power_spectra()

        # Focus on positive frequencies
        k_positive = self.freq_psi[:self.N // 2]

        # Find region beyond k ~ 1/R_c for fitting
        k_cutoff = 1.0 / self.R_c
        fit_region = (k_positive > k_cutoff) & (k_positive < k_positive[-1] / 2)

        if np.sum(fit_region) < 5:
            if self.verbose:
                print("  Warning: Insufficient data for spectral decay fit")
            self.spectral_decay_length = None
            return

        # Fit exponential decay: P(k) = A * exp(-k/k0) + B
        def exp_decay(k, A, B, k0):
            return A * np.exp(-k / k0) + B

        k_fit = k_positive[fit_region]
        power_fit = self.power_psi[:self.N // 2][fit_region]

        # Filter out zeros/very small values
        valid = power_fit > np.max(power_fit) * 1e-10
        k_fit = k_fit[valid]
        power_fit = power_fit[valid]

        if len(k_fit) < 5:
            if self.verbose:
                print("  Warning: Insufficient valid data for fit")
            self.spectral_decay_length = None
            return

        try:
            # Initial guess
            p0 = [np.max(power_fit), np.min(power_fit), 1.0 / self.R_c]
            popt, _ = curve_fit(exp_decay, k_fit, power_fit, p0=p0, maxfev=10000)

            self.spectral_decay_length = popt[2]

            if self.verbose:
                print(f"  Spectral decay length k₀ = {self.spectral_decay_length:.4f}")
                print(f"  Expected from R_c: k₀ ~ {1 / self.R_c:.4f}")
                print(f"  Ratio k₀/(1/R_c) = {self.spectral_decay_length * self.R_c:.3f}")

        except Exception as e:
            if self.verbose:
                print(f"  Warning: Spectral decay fit failed: {e}")
            self.spectral_decay_length = None

    def find_spectral_peaks(self, n_peaks=10):
        """Find prominent spectral peaks"""
        if self.verbose:
            print(f"\nFinding top {n_peaks} spectral peaks...")

        if self.power_psi is None:
            self.compute_power_spectra()

        # Search positive frequencies only
        power_half = self.power_psi[:self.N // 2]
        freq_half = self.freq_psi[:self.N // 2]

        # Find peaks above median
        threshold = np.median(power_half)
        peaks_idx, properties = find_peaks(power_half, height=threshold)

        if len(peaks_idx) == 0:
            if self.verbose:
                print("  No significant peaks found")
            self.peaks = None
            return

        # Sort by power
        sorted_idx = np.argsort(power_half[peaks_idx])[::-1]
        top_peaks = peaks_idx[sorted_idx[:n_peaks]]

        self.peaks = {
            'frequencies': freq_half[top_peaks],
            'powers': power_half[top_peaks],
            'indices': top_peaks
        }

        if self.verbose:
            print(f"  Found {len(peaks_idx)} peaks total")
            print(f"\n  Top {min(n_peaks, len(top_peaks))} peaks:")
            print("  " + "-" * 45)
            print("  k\t\t|Ψ̂(k)|²")
            print("  " + "-" * 45)
            for k, p in zip(self.peaks['frequencies'], self.peaks['powers']):
                print(f"  {k:.4f}\t\t{p:.6e}")

    def analyze_phi_psi_coupling(self):
        """Analyze Φ-Ψ phase relationship via cross-correlation"""
        if self.verbose:
            print("\nAnalyzing Φ-Ψ coupling...")

        # Cross-correlate Φ with Re[Ψ]
        phi_centered = self.phi - np.mean(self.phi)
        psi_real_centered = np.real(self.psi) - np.mean(np.real(self.psi))

        cross_corr = correlate(phi_centered, psi_real_centered, mode='same') / self.N

        # Normalize
        cross_corr /= np.max(np.abs(cross_corr))

        # Find peak (phase lag)
        peak_idx = np.argmax(np.abs(cross_corr))
        phase_lag = peak_idx - self.N // 2

        if self.verbose:
            print(f"  Phase lag: Φ lags Re[Ψ] by {phase_lag} lattice sites")
            print(f"  Cross-correlation peak: {cross_corr[peak_idx]:.4f}")

        return phase_lag, cross_corr

    def plot_power_spectra(self, output_dir, fmt='png', dpi=300):
        """Plot power spectra"""
        if self.verbose:
            print("\nGenerating power spectrum plots...")

        if self.power_psi is None:
            self.compute_power_spectra()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # Ψ power spectrum
        k_half = self.freq_psi[:self.N // 2]
        power_psi_half = self.power_psi[:self.N // 2]

        ax1.semilogy(k_half, power_psi_half, 'b-', linewidth=1.5, label='|Ψ̂(k)|²')
        ax1.axvline(1 / self.R_c, color='r', linestyle='--', linewidth=2,
                    label=f'k ~ 1/R_c = {1 / self.R_c:.3f}')

        # Mark peaks if found
        if self.peaks is not None:
            ax1.scatter(self.peaks['frequencies'], self.peaks['powers'],
                       c='darkred', s=80, marker='x', zorder=5,
                       label=f'Top {len(self.peaks["frequencies"])} peaks')

        ax1.set_xlabel('Spatial Frequency k')
        ax1.set_ylabel('Power |Ψ̂(k)|²')
        ax1.set_title(f'Quantum State Power Spectrum (R_c={self.R_c}, N={self.N})')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # Φ power spectrum
        power_phi_half = self.power_phi[:self.N // 2]

        ax2.semilogy(k_half, power_phi_half, 'g-', linewidth=1.5, label='|Φ̂(k)|²')
        ax2.set_xlabel('Spatial Frequency k')
        ax2.set_ylabel('Power |Φ̂(k)|²')
        ax2.set_title('Realized Field Power Spectrum')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        filename = os.path.join(output_dir, f'power_spectra_R{self.R_c:.1f}.{fmt}')
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()

        if self.verbose:
            print(f"  Saved: {filename}")

    def plot_spatial_correlation(self, output_dir, fmt='png', dpi=300):
        """Plot spatial correlation function"""
        if self.verbose:
            print("\nGenerating spatial correlation plot...")

        if self.correlation is None:
            self.compute_spatial_correlation()

        fig, ax = plt.subplots(figsize=(10, 6))

        lags = np.arange(-self.N // 2, self.N // 2)

        ax.plot(lags, self.correlation, 'b-', linewidth=2, label='⟨F(x)F(x+Δx)⟩')
        ax.axhline(0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
        ax.axhline(np.exp(-1), color='orange', linestyle='--', linewidth=2,
                   label='e⁻¹ decay threshold')

        # Mark R_c
        ax.axvline(-self.R_c, color='r', linestyle='--', linewidth=2, alpha=0.7)
        ax.axvline(self.R_c, color='r', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'±R_c = ±{self.R_c}')

        # Mark measured correlation length
        if self.correlation_length is not None:
            ax.axvline(self.correlation_length, color='g', linestyle=':', linewidth=2,
                       label=f'ξ = {self.correlation_length}')

        ax.set_xlabel('Spatial Lag Δx (lattice sites)')
        ax.set_ylabel('Normalized Correlation')
        ax.set_title(f'Spatial Correlation of Informational Density F = |Ψ|² (R_c={self.R_c})')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-min(50, self.N // 4), min(50, self.N // 4))

        plt.tight_layout()
        filename = os.path.join(output_dir, f'spatial_correlation_R{self.R_c:.1f}.{fmt}')
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()

        if self.verbose:
            print(f"  Saved: {filename}")

    def plot_state_profiles(self, output_dir, fmt='png', dpi=300):
        """Plot spatial profiles of Ψ and Φ"""
        if self.verbose:
            print("\nGenerating state profile plots...")

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        x = np.arange(self.N)

        # |Ψ|² profile
        axes[0].plot(x, self.F, 'b-', linewidth=1.5)
        axes[0].set_ylabel('Informational Density F = |Ψ|²')
        axes[0].set_title(f'IGSOA State Profiles (R_c={self.R_c}, N={self.N})')
        axes[0].grid(True, alpha=0.3)

        # Phase profile
        axes[1].plot(x, self.phase, 'purple', linewidth=1.5)
        axes[1].set_ylabel('Phase arg(Ψ) [rad]')
        axes[1].axhline(0, color='k', linestyle='--', linewidth=0.5, alpha=0.3)
        axes[1].grid(True, alpha=0.3)

        # Φ profile
        axes[2].plot(x, self.phi, 'g-', linewidth=1.5)
        axes[2].set_xlabel('Lattice Site x')
        axes[2].set_ylabel('Realized Field Φ')
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()
        filename = os.path.join(output_dir, f'state_profiles_R{self.R_c:.1f}.{fmt}')
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close()

        if self.verbose:
            print(f"  Saved: {filename}")

    def generate_report(self, output_dir):
        """Generate text report with analysis results"""
        if self.verbose:
            print("\nGenerating analysis report...")

        # Ensure all analyses are done
        if self.power_psi is None:
            self.compute_power_spectra()
        if self.correlation is None:
            self.compute_spatial_correlation()
        if self.spectral_decay_length is None:
            self.measure_spectral_decay()
        if self.peaks is None:
            self.find_spectral_peaks()

        # Create report
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("IGSOA STATE ANALYSIS REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Input file: {self.json_file}")
        report_lines.append(f"")

        # System parameters
        report_lines.append("\n" + "-" * 70)
        report_lines.append("SYSTEM PARAMETERS")
        report_lines.append("-" * 70)
        report_lines.append(f"Number of nodes (N):        {self.N}")
        report_lines.append(f"Causal radius (R_c):        {self.R_c}")
        report_lines.append(f"")

        # State statistics
        report_lines.append("\n" + "-" * 70)
        report_lines.append("STATE STATISTICS")
        report_lines.append("-" * 70)
        report_lines.append(f"|Ψ|² mean:                   {np.mean(self.F):.6f}")
        report_lines.append(f"|Ψ|² std dev:                {np.std(self.F):.6f}")
        report_lines.append(f"|Ψ|² range:                  [{np.min(self.F):.6f}, {np.max(self.F):.6f}]")
        report_lines.append(f"")
        report_lines.append(f"Φ mean:                     {np.mean(self.phi):.6f}")
        report_lines.append(f"Φ std dev:                  {np.std(self.phi):.6f}")
        report_lines.append(f"Φ range:                    [{np.min(self.phi):.6f}, {np.max(self.phi):.6f}]")
        report_lines.append(f"")
        report_lines.append(f"Phase mean:                 {np.mean(self.phase):.6f} rad")
        report_lines.append(f"Phase std dev:              {np.std(self.phase):.6f} rad")
        report_lines.append(f"")

        # Spectral analysis results
        report_lines.append("\n" + "-" * 70)
        report_lines.append("SPECTRAL ANALYSIS")
        report_lines.append("-" * 70)

        if self.spectral_decay_length is not None:
            report_lines.append(f"Spectral decay length (k₀): {self.spectral_decay_length:.4f}")
            report_lines.append(f"Expected (1/R_c):           {1 / self.R_c:.4f}")
            report_lines.append(f"Ratio k₀/(1/R_c):           {self.spectral_decay_length * self.R_c:.3f}")
        else:
            report_lines.append("Spectral decay length:      NOT MEASURED (insufficient data)")

        report_lines.append(f"")
        report_lines.append(f"Total Ψ power:              {np.sum(self.power_psi):.6e}")
        report_lines.append(f"Total Φ power:              {np.sum(self.power_phi):.6e}")
        report_lines.append(f"")

        # Peaks
        if self.peaks is not None and len(self.peaks['frequencies']) > 0:
            report_lines.append(f"\nTop {len(self.peaks['frequencies'])} spectral peaks:")
            report_lines.append("  k          |Ψ̂(k)|²")
            report_lines.append("  " + "-" * 35)
            for k, p in zip(self.peaks['frequencies'], self.peaks['powers']):
                report_lines.append(f"  {k:.4f}     {p:.6e}")
        else:
            report_lines.append("\nNo significant spectral peaks found")

        # Spatial correlation
        report_lines.append("\n" + "-" * 70)
        report_lines.append("SPATIAL CORRELATION")
        report_lines.append("-" * 70)

        if self.correlation_length is not None:
            report_lines.append(f"Correlation length (ξ):     {self.correlation_length} lattice sites")
            report_lines.append(f"R_c:                        {self.R_c}")
            report_lines.append(f"Ratio ξ/R_c:                {self.correlation_length / self.R_c:.3f}")
            report_lines.append(f"")
            if abs(self.correlation_length / self.R_c - 1.0) < 0.3:
                report_lines.append("✓ Correlation length matches R_c (within 30%)")
            else:
                report_lines.append("✗ Correlation length deviates from R_c")
        else:
            report_lines.append("Correlation length:         NOT FOUND (no e^{-1} decay)")

        # Physics validation summary
        report_lines.append("\n" + "=" * 70)
        report_lines.append("PHYSICS VALIDATION SUMMARY")
        report_lines.append("=" * 70)

        validation_checks = []

        # Check 1: Spectral cutoff
        if self.spectral_decay_length is not None:
            ratio = self.spectral_decay_length * self.R_c
            if 0.7 < ratio < 1.3:
                validation_checks.append("✓ Spectral cutoff validates R_c parameter")
            else:
                validation_checks.append(f"✗ Spectral cutoff deviates (ratio={ratio:.2f}, expected~1.0)")
        else:
            validation_checks.append("? Spectral cutoff not measured")

        # Check 2: Correlation length
        if self.correlation_length is not None:
            ratio = self.correlation_length / self.R_c
            if 0.7 < ratio < 1.3:
                validation_checks.append("✓ Correlation length validates R_c parameter")
            else:
                validation_checks.append(f"✗ Correlation length deviates (ξ/R_c={ratio:.2f}, expected~1.0)")
        else:
            validation_checks.append("? Correlation length not measured")

        # Check 3: State normalization
        mean_norm = np.mean(self.F)
        if 0.9 < mean_norm < 1.1:
            validation_checks.append("✓ State approximately normalized (⟨|Ψ|²⟩ ~ 1)")
        else:
            validation_checks.append(f"✗ State not normalized (⟨|Ψ|²⟩ = {mean_norm:.3f})")

        for check in validation_checks:
            report_lines.append(check)

        report_lines.append("\n" + "=" * 70)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 70)

        # Write report
        report_file = os.path.join(output_dir, f'analysis_report_R{self.R_c:.1f}.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        if self.verbose:
            print(f"  Saved: {report_file}")

        return '\n'.join(report_lines)

    def run_full_analysis(self, output_dir='igsoa_analysis', plot_format='png', dpi=300, skip_plots=False):
        """Run complete analysis pipeline"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n{'=' * 70}")
        print(f"IGSOA STATE ANALYSIS")
        print(f"{'=' * 70}")
        print(f"Input:       {self.json_file}")
        print(f"R_c:         {self.R_c}")
        print(f"N:           {self.N}")
        print(f"Output dir:  {output_dir}")
        print(f"{'=' * 70}\n")

        # Run analyses
        self.compute_power_spectra()
        self.compute_spatial_correlation()
        self.measure_spectral_decay()
        self.find_spectral_peaks()

        # Generate plots
        if not skip_plots:
            self.plot_power_spectra(output_dir, fmt=plot_format, dpi=dpi)
            self.plot_spatial_correlation(output_dir, fmt=plot_format, dpi=dpi)
            self.plot_state_profiles(output_dir, fmt=plot_format, dpi=dpi)

        # Generate report
        report = self.generate_report(output_dir)

        print(f"\n{'=' * 70}")
        print("ANALYSIS COMPLETE")
        print(f"{'=' * 70}")
        print(f"\nOutput files in: {output_dir}/")
        print(f"  - analysis_report_R{self.R_c:.1f}.txt")
        if not skip_plots:
            print(f"  - power_spectra_R{self.R_c:.1f}.{plot_format}")
            print(f"  - spatial_correlation_R{self.R_c:.1f}.{plot_format}")
            print(f"  - state_profiles_R{self.R_c:.1f}.{plot_format}")
        print()

        return report


def main():
    parser = argparse.ArgumentParser(
        description='IGSOA State Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_igsoa_state.py output.json 2.0
  python analyze_igsoa_state.py spectral.json 4.0 --output-dir results_R4
  python analyze_igsoa_state.py data.json 1.0 --plot-format pdf --dpi 600
        """
    )

    parser.add_argument('json_file', help='JSON output from dase_cli.exe')
    parser.add_argument('R_c', type=float, help='Causal radius parameter')
    parser.add_argument('--output-dir', default='igsoa_analysis',
                       help='Output directory for results (default: igsoa_analysis)')
    parser.add_argument('--plot-format', default='png', choices=['png', 'pdf', 'svg'],
                       help='Plot file format (default: png)')
    parser.add_argument('--dpi', type=int, default=300,
                       help='Plot resolution in DPI (default: 300)')
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip plot generation (report only)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--timestamp', action='store_true',
                       help='Add timestamp to output directory name')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.json_file):
        print(f"Error: File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # Add timestamp to output directory if requested
    output_dir = args.output_dir
    if args.timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"{args.output_dir}_{timestamp}"

    # Run analysis
    try:
        analyzer = IGSOAStateAnalyzer(args.json_file, args.R_c, verbose=args.verbose)
        analyzer.run_full_analysis(
            output_dir=output_dir,
            plot_format=args.plot_format,
            dpi=args.dpi,
            skip_plots=args.no_plots
        )

    except Exception as e:
        print(f"\nError during analysis: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
