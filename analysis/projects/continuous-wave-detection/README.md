# Continuous Wave Detection Initiative

## Objective
Deliver a real-time detection pipeline for persistent gravitational-wave tones emitted by rapidly rotating neutron stars and compact binary inspirals in quasi-stationary phases. The workstream prioritizes spectral coherence tracking alongside mission telemetry fusion to raise sensitivity without increasing alert latency.

## Workstreams
- **Spectral Tracking Engine** – extend the matched-filter bank with adaptive coherent integration windows tuned for 10–1000 Hz signals.
- **Noise Subtraction Study** – quantify benefits of magnetometer-driven subtraction and phased array nulling during high-noise windows.
- **Mission Telemetry Bridge** – wire control-room mission state changes into the detection scheduler for proactive recalibration.

## Success Metrics
| Metric | Target | Validation Artifact |
| --- | --- | --- |
| Detection efficiency at 1e-25 strain | ≥ 92% | Coherent injection campaign summarized in `results/cw_detection_efficiency.csv` |
| False alarm probability per 30-day run | ≤ 0.5% | Monthly false trigger log with adjudication notes |
| Alert latency from strain capture | ≤ 90 s (p95) | Integrated dashboard export from Command Center analytics |
| Calibration drift mitigation | ≤ 1% SNR penalty across 7-day stability test | Drift analysis notebook committed under `analysis/notebooks/cw_calibration.ipynb` |

## Milestones
1. Baseline matched filter benchmark against archived O3 data (Week 1).
2. Adaptive coherence window tuning under synthetic injections (Week 3).
3. Closed-loop dry run with telemetry playback inside Command Center (Week 5).
4. Phase review with science, operations, and ML leads (Week 6).

## Dependencies
- Requires access to the mission scheduler event bus (Phase 1 deliverable).
- FFT acceleration enhancements from Phase 4 must remain feature-flagged for reproducibility.
- Continuous survey instrumentation provided by the analytics stack (`web/command-center/analytics`).
