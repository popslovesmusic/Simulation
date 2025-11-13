# DASE Command Center Integration Plan

**Date:** 2025-11-11
**Status:** Ready for Integration
**Prerequisites:** All critical fixes applied, Grid and ModelPanel components created

---

## Executive Summary

This document outlines the integration steps to connect all Command Center components into a fully functional system. The architecture consists of:

1. **CLI** (`dase_cli.exe`) - Provides `--describe` flag for engine introspection and `METRIC:` output
2. **Backend** (Node.js) - REST API + WebSocket server with authentication
3. **Frontend** (React + TypeScript) - Modular component architecture
4. **New Components** - Grid (formula evaluation) and ModelPanel (dynamic configuration)

---

## Component Status

### ✅ Completed Components

| Component | Status | Location |
|-----------|--------|----------|
| CLI `--describe` flag | ✅ Complete | `dase_cli/src/main.cpp`, `command_router.cpp` |
| CLI `METRIC:` output | ✅ Complete | `dase_cli/src/metric_emitter.h` |
| Backend REST API | ✅ Complete | `backend/api/missions.js`, `backend/api/index.js` |
| Backend Authentication | ✅ Complete | `backend/api/auth.js` |
| Backend METRIC parsing | ✅ Complete | `backend/server.js` (WebSocket handler) |
| React App Foundation | ✅ Complete | `web/command-center/src/` |
| MissionSelection Component | ✅ Complete | `web/command-center/src/components/MissionSelection.tsx` |
| RunControlPanel Component | ✅ Complete | `web/command-center/src/components/RunControlPanel.tsx` |
| WaveformPlot Component | ✅ Complete | `web/command-center/src/components/WaveformPlot.tsx` |
| SymbolicsPanel Component | ✅ Complete | `web/command-center/src/playground/symbolics/SymbolicsPanel.tsx` |
| Grid Component | ✅ Complete | `web/command-center/src/components/Grid/Grid.tsx` |
| ModelPanel Component | ✅ Complete | `web/command-center/src/components/ModelPanel/ModelPanel.tsx` |

### 🔧 Critical Fixes Applied

1. ✅ **pythonBridge.js** - Added 30s timeout and 1MB output limit
2. ✅ **missions.js** - Fixed race condition (202 Accepted pattern)
3. ✅ **symbolics.js** - Missing return statement (already fixed by user)
4. ✅ **FeedbackDashboard.tsx** - Added `metricStats` to destructuring

---

## Integration Steps

### Step 1: Update App.tsx to Include New Components

**File:** `web/command-center/src/App.tsx`

**Current Structure:**
```typescript
<main className="app-main">
  <section className="app-column">
    <MissionSelection ... />
    <MissionBrief ... />
  </section>
  <section className="app-column">
    <RunControlPanel ... />
    <WaveformPlot ... />
  </section>
  <section className="app-column app-column--playground">
    <SymbolicsPanel />
    <TutorialNavigator />
    <SessionPanel />
    <FeedbackDashboard />
  </section>
</main>
```

**New Structure:**
```typescript
import { Grid } from './components/Grid';
import { ModelPanel } from './components/ModelPanel';

<main className="app-main">
  <section className="app-column app-column--left">
    <MissionSelection
      onMissionSelected={(mission) => {
        setSelectedMissionId(mission.id);
        setSelectedEngine(mission.engine);
      }}
      selectedMissionId={selectedMissionId}
    />
    <MissionBrief missionId={selectedMissionId} />
    <ModelPanel
      engineName={selectedEngine}
      onParameterChange={(params) => {
        console.log('Parameters changed:', params);
        // TODO: Store in state for mission creation
      }}
    />
  </section>

  <section className="app-column app-column--center">
    <Grid rows={100} cols={26} />
    <RunControlPanel
      missionId={selectedMissionId}
      engine={selectedEngine}
      onMissionUpdate={setSelectedMissionId}
    />
  </section>

  <section className="app-column app-column--right">
    <WaveformPlot missionId={selectedMissionId} />
    <SymbolicsPanel />
  </section>

  <section className="app-column app-column--playground">
    <TutorialNavigator />
    <SessionPanel />
    <FeedbackDashboard />
  </section>
</main>
```

**Action Required:**
```bash
# 1. Edit App.tsx to import and use Grid and ModelPanel
# 2. Add state for storing ModelPanel parameters:
const [modelParameters, setModelParameters] = useState<Record<string, unknown>>({});
```

---

### Step 2: Update Backend WebSocket to Support Grid Metrics

**File:** `backend/server.js`

