# DASE Analog Excel - CLI Integration Plan

## Executive Summary

The **DASE Analog Excel** web interface (`dase_interface.html`) is a visual programming environment for analog computing that uses a spreadsheet-like grid to design and simulate circuits using symbolic operators (amplifiers, integrators, IGS-OA dynamics nodes, etc.).

**Current Status:** Mock implementation with placeholder backend
**Goal:** Integrate with the working DASE CLI (`dase_cli.exe`) for real-time high-performance simulation

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  DASE Analog Excel (Web UI)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Grid Interface (DVSL - Digital Visual Symbol Lang)  │  │
│  │  - Drag & drop symbols (△, ∫, Φ, ~, etc.)           │  │
│  │  - Formula editor (=△(A1, gain=2.0))                 │  │
│  │  - Properties panel with parameter controls           │  │
│  │  - Simulation controls (Run/Pause/Stop)              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Terminal Interface (DASE CLI Bridge)                │  │
│  │  - Commands: create, run, metrics, destroy           │  │
│  │  - JSON command generation                           │  │
│  │  - Mock backend (currently)                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                 ┌──────────────────────┐
                 │  Integration Layer   │  ← TO BE IMPLEMENTED
                 │  (WebSocket/HTTP)    │
                 └──────────────────────┘
                            ↓
            ┌───────────────────────────────┐
            │    DASE CLI (dase_cli.exe)    │
            │  ✅ Phase 4B Engine (AVX2)    │
            │  ✅ IGSOA Complex Engine       │
            │  ✅ JSON Command Interface     │
            │  ✅ Performance: 5B ops/sec    │
            └───────────────────────────────┘
```

---

## Current Capabilities Analysis

### ✅ **What's Already Working (Web UI)**

1. **Visual Grid Interface**
   - 50 rows × 26 columns spreadsheet
   - Cell selection, navigation (arrow keys)
   - Copy/paste/cut/duplicate functionality
   - Formula bar with live editing

2. **Symbol Library (DVSL)**
   - **Core Analog**: Amplifier (△), Integrator (∫), Summer (∑), Multiplier (⊗), etc.
   - **IGS-OA Dynamics**: Field Node (Φ), Stochastic OA (Ξ), Coupling (R), Stress Tensor (O)
   - **Signal Generators**: Sine (~), Square (⊓), Noise (⋈)
   - **Neural**: Neuron (🧠), Synapse (🔗)
   - **Microwave/RF**: Oscillators, Waveguides, Resonant Cavities

3. **Formula Presets**
   - 50+ pre-built circuit configurations
   - Categories: Signal Processing, IGS-OA, Oscillators, Math Ops, Neural Networks, Control Systems

4. **Properties Panel**
   - Real-time parameter adjustment
   - Symbol configuration
   - Cell type/value display

5. **Simulation Controls UI**
   - Time step configuration (1-100ms)
   - Simulation speed control (0.1x-5.0x)
   - Performance metrics display (planned)
   - Circuit analysis (active cells, dependencies)

6. **Terminal Interface**
   - Command parser (`sendCLIToBackend` function)
   - JSON command generation
   - Currently uses **mock responses** (lines 1708-1786)

7. **Project Management**
   - Save/Load (localStorage currently)
   - Modified state tracking
   - Export to JSON structure

### ⚠️ **What Needs Integration (Mock → Real)**

The following are currently **mocked** and need to connect to the real DASE CLI:

| Function | Current (Mock) | Target (Real) | Line # |
|----------|---------------|---------------|--------|
| `sendCLIToBackend()` | Returns mock JSON | WebSocket/HTTP to CLI | 1708 |
| Engine creation | Sets `activeEngineId = 'engine_001'` | Real CLI response | 1726 |
| Mission execution | Returns fake metrics | Real AVX2 simulation | 1734 |
| Performance metrics | Hardcoded 5.3B ops/sec | Real-time from CLI | 1746 |
| Engine lifecycle | No actual process | Start/stop dase_cli.exe | - |

---

## Integration Requirements

### **Phase 1: Backend Process Management** ⭐ **CRITICAL**

#### 1.1 DASE CLI Process Wrapper

**Options:**

**A. Node.js Backend (Recommended)**
```javascript
// server.js (Node.js + Express + child_process)
const express = require('express');
const { spawn } = require('child_process');
const WebSocket = require('ws');

