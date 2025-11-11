# IGSOA Simulation Risk Register

The risk register is maintained jointly by engineering, science, and operations leads. Update entries after each cross-functional review and whenever new mitigations are enacted.

## Risk Scoring Key
- **Probability**: Low (L), Medium (M), High (H)
- **Impact**: Low (L), Medium (M), High (H)
- **Owner**: Accountable individual or guild responsible for mitigation.

## Active Risks

| ID | Description | Probability | Impact | Owner | Mitigation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-101 | Calibration drift impacting continuous wave detection sensitivity | M | H | Waveform Systems Guild | Automated calibration validation in `analysis/projects/continuous-wave-detection` with weekly drift reports | Monitoring |
| R-118 | Telemetry dashboards lacking real user adoption signals | M | M | Command Center Product | Launch survey cadence defined in `web/command-center/analytics` and track ≥60% response rate | Mitigation Active |
| R-132 | CMB imprint analysis susceptible to dust residual contamination | L | H | Science Council | Enforce dual-pipeline validation and capture findings in `analysis/projects/cmb-imprint-analysis` | Watch |
| R-147 | Echo search compute costs exceeding allocation | M | M | Research Operations | Profile inference workloads and escalate capacity decisions during monthly reviews | Mitigation Planned |

## Recently Closed Risks

| ID | Description | Resolution |
| --- | --- | --- |
| R-095 | Lack of onboarding documentation for new analysis contributors | Resolved via `docs/getting-started/ONBOARDING_CHECKLIST.md` and developer guide refresh. |

## Review Cadence
- Monthly cross-functional reviews documented in `docs/reviews/`.
- Quarterly governance board updates that feed into the release checklist.
- Immediate updates required when survey or telemetry signals regress beyond defined success thresholds.