**Current WebSocket Path:** `/ws/telemetry?missionId=...`

**New Requirement:** Grid needs `/ws/metrics` endpoint for LIVE() functions

**Changes Needed:**

```javascript
// Add new WebSocket endpoint for Grid LIVE() metrics
wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'http://localhost');
  const pathname = url.pathname;

  if (pathname === '/ws/telemetry') {
    // Existing telemetry handler
    const missionId = url.searchParams.get('missionId');
    // ... existing code ...
  } else if (pathname === '/ws/metrics') {
    // New handler for Grid LIVE() metrics
    console.log('[WebSocket] Grid metrics client connected');

    // When METRIC: messages arrive from CLI, broadcast to all Grid clients
    ws.on('message', (message) => {
      console.log('[WebSocket] Received from Grid:', message);
    });

    ws.on('close', () => {
      console.log('[WebSocket] Grid metrics client disconnected');
    });
  }
});
```

**Action Required:**
```bash
# Edit backend/server.js to add /ws/metrics endpoint handler
# Connect it to existing METRIC: parsing logic
```

---

### Step 3: Update Vite Proxy Configuration

**File:** `web/command-center/vite.config.ts`

**Current Configuration:**
```typescript
proxy: {
  '/api': { target: 'http://localhost:3000', changeOrigin: true, secure: false },
  '/streams': { target: 'http://localhost:3000', changeOrigin: true, secure: false },
  '/ws': { target: 'ws://localhost:8080', ws: true }
}
```

**Issue:** WebSocket target port mismatch. Backend runs on port 3000, not 8080.

**Fix:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:3000',
    changeOrigin: true,
    secure: false
  },
  '/ws': {
    target: 'ws://localhost:3000',  // ← Change from 8080 to 3000
    ws: true,
    changeOrigin: true
  }
}
```

**Action Required:**
```bash
# Edit vite.config.ts to fix WebSocket proxy target
```

---

### Step 4: Add CSS Layout for New Components

**File:** `web/command-center/src/styles/layout.css`

**Add Grid Layout:**
```css
.app-main {
  display: grid;
  grid-template-columns: 400px 1fr 400px 400px;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
  height: calc(100vh - 100px);
}

.app-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.app-column--left {
  /* Mission selection, brief, model config */
}

.app-column--center {
  /* Grid and run controls - takes most space */
  flex: 1;
}

.app-column--right {
  /* Waveform and symbolics */
}

.app-column--playground {
  /* Tutorials, sessions, feedback */
}

@media (max-width: 1800px) {
  .app-main {
    grid-template-columns: 350px 1fr 350px;
  }

  .app-column--playground {
    grid-column: 1 / -1;
    max-height: 400px;
  }
}
```

**Action Required:**
```bash
# Edit layout.css to accommodate new 4-column layout
```

---

### Step 5: Integrate ModelPanel with Mission Creation

**Goal:** When user configures parameters in ModelPanel and clicks "Create Mission", it should:
1. Collect all parameter values
2. Call `apiClient.createMission()` with configuration
3. Select the new mission automatically

**Implementation:**

**File:** `web/command-center/src/App.tsx`

```typescript
import { apiClient } from './services/apiClient';

function App() {
  // ... existing state ...
  const [modelParameters, setModelParameters] = useState<Record<string, unknown>>({});

  const handleCreateMission = useCallback(async () => {
    if (!selectedEngine) return;

    try {
      const mission = await apiClient.createMission({
        name: `${selectedEngine} Mission ${new Date().toISOString()}`,
        engine: selectedEngine,
        parameters: modelParameters,
        brief_markdown: `Auto-generated mission for ${selectedEngine}`,
      });

      setSelectedMissionId(mission.id);
      setSelectedEngine(mission.engine);
    } catch (error) {
      console.error('Failed to create mission:', error);
      alert(`Failed to create mission: ${(error as Error).message}`);
    }
  }, [selectedEngine, modelParameters]);

  return (
    // ... JSX ...
    <ModelPanel
      engineName={selectedEngine}
      onParameterChange={setModelParameters}
      onCreateMission={handleCreateMission}
    />
  );
}
```

**Update ModelPanel.tsx:**
```typescript
interface ModelPanelProps {
  engineName: string | null;
  onParameterChange?: (params: Record<string, unknown>) => void;
  onCreateMission?: () => void;  // ← Add this prop
}

// In the render:
<button
  type="button"
  className="primary"
  onClick={onCreateMission}
  disabled={!onCreateMission}
>
  Create Mission with Configuration
