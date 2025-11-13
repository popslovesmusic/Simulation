# IGSOA-SIM Project Organization

This document describes the organized structure of the IGSOA-SIM project.

## Directory Structure

### 🧪 tests/
**Purpose:** All test files and test scripts

**Contents:**
- C++ test files (`test_*.cpp`)
- Python test scripts (`test_*.py`)
- Julia test files (`test_*.jl`)
- Test batch files (`test_all.bat`)

**Examples:**
- `test_igsoa_2d.cpp`
- `test_igsoa_3d.cpp`
- `test_2d_engine_comprehensive.cpp`
- `test_new_features.py`
- `test_cli.py`

---

### 🔧 fixes/
**Purpose:** Scripts for applying fixes and improvements

**Contents:**
- Fix application scripts
- Conflict resolution scripts
- Improvement scripts

**Examples:**
- `apply_fixes.py`
- `apply_critical_fixes.py`
- `apply_audit_critical_fixes.py`
- `resolve_3d_conflicts.py`
- `apply_remaining_improvements.py`

---

### 🏗️ build/scripts/
**Purpose:** Build and compilation scripts

**Contents:**
- DLL compilation scripts
- Build batch files
- Library generation scripts
- Compilation verification

**Examples:**
- `compile_dll_phase3.py`
- `compile_dll_phase4a.py`
- `compile_dll_phase4b.py`
- `build_cli.bat`
- `rebuild.bat`
- `build_igsoa_test.bat`
- `generate_lib.bat`
- `verify_compilation.bat`

---

### 🔬 analysis/
**Purpose:** Analysis scripts and data processing tools

**Contents:**
- State analysis scripts
- Translation analysis
- Cost computation
- Drift extraction
- Plotting tools

**Examples:**
- `analyze_igsoa_state.py`
- `analyze_exotic_cost.py`
- `analyze_translation.py`
- `compute_autocorrelation.py`
- `extract_drift.py`
- `plot_satp_state.py`

---

### 🛠️ tools/
**Purpose:** General utility scripts and helpers

**Contents:**
- Visualization tools
- SATP analysis tools
- JSON utilities
- Directory utilities

**Examples:**
- `visualize_satp.py`
- `analyze_satp_v2.bat`
- `run_and_analyze_interactive.bat`
- `minify_json.py`
- `dir.py`

---

### 🎯 missions/
**Purpose:** Mission files and mission-related scripts

**Contents:**
- Mission JSON files
- Mission execution scripts
- SATP translation missions

**Examples:**
- `satp_translation_mission.py`
- `run_mission.bat`
- Various mission JSON configurations

---

### 📚 docs/
**Purpose:** All documentation (already organized by category)

**Structure:**
- `getting-started/` - Quick start guides, production guides
- `api-reference/` - API documentation
- `implementation/` - Implementation plans and reports
- `testing/` - Test documentation
- `reports-analysis/` - Analysis reports
- `satp/` - SATP protocol documentation
- `architecture-design/` - System architecture
- `security/` - Security documentation
- `issues-fixes/` - Issue tracking and fix documentation
- `guides-manuals/` - Operation manuals
- `roadmap/` - Future plans
- `components/` - Component-specific docs (backend, web, cli)
- `archive/` - Historical documents

---

### 💻 src/
**Purpose:** Source code (organized by language)

**Structure:**
- `cpp/` - C++ engine implementations (non-test)
  - `analog_universal_node_engine_avx2.cpp`
  - `dase_capi.cpp`
  - `igsoa_capi.cpp`
  - `python_bindings.cpp`
- `julia/` - Julia bindings and modules
- `python/` - Python bindings

---

### 🚀 dase_cli/
**Purpose:** DASE command-line interface

**Contents:**
- CLI executable
- CLI source code
- DLLs and dependencies
- Mission configuration files

---

### 📊 benchmarks/
**Purpose:** Performance benchmarking scripts

**Structure:**
- `julia/` - Julia benchmark scripts
- `python/` - Python benchmark scripts

---

### 🌐 web/
**Purpose:** Web interface files

**Contents:**
- HTML interface
- JavaScript
- CSS

---

### 🔌 backend/
**Purpose:** Backend server

**Contents:**
- Node.js server
- WebSocket implementation

---

### 📦 Other Directories

- `archive/` - Archived old files
- `results/` - Test and benchmark results
- `fft/` - FFT-related files

---

## File Organization Principles

1. **Tests** - All test files go in `tests/`
2. **Build** - All build/compile scripts go in `build/scripts/`
3. **Fixes** - All fix scripts go in `fixes/`
4. **Analysis** - Data analysis scripts go in `analysis/`
5. **Tools** - General utilities go in `tools/`
6. **Missions** - Mission configs and runners go in `missions/`
7. **Docs** - All documentation goes in `docs/` (organized by category)
8. **Source** - Implementation code stays in `src/`

---

## Quick Reference

| I want to... | Look in... |
|--------------|------------|
| Run tests | `tests/` |
| Build the project | `build/scripts/` |
| Apply a fix | `fixes/` |
| Analyze data | `analysis/` |
| Run a utility | `tools/` |
| Run a mission | `missions/` |
| Read documentation | `docs/` |
| Modify engine code | `src/cpp/` |
| Use the CLI | `dase_cli/` |
| Run benchmarks | `benchmarks/` |

---

## Maintenance

When adding new files:
1. Determine the file's primary purpose
2. Place it in the appropriate directory
3. Update this document if creating new categories
4. Keep the root directory clean - files belong in subdirectories

---

**Last Updated:** November 2025
**Organization Version:** 2.0
