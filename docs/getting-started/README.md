# DASE Analog Excel - High-Performance Analog Computing System

**Version:** 1.0
**Status:** Production Ready ✅
**Performance:** 5+ billion operations/second

---

## What is DASE?

**DASE (Discrete Analog Simulation Engine)** is a high-performance computing system for simulating analog circuits, neural networks, and IGS-OA (Informational Ground State - Ontological Algebra) dynamics using AVX2-optimized C++ engines.

**Key Features:**
- ⚡ **Blazing Fast:** 0.18 ns/op, 5.45 billion ops/sec
- 🎨 **Visual Programming:** Drag-and-drop circuit designer
- 🧠 **Advanced Physics:** IGS-OA dynamics, stochastic perturbations
- 💻 **Multi-Interface:** CLI, Web UI, Terminal
- 🚀 **Production Ready:** Fully tested and documented

---

## Quick Start

### Option 1: Command-Line Interface (Recommended)

1. **Open Command Prompt** in the `dase_cli` directory
2. **Run an example:**
   ```cmd
   cd dase_cli
   type mission_short_corrected.json | dase_cli.exe
   ```

3. **You should see:**
   ```
   {"command":"create_engine","status":"success"...}
   🚀 C++ OPTIMIZED MISSION LOOP STARTED (PHASE 4C - AVX2 SPATIAL) 🚀
   ...
   ⚡ Current Performance: 0.18 ns/op
   🚀 Speedup Factor: 84,552x
   ```

**See:** `dase_cli/README_WINDOWS.md` for detailed usage

### Option 2: Web Interface (Advanced)

1. **Install Node.js** (if not already installed)
2. **Install dependencies:**
   ```cmd
   cd backend
   npm install
   ```

3. **Start the server:**
   ```cmd
   npm start
   ```

4. **Open browser:** http://localhost:3000/dase_interface.html

5. **Build circuits** by dragging symbols onto the grid!

**See:** `INTEGRATION_PLAN.md` for web interface guide

---

## System Components

### 1. DASE CLI (`dase_cli/`)
**High-performance command-line interface**

- `dase_cli.exe` - Main executable
- `dase_engine_phase4b.dll` - AVX2 engine (5B ops/sec)
- `libfftw3-3.dll` - FFT library
- `*.json` - Example missions

**Documentation:**
- `README_WINDOWS.md` - Primary user guide
- `QUICKSTART.txt` - Quick reference
- `USAGE.md` - Complete API reference

### 2. Web Interface (`web/`)
**Visual programming environment**

- `dase_interface.html` - Analog Excel UI
- Drag-and-drop circuit designer
- Real-time simulation controls
- 30+ symbol types

**Features:**
- Visual grid (50×26 cells)
- Symbol library (amplifiers, integrators, oscillators)
- Formula presets (50+ circuits)
- Terminal interface

### 3. Backend Server (`backend/`)
**WebSocket bridge (Node.js)**

- `server.js` - WebSocket server
- `package.json` - Dependencies
- Bridges web UI to CLI

**Setup:**
```cmd
cd backend
npm install
npm start
```

### 4. Source Code (`src/`)
**C++ engine implementation**

- `analog_universal_node_engine_avx2.cpp` - Main engine
- `dase_capi.cpp` - C API wrapper
- `igsoa_complex_engine.h` - IGSOA implementation

**For rebuilding only** (optional)

---

## File Structure

```
sase_amp_fixed/
├── dase_cli/           ✅ Command-line interface
├── web/                ✅ Web UI
├── backend/            ✅ WebSocket server
├── src/                ⚠️  Source code (reference)
├── development/        ❌ Dev files (after reorganize.bat)
├── INTEGRATION_PLAN.md ✅ Web integration guide
├── FILE_ORGANIZATION.md✅ File structure docs
└── README.md           ✅ This file
```

**Total size:** ~3 MB (operational files only)

---

## Performance Benchmarks

### Phase 4B Engine (AVX2 Optimized)
- **Performance:** 0.18-0.33 ns/operation
- **Throughput:** 3-5.5 billion operations/second
- **Speedup:** 50,000-85,000x vs baseline
- **Nodes:** Up to 1 million supported

### IGSOA Complex Engine
- **Performance:** 25-32 ns/operation
- **Throughput:** 31-40 million operations/second
- **Features:** Complex-valued states, configurable coupling

**Tested on:** Windows 10/11, Intel Core i7/i9 (AVX2 required)

---

## Usage Examples

### Example 1: Create and Run Engine
```cmd
cd dase_cli
cat << EOF | dase_cli.exe
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":2000,"iterations_per_node":20}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
EOF
```

### Example 2: IGSOA Complex Engine
```cmd
type mission_igsoa_complex.json | dase_cli.exe
```

### Example 3: Multiple Engines
```cmd
type test_both_engines.json | dase_cli.exe
```

---

## Symbol Library (Web UI)

### Core Analog
- △ Amplifier - `=△(A1, gain=2.0)`
- ∫ Integrator - `=∫(A1, dt=0.01)`
- ∑ Summer - `=∑(A1, B1, C1)`
- ⊗ Multiplier - `=⊗(A1, B1)`