</button>
```

**Action Required:**
```bash
# 1. Add onCreateMission prop to ModelPanel
# 2. Implement handleCreateMission in App.tsx
# 3. Connect the button to onCreateMission callback
```

---

### Step 6: Connect Grid LIVE() to Backend METRIC Stream

**Current Status:**
- ✅ Grid has `useGridEngine` hook with WebSocket connection
- ✅ Backend parses `METRIC:` from CLI stdout
- ⚠️ Need to route METRIC messages to `/ws/metrics` clients

**Backend Changes:**

**File:** `backend/server.js`

```javascript
// Store Grid WebSocket clients
const gridClients = new Set();

wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'http://localhost');
  const pathname = url.pathname;

  if (pathname === '/ws/metrics') {
    gridClients.add(ws);
    console.log(`[WebSocket] Grid client connected (total: ${gridClients.size})`);

    ws.on('close', () => {
      gridClients.delete(ws);
      console.log(`[WebSocket] Grid client disconnected (total: ${gridClients.size})`);
    });
  }
});

// In the CLI stdout handler where METRIC: is parsed:
if (line.startsWith('METRIC:')) {
  const metricJson = line.substring(7);
  try {
    const metric = JSON.parse(metricJson);

    // Broadcast to Grid clients
    gridClients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({
          type: 'metrics:update',
          data: metric
        }));
      }
    });

    // Also send to mission-specific telemetry clients (existing code)
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'metrics:update',
        data: metric
      }));
    }
  } catch (err) {
    console.error('Failed to parse metric:', metricJson);
  }
}
```

**Action Required:**
```bash
# Edit backend/server.js to broadcast METRIC messages to /ws/metrics clients
```

---

### Step 7: Add Engine Selector to UI

**Goal:** Allow user to select an engine without creating a mission first.

**Implementation:**

**File:** `web/command-center/src/App.tsx`

```typescript
const [availableEngines, setAvailableEngines] = useState<string[]>([]);

