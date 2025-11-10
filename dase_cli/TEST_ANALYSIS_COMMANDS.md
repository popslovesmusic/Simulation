# Analysis Integration Test Guide

**Date:** 2025-11-06
**Status:** Ready for Testing

---

## Build Instructions

### Windows (MSVC 2022)

```bash
cd D:/igsoa-sim/dase_cli
build_with_analysis.bat
```

### Manual Build

```bash
cd D:/igsoa-sim/dase_cli
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
copy Release\dase_cli.exe ..
```

---

## Test 1: Check Tool Availability

**Command:**
```bash
cd D:/igsoa-sim/dase_cli
echo {"command":"check_analysis_tools","params":{}} | dase_cli.exe
```

**Expected Output:**
```json
{
  "status": "success",
  "result": {
    "python": {
      "available": true/false,
      "version": "3.x.x"
    },
    "julia_efa": {
      "available": true/false
    },
    "engine_fft": {
      "available": true,
      "features": ["1D_FFT", "2D_FFT", "3D_FFT"]
    }
  }
}
```

---

## Test 2: Engine FFT (1D)

**Commands:**
```bash
# Run complete test mission
dase_cli.exe < test_analysis_integration.json
```

**Test Mission (test_analysis_integration.json):**
```json
{
  "commands": [
    {"command": "create_engine", "params": {"engine_type": "igsoa_complex_1d", "num_nodes": 1024}},
    {"command": "run_mission", "params": {"engine_id": "engine_001", "num_steps": 1000}},
    {"command": "engine_fft", "params": {"engine_id": "engine_001", "field": "psi_real"}}
  ]
}
```

**Expected Output for FFT:**
```json
{
  "status": "success",
  "command": "engine_fft",
  "result": {
    "field_name": "psi_real",
    "N": 1024,
    "dc_component": ...,
    "peak_frequency": ...,
    "total_power": ...,
    "execution_time_ms": 0.5-2.0
  }
}
```

---

## Test 3: Engine FFT (2D)

**Create test file:** `test_fft_2d.json`
```json
{
  "commands": [
    {
      "command": "create_engine",
      "params": {
        "engine_type": "satp_higgs_2d",
        "num_nodes": 4096,
        "N_x": 64,
        "N_y": 64
      }
    },
    {
      "command": "run_mission",
      "params": {
        "engine_id": "engine_001",
        "num_steps": 500
      }
    },
    {
      "command": "engine_fft",
      "params": {
        "engine_id": "engine_001",
        "field": "phi"
      }
    }
  ]
}
```

**Run:**
```bash
dase_cli.exe < test_fft_2d.json
```

**Expected:** Radial profile in output, execution time ~2-5 ms

---

## Test 4: Python Analysis (if Python available)

**Create test file:** `test_python_analysis.json`
```json
{
  "commands": [
    {
      "command": "create_engine",
      "params": {
        "engine_type": "igsoa_complex_1d",
        "num_nodes": 1024,
        "R_c": 2.0
      }
    },
    {
      "command": "run_mission",
      "params": {
        "engine_id": "engine_001",
        "num_steps": 5000
      }
    },
    {
      "command": "python_analyze",
      "params": {
        "engine_id": "engine_001",
        "script": "analyze_igsoa_state.py",
        "args": {
          "positional": "2.0",
          "output-dir": "test_analysis",
          "verbose": ""
        }
      }
    }
  ]
}
```

**Run:**
```bash
dase_cli.exe < test_python_analysis.json
```

**Expected:** Generated plots in `test_analysis/` directory

---

## Test 5: Combined Analysis

**Create test file:** `test_combined_analysis.json`
```json
{
  "commands": [
    {
      "command": "create_engine",
      "params": {
        "engine_type": "igsoa_complex_2d",
        "num_nodes": 4096,
        "N_x": 64,
        "N_y": 64,
        "R_c": 2.0
      }
    },
    {
      "command": "run_mission",
      "params": {
        "engine_id": "engine_001",
        "num_steps": 3000
      }
    },
    {
      "command": "analyze_fields",
      "params": {
        "engine_id": "engine_001",
        "analysis_type": "engine",
        "config": {
          "engine": {
            "enabled": true,
            "compute_fft": true,
            "fields_to_analyze": ["psi_real", "phi"]
          }
        }
      }
    }
  ]
}
```

**Run:**
```bash
dase_cli.exe < test_combined_analysis.json
```

**Expected:** Multiple FFT results in output

---

## Validation Checklist

### ✅ Build Success
- [ ] CMakeLists.txt configures without errors
- [ ] All analysis source files compile
- [ ] dase_cli.exe links successfully
- [ ] No warnings about missing FFTW3

### ✅ Runtime Tests
- [ ] `check_analysis_tools` returns tool availability
- [ ] `engine_fft` works on 1D engine (IGSOA)
- [ ] `engine_fft` works on 2D engine (SATP+Higgs)
- [ ] `engine_fft` works on 3D engine
- [ ] FFT execution time < 5ms for 64×64
- [ ] Peak detection finds correct frequencies

### ✅ Python Integration (Optional)
- [ ] `python_analyze` executes if Python available
- [ ] Generated files appear in output directory
- [ ] Python script errors are captured correctly

### ✅ Error Handling
- [ ] Missing engine_id returns proper error
- [ ] Invalid field name returns proper error
- [ ] Python script not found returns proper error

---

## Quick Validation Script

Create `validate_integration.bat`:

```batch
@echo off
echo Testing Analysis Integration...
echo.

echo Test 1: Check tools
echo {"command":"check_analysis_tools","params":{}} | dase_cli.exe
echo.

echo Test 2: Engine FFT
dase_cli.exe < test_analysis_integration.json
echo.

echo Test 3: 2D FFT
dase_cli.exe < test_fft_2d.json
echo.

echo All tests complete!
pause
```

---

## Troubleshooting

### Build Issues

**Error:** `FFTW3 not found`
- **Solution:** Copy `libfftw3-3.lib` to `D:/igsoa-sim/dase_cli/` or project root

**Error:** `Cannot open include file: 'fftw3.h'`
- **Solution:** Copy `fftw3.h` to project root or update include path

### Runtime Issues

**Error:** `Engine not found`
- **Check:** Engine was created successfully in previous command
- **Fix:** Use correct engine_id in analysis commands

**Error:** `FFT failed: Field not found`
- **Check:** Field name matches engine type (psi_real for IGSOA, phi for SATP)
- **Fix:** Use appropriate field names

---

## Performance Benchmarks

Expected performance on modern CPU:

| Engine | Size | FFT Time |
|--------|------|----------|
| 1D | 1024 | ~0.5 ms |
| 2D | 64×64 | ~2 ms |
| 2D | 128×128 | ~8 ms |
| 3D | 32×32×32 | ~15 ms |

If times are significantly higher, check:
- FFTW3 is properly linked (not using slow fallback)
- Release build (not Debug)
- No antivirus interfering

---

## Next Steps After Validation

1. **If all tests pass:**
   - Integration is complete!
   - Update main INSTRUCTIONS.md
   - Document in project README

2. **If Python tests fail:**
   - Analysis still works (engine FFT)
   - Python integration is optional
   - Install Python dependencies if needed

3. **If FFT tests fail:**
   - Check FFTW3 library linkage
   - Verify cmake found correct library
   - Rebuild with verbose output

---

## Contact for Issues

If integration tests fail, check:
1. `D:/igsoa-sim/dase_cli/ANALYSIS_INTEGRATION.md` - Full documentation
2. `D:/IMPLEMENTATION_SUMMARY.md` - Implementation notes
3. Build output for specific error messages
