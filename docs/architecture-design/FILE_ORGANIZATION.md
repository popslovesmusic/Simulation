# DASE Project File Organization

## Directory Structure

```
sase_amp_fixed/
├── dase_cli/                   ✅ OPERATIONAL - Command-line interface
│   ├── dase_cli.exe           Main executable
│   ├── dase_engine_phase4b.dll   Phase 4B AVX2 engine (27KB)
│   ├── libfftw3-3.dll         FFTW dependency (2.6MB)
│   ├── mission_short_corrected.json   Example mission (Phase 4B)
│   ├── mission_igsoa_complex.json     Example mission (IGSOA)
│   ├── test_both_engines.json         Test suite
│   ├── examples.json          Comprehensive examples
│   ├── README_WINDOWS.md      Primary user guide
│   ├── QUICKSTART.txt         Quick reference
│   ├── USAGE.md               API documentation
│   ├── BUGFIX_SUMMARY.md      Known issues and fixes
│   ├── run_mission.bat        Helper script
│   └── src/                   ⚠️ CLI source code (optional for rebuilds)
│       ├── command_router.cpp
│       ├── engine_manager.cpp
│       └── main.cpp
│
├── web/                        ✅ OPERATIONAL - Web interface
│   └── dase_interface.html    Visual programming UI
│
├── backend/                    ✅ OPERATIONAL - WebSocket server
│   ├── server.js              Node.js backend
│   ├── package.json           NPM dependencies
│   └── README.md              Backend documentation
│
├── src/                        ⚠️ REFERENCE - C++ engine source
│   └── cpp/
│       ├── analog_universal_node_engine_avx2.cpp   Main engine
│       ├── dase_capi.cpp      C API wrapper
│       ├── igsoa_complex_engine.h   IGSOA implementation
│       └── *.h                Headers
│
├── development/                ❌ DEVELOPMENT FILES (created by reorganize.bat)
│   ├── build_artifacts/       *.obj files, build cache
│   ├── old_builds/            Superseded DLLs
│   ├── test_executables/      Unit tests
│   ├── build_scripts/         Compilation scripts
│   ├── benchmarks/            Performance tests
│   ├── documentation/         Historical analysis docs
│   └── miscellaneous/         Utility scripts
│
├── INTEGRATION_PLAN.md         ✅ Integration guide
├── fftw3.h                     ✅ FFTW header (for rebuilds)
├── libfftw3-3.dll              ✅ FFTW library (backup)
└── reorganize.bat              🔧 Cleanup script
```

---

## Operational Files (Required for Production)

### Minimum Runtime
If you only want to **run** the system (not develop):
```
dase_cli/
  ├── dase_cli.exe
  ├── dase_engine_phase4b.dll
  ├── libfftw3-3.dll
  ├── mission_short_corrected.json
  └── README_WINDOWS.md
```

### Full Operational Set
For complete functionality including web UI:
```
dase_cli/            (all .exe, .dll, .json, .md files)
web/                 (dase_interface.html)
backend/             (server.js, package.json)
INTEGRATION_PLAN.md
```

### Optional for Rebuilding
If you need to **rebuild** the CLI or engine:
```
src/cpp/             (C++ source code)
dase_cli/src/        (CLI source)
fftw3.h              (FFTW header)
development/build_scripts/   (build scripts)
```

---

## File Categories

### ✅ **Essential Runtime** (Cannot delete)
| File | Size | Purpose |
|------|------|---------|
| `dase_cli.exe` | 206KB | Main CLI executable |
| `dase_engine_phase4b.dll` | 27KB | AVX2-optimized engine |
| `libfftw3-3.dll` | 2.6MB | FFTW library |
| `README_WINDOWS.md` | 15KB | User documentation |

**Total: ~2.8 MB**

### ⚠️ **Reference Source** (Keep for rebuilds)
| Directory | Size | Purpose |
|-----------|------|---------|
| `src/cpp/` | ~200KB | C++ engine source |
| `dase_cli/src/` | ~50KB | CLI source code |
| `fftw3.h` | 600KB | FFTW header |

**Total: ~850 KB**

### ❌ **Development Only** (Move to development/)
| Category | Files | Size |
|----------|-------|------|
| Build artifacts | `*.obj` | ~3.5 MB |
| Old engines | `phase3.dll`, `phase4a.dll` | ~70 KB |
| Tests | `test_*.exe`, `*.obj` | ~350 KB |
| Build scripts | `*.bat`, `*.py`, CMake | ~50 KB |
| Benchmarks | `benchmarks/` | ~500 KB |
| Docs | `docs/` | ~800 KB |
| Misc | Others | ~200 KB |

