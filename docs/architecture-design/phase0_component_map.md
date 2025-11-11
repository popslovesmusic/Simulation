# Phase 0 Component Map

This document summarizes the repository layout for the three primary subsystems that participate in Phase 0 (baseline validation):

- **Backend service (`backend/`)**
- **Offline analysis artifacts (`igsoa_analysis/`)**
- **Command Center web client (`web/`)**

## Backend (`backend/`)

| Area | Purpose | Key Files |
|------|---------|-----------|
| HTTP + WebSocket entry point | Hosts REST endpoints for engine discovery and WebSocket bridge for mission control. Uses Express for HTTP, `ws` for bidirectional messaging, and spawns `dase_cli.exe` processes on demand. | `server.js` |
| Runtime configuration | Defines npm metadata, runtime scripts, and dependencies. | `package.json` |
| Legacy snapshot | Preserves a previous server implementation for reference; not part of the active runtime. | `server.js.backup` |
| Dependencies | Installed locally under `node_modules/`; no committed source changes should occur here. | `node_modules/` |

**Operational boundary**

- Owns all network-facing logic and CLI process supervision.
- Emits simulation events to the front end via WebSockets.
- Shares no source code with the front end; communication is JSON over HTTP/WebSocket.
- Does **not** include physics logic—the compiled engines remain external binaries invoked via CLI.

## IGSOA Analysis (`igsoa_analysis/`)

| Area | Purpose | Key Files |
|------|---------|-----------|
| Analytical summaries | Text report describing state statistics for a representative mission run at \(R_c = 0.5\). | `analysis_report_R0.5.txt` |
| Visualization assets | PNG exports of spectral power, spatial correlation, and state profile plots derived from offline notebooks. | `power_spectra_R0.5.png`, `spatial_correlation_R0.5.png`, `state_profiles_R0.5.png` |

**Operational boundary**

- Contains **derived artifacts only** (reports, plots) that validate physics behavior post-simulation.
- Source notebooks/tools reside elsewhere (`analysis/`); this directory packages the curated outputs used for reviews.
- No executable code is run from this directory during CI or deployment.

## Command Center Web Client (`web/`)

| Area | Purpose | Key Files |
|------|---------|-----------|
| Entry point | Static HTML shell that loads ES6 modules and CSS bundles. | `web/index.html` |
| Styling | Theme, grid, terminal, and component panel styles, segmented by concern. | `web/css/base.css`, `header.css`, `grid.css`, `terminal.css`, `components.css` |
| Application bootstrap | Initializes the `DASEApp`, wires modules, and manages lifecycle events. | `web/js/main.js` |
| Configuration | Central configuration for API endpoints and environment toggles. | `web/js/config.js` |
| Components | ES6 modules for UI widgets (currently terminal output). | `web/js/components/Terminal.js` |
| Network layer | WebSocket client and REST fallback for communicating with the backend. | `web/js/network/EngineClient.js` |
| Legacy archive | Preserves pre-modular implementations for reference without affecting live builds. | `web/archive/` |

**Operational boundary**

- Consumes backend APIs only through HTTP/WebSocket; no direct filesystem access.
- Responsible for rendering mission dashboards and waveform telemetry.
- Additional UI modules will live under `web/js/components/` (widgets) and `web/js/network/` (data services).
- Assets under `web/archive/` remain read-only and must not be imported into the modular build without review.

## Cross-cutting notes

- Shared validation artifacts referenced by all components (e.g., waveform CSV/JSON) live under `results/` and `analysis/`.
- Phase 0 tasks should treat each subsystem as independently deployable and communicate strictly through documented APIs and artifacts.
