# Phase 4 Surrogate Performance Review

**Date:** 2025-11-10  \
**Facilitator:** Acceleration Working Group  \
**Scope:** Dataset curation, surrogate prototyping, and engine integration readiness

## Executive Summary

The Phase 4 acceleration sprint successfully established the infrastructure
required to train and serve surrogate models within the IGSOA simulation stack.
Waveform runs can now be curated into reproducible datasets, PyTorch-based
surrogate prototypes are available for experimentation, and the backend runtime
supports surrogate inference with robust fallbacks and benchmarking capture.

## Latency Analysis

- Surrogate inference latency is recorded per command via `SurrogateAdapter`
  metrics. Initial dry-run benchmarks on synthetic data show sub-millisecond
  inference, while full simulation fallbacks remain orders of magnitude slower.
- Profiling artifacts store surrogate usage flags, enabling longitudinal
  tracking of latency regression across missions.
- Benchmark JSON artifacts are written to `analysis/datasets/surrogate_benchmarks/`
  for auditability.

## Accuracy Trade-offs

- Validation mode compares surrogate predictions against the full simulation to
  compute mean absolute error (MAE). These metrics are appended to profiler
  metadata and persisted in benchmark artifacts.
- Notebook-driven experiments (`analysis/notebooks/surrogate_evaluation.ipynb`)
  codify the baseline training configuration (seeded runs, layer sizes, and
  optimiser settings) to make future accuracy studies reproducible.
- Surrogate fallbacks remain enabled by default until accuracy targets are
  validated across representative missions.

## Data Governance

- Dataset packaging scripts enforce provenance tracking by embedding source run
  paths and metadata fields inside dataset manifests (`manifest.json`).
- Generated datasets reside under `analysis/datasets/`, segregating training
  artifacts from mission telemetry. The repository README for the datasets
  directory documents handling expectations and overwrite policies.
- Benchmark payloads include timestamps and run identifiers, providing a clear
  chain of custody for model evaluation data.

## Action Items

1. Populate curated datasets using recent waveform batches and file a follow-up
   review to confirm statistical representativeness.
2. Extend surrogate benchmarking to capture additional error metrics (RMSE,
   spectral energy drift) before enabling surrogates in production missions.
3. Coordinate with governance to validate anonymisation procedures ahead of any
   external data sharing.

_Approved by the Acceleration Working Group. No outstanding blockers for moving
into targeted surrogate training experiments._
