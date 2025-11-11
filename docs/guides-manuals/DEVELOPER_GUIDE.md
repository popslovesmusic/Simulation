# IGSOA Simulation Developer Guide

This guide equips contributors with the engineering context, workflows, and quality bars required to extend the IGSOA simulation platform. It should be read alongside the project roadmap and phase reviews documented in `docs/reviews/`.

## Architecture Orientation
- **Core Engine (`src/`, `backend/`)** – high-performance waveform generation and mission orchestration primitives. Respect deterministic execution and thread-safety measures outlined in the error-handling dossiers.
- **Analysis Tooling (`analysis/`)** – reproducible notebooks, scripts, and study artifacts. Each project folder must include success metrics and validation data.
- **Command Center UI (`web/command-center/`)** – React + Vite frontend delivering mission operations workflows.
- **Governance & Reviews (`docs/reviews/`)** – houses formal phase gates, risk decisions, and cross-functional notes.

## Branching & Reviews
1. Derive feature branches from the active phase branch (e.g., `phase-5/research`).
2. Keep changes scoped to a single roadmap phase. Reference success metrics in the PR summary.
3. Run relevant verification steps (unit tests, `npm run build`, `engine_test_suite.sh`, etc.) and attach logs.
4. Request reviewers from engine, analysis, and operations guilds for multi-domain changes.

## Development Workflow
- **Environment Setup**: Install dependencies from `requirements-dev.txt` and run `engine_test_suite.sh --smoke` before pushing changes.
- **Coding Standards**: TypeScript and Python must pass strict linting. Avoid catching broad exceptions and prefer explicit return types.
- **Documentation**: Update project artifacts concurrently with code. New features require entries in `docs/reviews/` describing rationale and acceptance evidence.
- **Analytics Integration**: When adding UI features, instrument them via `web/command-center/analytics` to capture survey responses and telemetry that inform roadmap adjustments.

## Validation Expectations
- Maintain reproducibility by checking notebooks and scripts into version control with parameter manifests.
- Supply success metric dashboards or tables under `results/` for every research initiative.
- Record anomalies and mitigations in `docs/security/RISK_REGISTER.md` to keep the governance council informed.

## Release Checklist (Snapshot)
- ✅ Phase objectives met and documented.
- ✅ Regression test suites green with links in PR description.
- ✅ User feedback loop updated (surveys, dashboards, response targets).
- ✅ Risk register updated with any new operational or security considerations.

For deeper onboarding, pair this guide with the onboarding checklist located in `docs/getting-started/ONBOARDING_CHECKLIST.md`.