const app = express();
const wss = new WebSocket.Server({ port: 8080 });

// Spawn DASE CLI process
const daseProcess = spawn('dase_cli.exe', [], {
    cwd: 'D:\\isoG\\New-folder\\sase_amp_fixed\\dase_cli'
});

wss.on('connection', (ws) => {
    ws.on('message', (jsonCommand) => {
        // Write to CLI stdin
        daseProcess.stdin.write(jsonCommand + '\n');
    });

    // Read from CLI stdout
    daseProcess.stdout.on('data', (data) => {
        ws.send(data.toString());
    });
});

app.listen(3000);
```

**B. Python Backend (Alternative)**
```python
# server.py (Flask + subprocess)
from flask import Flask, request
from flask_socketio import SocketIO, emit
import subprocess
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

dase_process = subprocess.Popen(
    ['dase_cli.exe'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

@socketio.on('dase_command')
def handle_command(json_data):
    dase_process.stdin.write(json_data + '\n')
    dase_process.stdin.flush()

    result = dase_process.stdout.readline()
    emit('dase_response', result)

if __name__ == '__main__':
    socketio.run(app, port=5000)
```

**C. Electron App (Full Desktop Integration)**
- Package entire system as standalone desktop app
- Direct IPC between renderer (UI) and main process (CLI)
- No network layer needed

**Recommendation:** Start with **Option A (Node.js)** for simplicity and WebSocket real-time communication.

#### 1.2 WebSocket Client Update (Web UI)

Replace `sendCLIToBackend()` mock function:

```javascript
// Add at top of script section (line ~835)
const ws = new WebSocket('ws://localhost:8080');

ws.onopen = () => {
    addTerminalLine('Connected to DASE CLI backend', 'terminal-success');
};

ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    handleDaseResponse(response);
};

ws.onerror = (error) => {
    addTerminalLine(`WebSocket error: ${error}`, 'terminal-error');
};

ws.onclose = () => {
    addTerminalLine('Disconnected from DASE CLI backend', 'terminal-warning');
};

// REPLACE sendCLIToBackend (line 1708) with:
async function sendCLIToBackend(jsonCommand) {
    return new Promise((resolve, reject) => {
        const commandObj = JSON.parse(jsonCommand);
        const requestId = Date.now().toString();

        // Store pending request
        pendingRequests.set(requestId, { resolve, reject, command: commandObj.command });

        // Add request ID to command
        commandObj.requestId = requestId;

        // Send via WebSocket
        ws.send(JSON.stringify(commandObj));

        // Timeout after 30 seconds
        setTimeout(() => {
            if (pendingRequests.has(requestId)) {
                pendingRequests.delete(requestId);
                reject(new Error('Command timeout'));
            }
        }, 30000);
    });
}

// Add response handler
function handleDaseResponse(response) {
    const requestId = response.requestId;
    if (pendingRequests.has(requestId)) {
        const { resolve } = pendingRequests.get(requestId);
        pendingRequests.delete(requestId);
        resolve(response);
    }
}

const pendingRequests = new Map();
```

---

### **Phase 2: DVSL → DASE Command Translation** ⭐⭐

The web UI uses symbolic formulas (DVSL), but the CLI expects:
- `num_steps`
- `iterations_per_node`
- Engine configuration

**Challenge:** How to convert a DVSL circuit into a DASE mission?

#### 2.1 Circuit Compilation Strategy

**Option A: Grid-to-Matrix Mapping**
- Each DVSL cell becomes a node in the DASE engine
- Cell formulas define coupling/interaction rules
- Parameters extracted from symbols

**Option B: Custom Interpreter Layer**
- Build a DVSL→C++ code generator
- Compile circuits into custom mission logic
- Requires extending dase_capi.cpp

**Option C: Hybrid Approach (Recommended)**
1. Parse active cells in grid
2. Extract dependency graph (which cells reference which)
3. Map to DASE engine nodes (1 cell = N nodes depending on complexity)
4. Configure engine based on circuit topology
5. Run mission with auto-generated parameters

#### 2.2 Example Translation

**DVSL Grid:**
```
A1: =~(freq=440, amp=1.0)     // Sine oscillator
A2: =△(A1, gain=2.0)          // Amplifier
A3: =∫(A2, dt=0.01)           // Integrator
```

**Translated to DASE Commands:**
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":3}}
{"command":"set_node_config","params":{"engine_id":"engine_001","nodes":[
    {"id":0,"type":"oscillator","freq":440,"amp":1.0},
    {"id":1,"type":"amplifier","gain":2.0,"input":0},
    {"id":2,"type":"integrator","dt":0.01,"input":1}
]}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1000,"iterations_per_node":20}}
```

**Problem:** Current CLI doesn't support `set_node_config` — needs extension!

---

### **Phase 3: Performance Visualization** ⭐

#### 3.1 Real-Time Metrics Update

Update simulation panel metrics from actual CLI responses:

```javascript
// In handleDaseCliCommand, after successful 'metrics' response:
if (result.status === 'success' && result.command === 'get_metrics') {
    document.getElementById('opsPerSec').textContent =
        formatNumber(result.result.ops_per_sec);
    document.getElementById('simTime').textContent =
        formatTime(result.result.total_operations / result.result.ops_per_sec);
    // ... etc
}
```

#### 3.2 Live Waveform Display (Future)

- Canvas-based oscilloscope view
- Real-time streaming of node values
- Requires extending CLI to output time-series data

---

### **Phase 4: Advanced Features** ⭐⭐⭐

1. **Circuit Validation**
   - Detect feedback loops
   - Warn about unstable configurations
   - Suggest parameter adjustments

2. **Auto-Optimization**
   - Use CLI metrics to tune time step
   - Dynamic adjustment based on error estimates

3. **Multi-Engine Support**
   - Run multiple circuits simultaneously
   - Compare Phase 4B vs IGSOA Complex performance

4. **Cloud Integration**
   - Upload/download projects to Firestore
   - Share circuits with community
   - Version control

---

## Implementation Roadmap

### **Sprint 1: Core Backend (Week 1)**
- [ ] Set up Node.js server with Express
- [ ] Implement WebSocket bridge to dase_cli.exe
- [ ] Test basic command flow (create → run → metrics)
- [ ] Update web UI to use WebSocket instead of mock
- [ ] Verify real engine creation and destruction

**Deliverables:**
- `server.js` (Node backend)
- Updated `sendCLIToBackend()` in HTML
- Test script demonstrating end-to-end flow

### **Sprint 2: Command Translation (Week 2)**
- [ ] Implement DVSL parser (extract active cells)
- [ ] Build dependency graph analyzer
- [ ] Create DASE command generator
- [ ] Test with simple circuits (oscillator → amplifier → integrator)
- [ ] Handle error cases (invalid formulas, circular refs)

**Deliverables:**
- `dvsl_compiler.js` module
- Unit tests for formula parsing
- Integration test with 5+ sample circuits

### **Sprint 3: UI Polish & Metrics (Week 3)**
- [ ] Connect simulation controls to real CLI
- [ ] Update performance metrics display
- [ ] Add progress indicators for long-running missions
- [ ] Implement auto-refresh for metrics
- [ ] Error handling and user feedback

**Deliverables:**
- Updated simulation panel
- Real-time metrics dashboard
- Error message improvements

### **Sprint 4: Testing & Documentation (Week 4)**
- [ ] End-to-end testing with all symbol types
- [ ] Performance benchmarking (latency, throughput)
- [ ] User documentation (how to build circuits)
- [ ] Developer API docs (for extending symbols)
- [ ] Deployment guide

**Deliverables:**
- Test suite (automated)
- User manual (PDF/Markdown)
- Developer guide
- Docker container for easy deployment

---

## Critical Gaps & Solutions

### **Gap 1: CLI Doesn't Support Node-Level Configuration**

**Problem:** The DASE CLI only accepts `num_steps` and `iterations_per_node`, but doesn't allow configuring individual node behaviors (oscillator, amplifier, etc.).

**Solutions:**

**A. Extend the CLI (Recommended Long-Term)**
Add new C API functions:
```cpp
// dase_capi.h
void dase_set_node_type(DaseEngineHandle, uint32_t node_id, const char* type, const char* params_json);
void dase_set_node_coupling(DaseEngineHandle, uint32_t from_id, uint32_t to_id, double strength);
```

Expose via CLI commands:
```json
{"command":"configure_node","params":{"engine_id":"engine_001","node_id":5,"type":"amplifier","gain":2.0}}
{"command":"set_coupling","params":{"engine_id":"engine_001","from":5,"to":6,"strength":0.8}}
```

**B. Use Mission Parameters Creatively (Short-Term)**
Encode circuit topology in `iterations_per_node` or other numeric parameters:
- Treat each "iteration" as a different node type
- Use `num_steps` to control circuit complexity
- **Limitation:** Very restrictive, not scalable

**C. Pre-Generate Mission Profiles (Hybrid)**
- Create a library of pre-compiled mission types (oscillator banks, filter chains, etc.)
- Web UI selects appropriate mission template based on DVSL grid
- Limited flexibility but faster time-to-market

**Recommendation:** Implement **Solution C** for MVP, then migrate to **Solution A** for v2.0.

### **Gap 2: No Time-Series Output**

**Problem:** CLI only returns aggregate metrics (ns/op, total ops), not individual node values over time.

**Solutions:**

**A. Add Streaming Output**
```cpp
// New CLI command
{"command":"stream_values","params":{"engine_id":"engine_001","nodes":[0,1,2],"frequency":10}}
// Returns: {"time":0.1,"values":[1.2, 3.4, 5.6]}
```

**B. Batch Export**
```json
{"command":"export_timeseries","params":{"engine_id":"engine_001","format":"csv","file":"output.csv"}}
```

**C. Post-Simulation Retrieval**
```cpp
void dase_get_node_history(DaseEngineHandle, uint32_t node_id, double* output_buffer, uint64_t buffer_size);
```

### **Gap 3: IGS-OA Symbols Not Mapped**

**Problem:** The web UI has symbols for Φ (IGS Field), Ξ (Stochastic OA), etc., but these don't correspond to any CLI functionality.

**Solution:**
1. Use `igsoa_complex` engine type
2. Map Φ → base node with specific `R_c` value
3. Map Ξ → stochastic perturbation (requires CLI extension)
4. Map R → coupling radius configuration

**For MVP:** Only support basic analog symbols with Phase 4B engine, mark IGS-OA as "experimental" until CLI is extended.

---

## Testing Strategy

### Unit Tests
- [x] Formula parser (validate DVSL syntax)
- [ ] WebSocket reconnection logic
- [ ] Command queue management
- [ ] Error handling (engine not found, timeout, etc.)

### Integration Tests
- [ ] Create engine → Run mission → Get metrics → Destroy (full lifecycle)
- [ ] Multiple engines in parallel
- [ ] Grid persistence (save/load)
- [ ] Concurrent user sessions

### Performance Tests
- [ ] Measure WebSocket latency (< 10ms target)
- [ ] Test with 100+ active cells
- [ ] Stress test with 10,000 step missions
- [ ] Memory leak detection (long-running sessions)

### User Acceptance Tests
- [ ] Build a simple oscillator circuit
- [ ] Create a PI controller and verify stability
- [ ] Design a neural network with multiple layers
- [ ] Load a saved project and resume simulation

---

## Deployment Options

### **Option 1: Local Desktop App (Electron)**
**Pros:**
- No server setup required
- Direct CLI access
- Offline capable
- Easy distribution (.exe installer)

**Cons:**
- Larger bundle size
- Platform-specific builds

### **Option 2: Client-Server (Web Browser + Node Backend)**
**Pros:**
- Access from any device
- Centralized compute (cloud GPU potential)
- Easier updates (just redeploy server)

**Cons:**
- Network latency
- Requires hosting
- Security considerations

### **Option 3: Hybrid (PWA + Local Backend)**
**Pros:**
- Best of both worlds
- Works offline once installed
- Can connect to cloud for sharing

**Cons:**
- More complex architecture

**Recommendation:** Start with **Option 2** for development, then package as **Option 1** (Electron) for v1.0 release.

---

## File Structure (Proposed)

```
D:\isoG\New-folder\sase_amp_fixed\
├── dase_cli/                    # ✅ Already exists
│   ├── dase_cli.exe
│   ├── dase_engine_phase4b.dll
│   └── ...
├── web/                         # ✅ Already exists
│   └── dase_interface.html
├── backend/                     # 🆕 TO CREATE
│   ├── server.js                # Node.js WebSocket server
│   ├── dvsl_compiler.js         # DVSL → DASE translator
│   ├── package.json
│   └── README.md
├── tests/                       # 🆕 TO CREATE
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                        # 🆕 TO CREATE
│   ├── USER_GUIDE.md
│   ├── API_REFERENCE.md
│   └── DEPLOYMENT.md
└── INTEGRATION_PLAN.md          # This file
```

---

## Success Criteria

### **MVP (Minimum Viable Product)**
- ✅ User can drag a symbol onto grid
- ✅ User can configure symbol parameters
- ✅ User can click "Run" and see real CLI metrics
- ✅ Performance displays actual ops/sec from engine
- ✅ Errors are handled gracefully

### **V1.0 (Production Ready)**
- ✅ All MVP features
- ✅ Save/load projects to cloud (Firestore)
- ✅ Support for 20+ symbol types
- ✅ Oscilloscope-like waveform viewer
- ✅ Multi-engine comparison mode
- ✅ Comprehensive error handling
- ✅ User documentation
- ✅ Packaged as Electron app

### **V2.0 (Advanced Features)**
- ✅ Real-time time-series streaming
- ✅ Circuit optimization AI (suggest improvements)
- ✅ Community library (share circuits)
- ✅ IGS-OA symbols fully functional
- ✅ GPU acceleration for large grids
- ✅ Export to Verilog/SPICE

---

## Next Steps (Immediate Actions)

1. **Set up Node.js backend** (Est. 2-3 hours)
   ```bash
   cd D:\isoG\New-folder\sase_amp_fixed
   mkdir backend
   cd backend
   npm init -y
   npm install express ws
   # Create server.js
   ```

2. **Test WebSocket connection** (Est. 1 hour)
   - Start Node server
   - Update HTML to connect
   - Verify ping/pong

3. **Implement first real command** (Est. 2 hours)
   - `create_engine` via WebSocket
   - Verify engine appears in terminal output
   - Display engine ID in UI

4. **Create simple circuit test** (Est. 1 hour)
   - Place 3 symbols on grid
   - Generate basic DASE command
   - Run and display results

**Total Time Estimate: 6-7 hours for functional prototype**

---

## Conclusion

The DASE Analog Excel web interface is **90% complete** from a UI perspective. The remaining 10% is the critical backend integration with the DASE CLI. With the CLI now fully functional and bug-free (as per BUGFIX_SUMMARY.md), the path forward is clear:

1. Build a lightweight WebSocket bridge (Node.js)
2. Replace mock functions with real CLI calls
3. Implement basic DVSL-to-DASE translation
4. Test with simple circuits
5. Iterate based on user feedback

**The foundation is solid. Integration is straightforward. Time to make it real!** 🚀
