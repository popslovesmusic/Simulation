# Command Center Analytics Stack

This directory configures the user feedback loops that drive roadmap prioritization for the Command Center. Import definitions from this folder when instrumenting UI features.

## Components
- **Surveys (`feedbackConfig.ts`)** – structured surveys surfaced in the UI to capture mission operator sentiment and prioritization signals.
- **Telemetry Dashboards (`telemetryDashboards.ts`)** – declarative metric definitions powering trend visualizations inside the Feedback Dashboard component.
- **Channel Registry (`channelRegistry.ts`)** – central registry describing event routing and success thresholds.

## Workflow
1. Update survey or telemetry definitions here.
2. Ensure UI surfaces render new definitions via `useFeedbackLoop`.
3. Export summarized insights to cross-functional reviews and update `docs/security/RISK_REGISTER.md` if risk thresholds are exceeded.

All changes must include validation notes in the associated PR.