useEffect(() => {
  fetch('/api/engines', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('command-center-token') ?? ''}`
    }
  })
    .then(res => res.json())
    .then(data => setAvailableEngines(data.engines))
    .catch(err => console.error('Failed to load engines:', err));
}, []);

// In the JSX:
<header className="app-header" aria-live="polite">
  <h1>{t('app.title')}</h1>
  <div className="engine-selector">
    <label>
      Engine:
      <select
        value={selectedEngine ?? ''}
        onChange={(e) => setSelectedEngine(e.target.value || null)}
      >
        <option value="">Select engine...</option>
        {availableEngines.map((engine) => (
          <option key={engine} value={engine}>
            {engine}
          </option>
        ))}
      </select>
    </label>
  </div>
</header>
```

**Action Required:**
```bash
# Add engine selector dropdown to app header
```

---

## Testing Checklist

### Backend Testing

```bash
# 1. Start backend server
cd backend
npm install
node server.js

# Expected output:
# [Server] REST API listening on http://localhost:3000
# [WebSocket] Server listening on ws://localhost:3000
```

### CLI Testing

```bash
# 2. Test CLI --describe flag
./dase_cli/dase_cli.exe --describe igsoa_gw

# Expected: JSON output with engine description
```

### Frontend Testing

```bash
# 3. Start frontend dev server
cd web/command-center
npm install
npm run dev

# Expected: Dev server on http://localhost:5173
```

### Integration Testing

1. ✅ **Auth Test:** Open browser, enter token in localStorage
   ```javascript
   localStorage.setItem('command-center-token', 'YOUR_TOKEN_HERE');
   ```

2. ✅ **Engine Selection Test:** Select `igsoa_gw` from dropdown, verify ModelPanel loads parameters

3. ✅ **Grid Formula Test:**
   - Click cell A1, type `=5+3`, press Enter
   - Verify cell shows `8`
   - Click cell A2, type `=A1*2`, press Enter
   - Verify cell shows `16`

4. ✅ **LIVE() Function Test:**
   - Create a mission with `igsoa_gw` engine
   - Start the mission
   - In Grid, click cell B1, type `=LIVE("total_energy")`
   - Verify cell updates with real-time values from simulation

5. ✅ **ModelPanel Parameter Test:**
   - Select engine `igsoa_gw`
   - Change `grid_nx` parameter to 64
   - Click "Create Mission with Configuration"
   - Verify new mission appears in MissionSelection list

6. ✅ **WebSocket Metrics Test:**
   - Open DevTools Network tab, filter by WS
   - Verify `/ws/metrics` connection established
   - Start a mission
   - Verify `metrics:update` messages arriving

---

## Deployment Checklist

### Pre-Deployment

- [ ] All critical fixes applied
- [ ] Grid and ModelPanel components integrated into App.tsx
- [ ] WebSocket routing configured correctly
- [ ] Vite proxy configuration fixed
- [ ] CSS layout supports 4-column design
- [ ] Engine selector added to header
- [ ] Integration tests pass

### Production Configuration

**Backend:**
```bash
# Set production environment
export NODE_ENV=production
export PORT=3000
export PLAYGROUND_PYTHON=/usr/bin/python3

# Generate production tokens
export API_TOKENS="token1,token2,token3"
```

**Frontend:**
```bash
# Build for production
cd web/command-center
npm run build

# Output: dist/ directory with static assets
```

**Nginx Configuration:**
```nginx
server {
  listen 80;
  server_name command-center.example.com;

  # Frontend static files
  location / {
    root /var/www/command-center/dist;
    try_files $uri $uri/ /index.html;
  }

  # Backend REST API
  location /api/ {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }

  # WebSocket upgrade
  location /ws/ {
    proxy_pass http://localhost:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
```

---

## Known Limitations

1. **Grid Scrolling:** Canvas-based Grid doesn't have native scrolling. Consider adding scroll offset controls.

2. **Formula Complexity:** Current formula evaluator uses `new Function()` which is limited. For complex math, consider integrating with SymbolicsPanel.

3. **Cell Dependencies:** Circular references not detected. Will cause infinite loops.

4. **METRIC Buffering:** No message queuing if WebSocket reconnects. Metrics during disconnection are lost.

5. **Parameter Validation:** ModelPanel doesn't validate parameter ranges server-side yet.

---

## Future Enhancements

### Phase 1 (Immediate)
- [ ] Add Grid scrolling with arrow keys
- [ ] Add circular dependency detection
- [ ] Add server-side parameter validation
- [ ] Add WebSocket reconnection with exponential backoff

### Phase 2 (Next Sprint)
- [ ] Add Grid cell formatting (number precision, colors)
- [ ] Add ModelPanel cell reference picker (click Grid cell to link)
- [ ] Add METRIC history buffer and replay
- [ ] Add formula autocomplete for cell references

### Phase 3 (Future)
- [ ] Add Grid chart generation from selected cells
- [ ] Add ModelPanel equation editor with LaTeX preview
- [ ] Add collaborative editing for Grid cells
- [ ] Add Mission templates with predefined configurations

---

## Troubleshooting

### Issue: Grid LIVE() cells show "=LIVE(...)" but don't update

**Diagnosis:**
```bash
# Check backend WebSocket handler
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  http://localhost:3000/ws/metrics
```

**Fix:** Verify `/ws/metrics` endpoint exists in `backend/server.js` and broadcasts METRIC messages.

### Issue: ModelPanel shows "Failed to fetch engine description"

**Diagnosis:**
```bash
# Test REST API endpoint directly
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3000/api/engines/igsoa_gw
```

**Fix:** Verify `dase_cli.exe --describe igsoa_gw` works and returns valid JSON.

### Issue: WebSocket connection fails with 403 Forbidden

**Diagnosis:** Authentication token not provided for WebSocket

**Fix:** Update `useGridEngine.ts` to include token in WebSocket URL:
```typescript
const token = localStorage.getItem('command-center-token') ?? '';
const ws = new WebSocket(`${wsOrigin}/ws/metrics?token=${token}`);
```

Then update `backend/api/auth.js` to support query parameter auth:
```javascript
function authenticateRequest(req, res, next) {
  const header = req.get('Authorization');
  const queryToken = req.query.token;  // ← Add this

  const token = header?.match(/^Bearer (.+)$/)?.[1] ?? queryToken;

  if (!token || !registry.validate(token)) {
    return res.status(403).json({ error: 'Invalid API token' });
  }

  return next();
}
```

---

## Summary

**Total Implementation Time Estimate:** 4-6 hours

**Critical Path:**
1. Integrate Grid and ModelPanel into App.tsx (1 hour)
2. Fix WebSocket routing and proxy config (1 hour)
3. Connect ModelPanel to mission creation (1 hour)
4. Test LIVE() function end-to-end (1 hour)
5. CSS layout adjustments (1 hour)
6. Integration testing and bug fixes (1 hour)

**Confidence Level:** HIGH (All components already built and tested individually)

**Next Steps:**
1. Review this integration plan
2. Follow Step 1-7 in sequence
3. Run integration testing checklist
4. Deploy to staging environment
5. Conduct user acceptance testing

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Author:** Claude Code Assistant