**Total: ~5.5 MB** (safe to archive)

---

## Usage Scenarios

### Scenario 1: End User (Just Running)
**Keep:**
- `dase_cli/` (exclude `src/`)
- `web/` (if using web UI)
- `backend/` (if using web UI)
- `README_WINDOWS.md`

**Delete/Archive:**
- Everything else

**Size: ~3 MB**

### Scenario 2: Developer (Building & Testing)
**Keep:**
- All operational files
- `src/`
- `dase_cli/src/`
- `development/build_scripts/`
- `development/test_executables/`

**Archive:**
- `development/documentation/` (historical)
- `development/benchmarks/` (old results)

**Size: ~10 MB**

### Scenario 3: Full Archive (Everything)
**Keep:**
- All files including `development/`

**Size: ~15 MB**

---

## Reorganization Process

Run the reorganization script to move development files:

```cmd
reorganize.bat
```

This will:
1. Create `development/` directory structure
2. Move all build artifacts, tests, old DLLs, etc.
3. Keep operational files in place
4. Generate summary report

**After reorganization:**
- Operational size: ~3 MB
- Development archive: ~5.5 MB
- Source code (optional): ~850 KB

---

## File Dependency Tree

```
dase_cli.exe
  └─ dase_engine_phase4b.dll
       └─ libfftw3-3.dll

server.js (backend)
  └─ dase_cli.exe (spawned as child process)

dase_interface.html (web)
  └─ WebSocket → server.js → dase_cli.exe
```

**No circular dependencies. All files are self-contained.**

---

## Rebuilding From Source

If `development/` was archived and you need to rebuild:

### Rebuild the Engine DLL
```cmd
cd development/build_scripts
compile_dll_phase4b.py
```
Requires: `src/cpp/*.cpp`, MSVC compiler

### Rebuild the CLI
```cmd
cd dase_cli/src
cl.exe /EHsc /std:c++17 /MD /O2 *.cpp /Fe:../dase_cli.exe
```
Requires: `dase_cli/src/*.cpp`, MSVC compiler

### Rebuild Everything
```cmd
cd development/build_scripts
build_all.bat
```

---

## Version Control Recommendations

### Git .gitignore
```gitignore
# Build artifacts
*.obj
*.pdb
*.ilk
build/

# Old versions
development/old_builds/

# Test executables
development/test_executables/

# Node modules (backend)
backend/node_modules/

# Temporary files
*.tmp
*.log
```

### What to Commit
✅ All operational files
✅ Source code (`src/`, `dase_cli/src/`)
✅ Build scripts (`development/build_scripts/`)
✅ Documentation (essential)
❌ Build artifacts (`.obj`, `.dll` except final)
❌ Test executables
❌ Benchmark data
❌ node_modules

---

## Disk Space Analysis

**Before reorganization:**
```
Total:        ~15 MB
Operational:  ~3 MB   (20%)
Development:  ~5.5 MB (37%)
Source:       ~0.9 MB (6%)
Redundant:    ~5.6 MB (37%)
```

**After reorganization:**
```
Root directory:  ~3 MB   (operational only)
development/:    ~5.5 MB (archived)
src/:            ~0.9 MB (reference)
```

**Space savings:** ~10 MB removed from operational directory

---

## Cleanup Checklist

- [ ] Run `reorganize.bat`
- [ ] Test `dase_cli.exe` still works
- [ ] Test web interface (if using)
- [ ] Verify all essential .json examples present
- [ ] Compress `development/` to .zip for archival
- [ ] Delete `development/` if no future builds planned
- [ ] Update documentation paths
- [ ] Test rebuild process (if keeping source)

---

## Quick Reference

**To run the CLI:**
```cmd
cd dase_cli
type mission_short_corrected.json | dase_cli.exe
```

**To start web interface:**
```cmd
cd backend
npm install
npm start
# Open http://localhost:3000/dase_interface.html
```

**To rebuild CLI:**
```cmd
cd dase_cli/src
cl.exe /EHsc /std:c++17 /MD /O2 *.cpp /Fe:../dase_cli.exe
```

**To archive development files:**
```cmd
reorganize.bat
tar -czf development.tar.gz development/
rmdir /S /Q development
```

---

## Summary

**Operational files:** 3 MB (20% of total)
**Development files:** 5.5 MB (37% of total)
**Source code:** 0.9 MB (6% of total)
**Redundant files:** 5.6 MB (37% of total - safe to delete)

**After cleanup: 3 MB production-ready system** 🎉
