# Phase 0 Baseline Validation Report

This report captures automated comparisons between the current artifact set
and the analytical benchmarks established for Phase 0 mobilization.

## Summary

- Checks within tolerance: 11 / 12
- Flagged follow-ups: 1

## Detailed Results

| Status | Artifact | Metric | Measured | Benchmark | Rule | Δ |
|--------|----------|--------|----------|-----------|------|---|
| ✅ | oscillator_100.0hz | frequency_hz | 1.000000e+02 | 1.000000e+02 | ±1.00e-06 | 0.00e+00 |
| ✅ | oscillator_440.0hz | frequency_hz | 4.400000e+02 | 4.400000e+02 | ±1.00e-06 | 0.00e+00 |
| ✅ | oscillator_1000.0hz | frequency_hz | 1.000000e+03 | 1.000000e+03 | ±1.00e-06 | 0.00e+00 |
| ✅ | filter_64samples | energy_ratio | 2.647059e-01 | 2.647059e-01 | ±5.00e-08 | -3.16e-08 |
| ✅ | filter_128samples | energy_ratio | 2.647059e-01 | 2.647059e-01 | ±5.00e-08 | -3.16e-08 |
| ✅ | filter_256samples | energy_ratio | 2.647059e-01 | 2.647059e-01 | ±5.00e-08 | -3.16e-08 |
| ✅ | filter_512samples | energy_ratio | 2.647059e-01 | 2.647059e-01 | ±5.00e-08 | -3.16e-08 |
| ✅ | filter_1024samples | energy_ratio | 2.647059e-01 | 2.647059e-01 | ±5.00e-08 | -3.16e-08 |
| ✅ | engine_integration | ns_per_op | 9.708464e+01 | 1.000000e+02 | ≤1.00e+02 | -2.92e+00 |
| ✅ | engine_integration | speedup | 1.596545e+02 | 1.500000e+02 | ≥1.50e+02 | 9.65e+00 |
| ✅ | gw_waveform_alpha_1.500000 | peak_amplitude | 4.390880e-19 | 4.390880e-19 | ±8.78e-21 | 0.00e+00 |
| ⚠️ | gw_waveform_alpha_1.500000 | mean_amplitude | 2.969284e-19 | 1.975896e-19 | ±1.98e-20 | 9.93e-20 |

## Flags

- **gw_waveform_alpha_1.500000** — Waveform mean amplitude drifted outside the 10% stability band.

## Data Sources

- Verification log: `verification_results_20251023_054706.json`
- Waveform sample: `gw_waveform_alpha_1.500000.csv`
