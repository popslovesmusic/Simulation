# Code Review: Bridge Servers and Mission Backend (2025-03)

## Scope
This review examined the Python bridge servers and Node.js backend that connect the DVSL/DASE interfaces to the native simulation engine. The focus was on correctness, security, performance bottlenecks, and how well each function fulfills its responsibilities. Reviewed artifacts include:

- `src/python/bridge_server_improved.py`
- `src/python/bridge_server.py`
- `src/python/igsoa_logging.py`
- `backend/server.js`
- `backend/api/*` (missions, authentication, playground routers, and Python bridge helpers)
- `backend/mission_runtime/*`

## High-Severity Findings

### WebSocket mission metrics use unsynchronized shared state
`ws_handler` in `bridge_server_improved.py` increments counters (`performance_metrics["active_simulations"]` and `performance_metrics["total_requests"]`) from multiple threads without a lock or atomic helper, which risks negative counts or lost updates under concurrent workloads (lines 244-316). The metrics dictionary is also directly exposed through `/api/status`, so stale or corrupted counts leak into the UI. Wrap updates in a `threading.Lock` or replace the mutable dictionary with a thread-safe abstraction.

### Analysis endpoint can double-respond after timeout
The `/api/analysis` route in `backend/server.js` starts a five-minute timeout but never cancels it when the Python subprocess completes (lines 192-260). If the subprocess finishes quickly, Express still attempts to send the timeout response after five minutes, triggering `ERR_HTTP_HEADERS_SENT` and leaving clients with misleading failures. Track the timeout handle and clear it inside the `close` handler before sending the success payload.

### Tutorial/glossary slug validation vulnerable to traversal
`readDocument` in `backend/api/playground/tutorials.js` uses `path.join` and a string-prefix check to block `..` segments (lines 35-47). Paths such as `../secrets/system` still pass the `startsWith` check because the joined string retains the tutorials directory prefix, enabling directory traversal. Normalize with `path.resolve` (for both the directory and candidate path) and compare the resolved paths before reading from disk.

### Security tokens printed to application logs
`backend/server.js` logs every API token on startup (line 60). Because tokens authorize mission control and engine execution, emitting them to stdout/console is a direct credential disclosure. Remove this log or replace it with a count-only message.

## Medium-Severity Findings

### Mission launch lifecycle is only stubbed
`launchSimulation`/`stopSimulation` in `backend/server.js` simply mutate status fields (lines 30-43), yet API handlers return success responses implying a real run loop. Without process orchestration or error propagation, `/missions` reports will permanently show `running`, and clients cannot tell whether mission execution actually started. Either connect these hooks to the CLI/WebSocket orchestration layer or downgrade the API contract to “queued only.”

### Mission commands cannot be correlated with CLI responses
The WebSocket client map stores an unused `pendingCommands` map (line 374). Commands sent to the CLI are never tagged with request IDs, so there is no way to match responses or timeouts back to their originating mission action. Either remove the dead field or implement a correlation mechanism that satisfies the pending-command semantics implied by the map.

### WebSocket authentication header parsing incompatible with REST path
REST endpoints mandate `Authorization: Bearer <token>` headers, but the WebSocket server treats the header value as the bare token (lines 283-299). Clients that reuse the REST auth middleware will send the `Bearer` prefix and be rejected even with valid credentials. Normalize the WebSocket branch to strip the prefix before validation.

### Python analysis process lacks timeout cleanup and failure hooks
`runPythonTool` assumes the target script returns a single JSON payload and kills the process when stdout exceeds 1 MB (lines 14-76). Any script that logs status messages or writes multi-line JSON will trip parsing errors. Consider framing JSON output with delimiters or switching to structured IPC (pipes, gRPC) to avoid fragility.

## Low-Severity Findings

- `COMMAND_TIMEOUT_MS` in `backend/server.js` is never referenced, suggesting an unfinished guard for slow CLI commands (line 22). Implement or remove to avoid confusion.
- `api_benchmark` assumes the C++ metrics object exposes every attribute accessed (lines 127-178). Defensive `getattr` calls (as already used elsewhere in the file) would prevent AttributeErrors when the engine binary changes.
- `backend/api/playground/pythonBridge.js` accepts arbitrary relative script paths, enabling callers to request files outside `services/` if they supply values with `../` segments. Add a whitelist or resolve-and-verify step before spawning Python.
- `backend/api/missions.js` immediately sets missions to `running` even though `launchSimulation` may still be pending (lines 18-49). Distinguish between “queued,” “launching,” and “running” to give operators clearer feedback.

## Positive Observations

- `MissionSchemaValidator` and `MissionPlanner` offer well-structured validation with clear error/warning separation and JSON export, providing a solid foundation for mission QA.
- The WebSocket server enforces buffer and process-count limits, reducing the risk of uncontrolled resource growth.

## Recommendations

1. Prioritize thread-safety fixes in the Python bridge to keep system metrics trustworthy.
2. Harden Express routes and WebSocket handlers: clear timeouts, sanitize log output, align authentication parsing, and enforce filesystem boundaries.
3. Implement real mission lifecycle hooks or downgrade API messaging until the orchestration layer is available.
4. Introduce automated tests (unit or integration) for slug handling, analysis timeouts, and WebSocket auth to prevent regressions.

## Suggested Follow-Up Work
- Create a security hardening ticket focused on filesystem traversal, token confidentiality, and process spawning safeguards across both services.
- Profile the CLI bridge under concurrent missions after thread-safety changes to validate that metrics and mission state remain consistent.
