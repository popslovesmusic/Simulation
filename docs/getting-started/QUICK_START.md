# DASE Engine - Quick Start Guide

## System Overview

The DASE system provides a **dual-architecture** engine for high-performance computation:

1. **Phase 4B Engine** - Real-valued analog computation (2.85 ns/op)
2. **IGSOA Complex Engine** - Complex-valued quantum-inspired computation (~25 ns/op)

Both engines are accessible through:
- **Julia FFI** (direct, zero-copy, fastest)
- **Python ctypes** (portable, easy integration)
- **JSON CLI** (AI-ready, language-agnostic)

---

## Quick Start Options

### Option 1: Julia (Fastest - Recommended)

**Run Quick Benchmark:**
```bash
cd "D:\isoG\New-folder\sase amp fixed\benchmarks\julia"
julia test_julia_quick.jl
```

**Run Full Endurance Test (~8 minutes):**
```bash
cd "D:\isoG\New-folder\sase amp fixed\benchmarks\julia"
julia benchmark_julia_endurance.jl
```

**Expected Output:**
```
⚡ Current Performance: 2.85 ns/op
📊 Operations/sec:     351173047
🎉 TARGET ACHIEVED! Engine ready for production!
```

---

### Option 2: Python

**Quick Test:**
```bash
cd "D:\isoG\New-folder\sase amp fixed"
python test_python_quick.py
```

**Expected Output:**
```
Performance: ~4-5 ns/op
Throughput: ~200-250 M ops/sec
```

---

### Option 3: JSON CLI (AI Integration)

**Start CLI:**
```bash
cd "D:\isoG\New-folder\sase amp fixed"
dase_cli\dase_cli.exe
```

**Send JSON Commands via stdin:**

1. **Get Capabilities:**
```json
{"command":"get_capabilities"}
```

2. **Create Engine:**
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":1024}}
```

3. **Run Mission:**
```json
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":10000,"iterations_per_node":30}}
```

4. **Get Metrics:**
```json
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
```

**Python Integration Example:**
```python
import subprocess
import json

# Start CLI
proc = subprocess.Popen(
    ['dase_cli/dase_cli.exe'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Create engine
cmd = {"command": "create_engine", "params": {"engine_type": "phase4b", "num_nodes": 1024}}
proc.stdin.write(json.dumps(cmd) + '\n')
proc.stdin.flush()
response = json.loads(proc.stdout.readline())
engine_id = response['result']['engine_id']

# Run mission
cmd = {"command": "run_mission", "params": {"engine_id": engine_id, "num_steps": 10000}}
proc.stdin.write(json.dumps(cmd) + '\n')
proc.stdin.flush()
response = json.loads(proc.stdout.readline())

# Get metrics
cmd = {"command": "get_metrics", "params": {"engine_id": engine_id}}
proc.stdin.write(json.dumps(cmd) + '\n')
proc.stdin.flush()
response = json.loads(proc.stdout.readline())
print(f"Performance: {response['result']['ns_per_op']} ns/op")
```

---

## Available Engines

### 1. Phase 4B (Real-valued - Default)

**Use Case:** High-performance analog computation, signal processing

**Performance:** 2.85 ns/op (351 M ops/sec)

**Julia Example:**
```julia
include("src/julia/DaseEngine.jl")
using .DaseEngine

# Create engine (automatically uses Phase 4B)
engine = create_engine(1024)

# Prepare signals
inputs = sin.(collect(0:9999) .* 0.01)
controls = cos.(collect(0:9999) .* 0.01)

# Run mission
run_mission!(engine, inputs, controls, 30)

# Get metrics
metrics = get_metrics(engine)
println("Performance: $(metrics.ns_per_op) ns/op")

# Cleanup
destroy_engine(engine)
```

---

### 2. IGSOA Complex (Complex-valued)

**Use Case:** Quantum-inspired physics simulations, complex field dynamics

**Performance:** ~25 ns/op (40 M ops/sec)

**CLI Example:**
```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024,"R_c":1e-34}}
```

**Features:**
- Complex quantum states |Ψ⟩
- Schrödinger-like evolution
- Φ-Ψ coupling dynamics
- Entropy production tracking

---

## File Locations

### Executables
- **CLI:** `dase_cli/dase_cli.exe`
- **Phase 4B DLL:** `dase_engine_phase4b.dll`

### Julia Scripts
- **Quick test:** `benchmarks/julia/test_julia_quick.jl`
- **Endurance:** `benchmarks/julia/benchmark_julia_endurance.jl`

### Python Scripts
- **Quick test:** `test_python_quick.py`

### Documentation
- **Comprehensive Analysis:** `COMPREHENSIVE_ANALYSIS.md`
- **This Guide:** `QUICK_START.md`

---

## Benchmarking

### Quick Benchmark (< 1 second)
```bash
# Julia (fastest)
julia benchmarks/julia/test_julia_quick.jl

# Python
python test_python_quick.py
```

### Endurance Test (8-12 minutes)
```bash
# Julia
julia benchmarks/julia/benchmark_julia_endurance.jl
```

**Expected Results:**
- **Phase 4B:** 2.85 ns/op, 351 M ops/sec
- **Python baseline:** 4.27 ns/op, 234 M ops/sec
- **Speedup:** 1.5× faster than Python

---

## Performance Expectations

### Phase 4B (Real-valued)
| Metric | Value | Status |
|--------|-------|--------|
| **ns/op** | 2.85 | ✅ Production |
| **ops/sec** | 351 M | ✅ Excellent |
| **vs Baseline** | 5,443× | ✅ Exceeds target |

### IGSOA Complex (Complex-valued)
| Metric | Value | Status |
|--------|-------|--------|
| **ns/op** | ~25 | ✅ Production |
| **ops/sec** | 40 M | ✅ Good |
| **vs Baseline** | 620× | ✅ Exceeds target |

---

## Troubleshooting

### Issue: "DLL not found"
**Solution:** Ensure you're running from the correct directory:
```bash
cd "D:\isoG\New-folder\sase amp fixed"
```

### Issue: Julia "module not found"
**Solution:** Run from the benchmarks/julia directory:
```bash
cd "D:\isoG\New-folder\sase amp fixed\benchmarks\julia"
julia benchmark_julia_endurance.jl
```

### Issue: Low performance (> 10 ns/op)
**Solution:** Verify Phase 4B DLL is loaded:
- Check Julia output for "Phase 4B: Single parallel region, zero barriers"
- Ensure `dase_engine_phase4b.dll` exists in project root

### Issue: CLI doesn't respond
**Solution:** Commands must be valid JSON on a single line:
```bash
echo '{"command":"get_capabilities"}' | dase_cli/dase_cli.exe
```

---

## Next Steps

1. **Run Quick Test:** Verify installation with `julia test_julia_quick.jl`
2. **Run Endurance Test:** Validate performance with full benchmark
3. **Integrate with AI:** Use JSON CLI for AI agent control
4. **Explore IGSOA:** Test complex-valued quantum-inspired engine

For detailed documentation, see `COMPREHENSIVE_ANALYSIS.md`.
