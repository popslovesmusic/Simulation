# Echo Searches Program

## Objective
Identify and characterize post-merger gravitational-wave echoes expected from exotic compact object interactions. The program emphasizes joint time-frequency residual analysis and parameterized waveform inversion to separate genuine echoes from instrument artifacts.

## Workstreams
- **Residual Scanner** – deploy excess power scans on post-merger segments using multi-resolution Q transforms.
- **Template Inference Lab** – iterate on Bayesian parameter estimation for echo spacing, damping, and phase coherence.
- **Artifact Rejection Taskforce** – correlate candidate events with auxiliary sensors to eliminate glitches and operator interventions.

## Success Metrics
| Metric | Target | Validation Artifact |
| --- | --- | --- |
| Echo recovery rate on simulated datasets | ≥ 85% | Injection matrix stored under `results/echo/recall_matrix.csv` |
| False positive rate | ≤ 3% | Quarterly review packet with glitch cross-checks |
| Posterior convergence time | ≤ 6 hours on 64-core cluster | Profiling summary archived in `analysis/notebooks/echo_sampler_bench.ipynb` |
| Cross-team review cadence | Monthly | Meeting notes housed in `docs/reviews/echo-searches` |

## Milestones
1. Assemble catalog of historical post-merger segments (Week 2).
2. Deliver first-pass residual scanner with alerting to the Command Center (Week 4).
3. Validate template inference lab against curated injection suite (Week 6).
4. Conduct cross-team review prior to scaling compute spend (Week 8).

## Dependencies
- Requires stable calibration pipeline outputs from Phase 1 operations.
- Must integrate with collaboration session tooling for peer review sign-off.
- Needs access to user feedback metrics gathered via Command Center surveys to refine prioritization.
