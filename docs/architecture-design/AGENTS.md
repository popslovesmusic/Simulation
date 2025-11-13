# Simulation Project Agent Guidelines

This project follows the multi-phase implementation roadmap discussed in IGSOA project planning. Use this file as the authoritative reference for workflow expectations when contributing anywhere in the repository.

## Review-Driven Phase Structure
- Work must be organized into the following sequential phases, each ending with a formal review gate before progressing:
  1. **Phase 0 – Project Mobilization & Baseline Validation**: set up CI, repository structure confirmation, and baseline physics validation.
  2. **Phase 1 – Engine Refinement & Mission Schema Hardening**: expand regression coverage, mission validation, and profiling instrumentation.
  3. **Phase 2 – Playground Foundation (Stage 1 UI)**: deliver core Command Center UI with waveform visualization and mission control features.
  4. **Phase 3 – Advanced Playground Capabilities (Stage 2 UI)**: add symbolic tooling, tutorials/glossary, and collaboration support.
  5. **Phase 4 – Performance Acceleration & ML Surrogates**: curate datasets, train surrogate models, and integrate accelerated inference paths.
  6. **Phase 5 – Exploratory Science & Continuous Improvement**: launch research initiatives, enhance documentation, and solidify governance tooling.
- Do not skip or merge phases. Each phase requires a pause for stakeholder review to confirm objectives are met.

## Phase Execution Expectations
- Maintain clear success metrics and validation artifacts for each phase (test reports, profiling logs, review notes) under the appropriate directories (`results/`, `analysis/`, `docs/`).
- Prioritize user feedback loops during UI phases. Capture findings from Stage 1 and Stage 2 reviews before implementing advanced features.
- For ML work, establish reproducible dataset management and training configurations early to support later acceleration efforts.

## Contribution Guidance
- Reference this roadmap when planning changes; scope pull requests to a single phase whenever possible.
- Document review outcomes and decisions in `docs/reviews/` with links to relevant artifacts.
- Align new tooling, documentation, or research efforts with the phase currently in progress, and flag deviations for discussion during the next review gate.

Adhering to this phased plan keeps the IGSOA simulation ecosystem coherent, reviewable, and aligned with the Command Center vision.