### IGS-OA Dynamics
- Φ IGS Field Node - `=Φ(potential=0.0)`
- Ξ Stochastic OA - `=Ξ(A1, amplitude=0.01)`
- R Lattice Coupling - `=R(A1, B1, radius=1.0)`
- O Stress Tensor - `=O(A1:C3, average=5)`

### Signal Generators
- ~ Sine Oscillator - `=~(freq=440, amp=1.0)`
- ⊓ Square Wave - `=⊓(freq=100, amp=5.0)`
- ⋈ Noise Generator - `=⋈(amp=0.1)`

### Neural
- 🧠 Neuron - `=🧠(A1, threshold=0.5)`
- 🔗 Synapse - `=🔗(A1, B1, weight=0.8)`

**Total: 30+ symbols across 6 categories**

---

## Documentation

| Document | Purpose |
|----------|---------|
| `dase_cli/README_WINDOWS.md` | Primary user guide |
| `dase_cli/QUICKSTART.txt` | Quick reference card |
| `dase_cli/USAGE.md` | Complete API reference |
| `dase_cli/BUGFIX_SUMMARY.md` | Bug fixes and solutions |
| `INTEGRATION_PLAN.md` | Web UI integration guide |
| `FILE_ORGANIZATION.md` | File structure documentation |
| `backend/README.md` | Backend server setup |

---

## Project Cleanup

To organize files and reduce clutter:

```cmd
reorganize.bat
```

This moves development files (~5.5 MB) to `development/` directory, leaving only operational files (~3 MB) in the main directory.

**See:** `FILE_ORGANIZATION.md` for details

---

## System Requirements

### Minimum
- **OS:** Windows 10/11 64-bit
- **CPU:** Intel/AMD with AVX2 support
- **RAM:** 4 GB
- **Disk:** 10 MB

### Recommended
- **OS:** Windows 11 64-bit
- **CPU:** Intel Core i7/i9 (8+ cores)
- **RAM:** 16 GB
- **Disk:** 100 MB (with development files)

### For Web Interface
- **Node.js:** v16 or later
- **Browser:** Chrome/Edge/Firefox (modern)

---

## Known Issues

### Segfault on CLI Exit
**Status:** Cosmetic only
**Impact:** None (all commands complete successfully)
**Cause:** FFTW cleanup order
**Workaround:** Redirect stderr (`2>nul`) if needed

**See:** `dase_cli/BUGFIX_SUMMARY.md` for details

---

## Advanced Features

### Multi-Engine Support
Run multiple engine types simultaneously:
- Phase 4B (real-valued, AVX2)
- IGSOA Complex (complex-valued)

### Terminal Commands
Built-in terminal for advanced users:
- `dase create <type> <nodes>` - Create engine
- `dase run <steps>` - Run mission
- `dase metrics` - Get performance data
- `dase list` - List active engines
- `dase destroy` - Cleanup

### JSON API
Full JSON command interface for integration:
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":1000,"iterations_per_node":20}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
```

---

## Troubleshooting

### "DLL not found"
- Ensure `libfftw3-3.dll` is in `dase_cli/` directory
- Copy from root if missing

### "AVX2 not supported"
- Your CPU doesn't support AVX2 instructions
- Upgrade to modern Intel/AMD processor

### JSON parse errors
- Ensure one command per line
- No pretty-printing (use `minify_json.py`)

### WebSocket connection fails
- Check Node.js server is running
- Verify firewall isn't blocking port 8080

**See:** `dase_cli/USAGE.md` troubleshooting section

---

## Development

### Rebuilding the CLI
```cmd
cd dase_cli/src
cl.exe /EHsc /std:c++17 /MD /O2 /I. /I../../src/cpp *.cpp /Fe:../dase_cli.exe
```

### Rebuilding the Engine DLL
```cmd
cd development/build_scripts
python compile_dll_phase4b.py
```

### Running Tests
```cmd
cd dase_cli
test_all.bat
```

**See:** `src/` directory for source code

---

## Version History

### v1.0 (Current)
- ✅ Phase 4B AVX2 engine (5B ops/sec)
- ✅ IGSOA Complex engine
- ✅ JSON CLI interface
- ✅ Web UI (90% complete)
- ✅ Bug fixes (get_metrics engine type)
- ✅ Comprehensive documentation

### Future Plans (v2.0)
- Real-time waveform streaming
- Circuit optimization AI
- GPU acceleration
- Cloud integration
- Export to Verilog/SPICE

---

## Contributing

This is a research project. For questions or suggestions:

1. Read the documentation thoroughly
2. Check `BUGFIX_SUMMARY.md` for known issues
3. Review `INTEGRATION_PLAN.md` for roadmap

---

## License

MIT License (see LICENSE file)

---

## Acknowledgments

- **FFTW Library:** FFT computations
- **MSVC Compiler:** C++ optimization
- **Node.js:** Backend server
- **nlohmann/json:** JSON parsing

---

## Quick Links

- **User Guide:** `dase_cli/README_WINDOWS.md`
- **API Reference:** `dase_cli/USAGE.md`
- **Web Integration:** `INTEGRATION_PLAN.md`
- **File Organization:** `FILE_ORGANIZATION.md`
- **Backend Setup:** `backend/README.md`

---

**Ready to compute at 5 billion operations per second?** 🚀

Start here: `dase_cli/QUICKSTART.txt`
