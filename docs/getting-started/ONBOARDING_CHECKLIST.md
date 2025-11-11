# IGSOA Simulation Onboarding Checklist

Use this checklist to onboard new contributors within the current roadmap phase. Each item should be completed within the first two weeks unless otherwise negotiated with the engineering lead.

## Week 0–1: Access & Orientation
- [ ] Gain repository access and review `AGENTS.md` for phase context.
- [ ] Install engine and UI dependencies (`requirements-dev.txt`, `npm install` in `web/command-center`).
- [ ] Run `engine_test_suite.sh --smoke` and `npm run build` to validate the local environment.
- [ ] Read the `IGSOA_PROJECT_ROADMAP.md` and the latest entries in `docs/reviews/`.

## Week 1–2: Hands-On Ramp
- [ ] Pair with a senior contributor to walk through the mission command workflow in `web/command-center`.
- [ ] Explore active research branches in `analysis/projects/` and note outstanding success metrics.
- [ ] Shadow a cross-functional review to understand governance expectations.
- [ ] Submit a documentation PR updating this checklist with any missing context discovered during onboarding.

## Continuous Expectations
- [ ] Capture user feedback using the survey templates in `web/command-center/analytics` for any UI-affecting changes.
- [ ] Log operational or security risks in `docs/security/RISK_REGISTER.md` whenever new failure modes are discovered.
- [ ] Participate in monthly research syncs to review progress against success metrics.

> 🎯 **Completion Criteria**: New contributors should demonstrate a full walkthrough of the Command Center analytics dashboard, deploy a research notebook from `analysis/projects/`, and highlight at least one risk mitigation or documentation improvement opportunity.
