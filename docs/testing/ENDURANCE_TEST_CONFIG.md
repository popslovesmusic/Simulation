# DASE Engine Endurance/Stress Test Configuration

**Status**: ⚠️ CONFIGURED BUT NOT RUN (awaiting user confirmation)

---

## Test Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Total Operations** | ~168.3 billion ops | 168,192,000,000 operations |
| **Total Duration** | ≥10 minutes (~603 seconds) | Based on 280.3M ops/sec performance |
| **Mission Steps** | 5,475,000 | Outer loop iterations |
| **Nodes** | 1,024 | Parallel processing units |
| **Iterations per Node** | 30 | Inner loop iterations |
| **CPU Utilization** | 100% (12/12 cores) | Full multi-threading |
| **Test Type** | Endurance/Stress Test | Long-running stability test |

---

## Calculations

### Total Operations:
```
Total Operations = Mission Steps × Nodes × Iterations
                 = 5,475,000 × 1,024 × 30
                 = 168,192,000,000 operations
                 = ~168.3 billion operations
```

### Expected Duration:
```
Duration = Total Operations / Throughput
         = 168,192,000,000 / 280,300,000 ops/sec
         = 600 seconds
         = 10.0 minutes
```

### Actual performance may vary based on:
- CPU thermal throttling (if sustained at 100% for 10+ minutes)
- Background processes
- Memory bandwidth saturation
- Cache efficiency over long runs

---

## Configuration Changes

### File Modified: `src/python/dase_benchmark_fixed.py`

**Changes Made**:

1. **Updated `test_performance()` method** (lines 230-288):
   - Added `test_type` parameter ("standard" or "endurance")
   - Added detailed progress reporting for endurance tests
   - Added start/end time stamps
   - Enhanced metrics collection (elapsed_min, ops_per_ns, etc.)
   - Added configuration display before test starts

2. **Updated `main()` function** (lines 422-449):
   - Changed `cycles` parameter from 3,000 → 5,475,000
   - Added `test_type="endurance"` parameter
   - Reordered tests (basic ops and accuracy before endurance test)
   - Added inline documentation of test parameters

3. **Updated `summarize()` method** (lines 383-450):
   - Added endurance test-specific summary format
   - Added expected vs. actual operation count comparison
   - Added test duration validation (checks for ≥10 minutes)
   - Added detailed performance metrics display
   - Added pass/fail criteria for endurance test

---

## How to Run

### Standard Benchmark (Quick Test):
```python
# Edit main() function, change to:
bench.test_performance(cycles=3_000, test_type="standard")
```
**Duration**: ~0.3 seconds
**Purpose**: Quick performance check

### Endurance Test (Current Configuration):
```bash
cd "D:/isoG/New-folder/sase amp fixed"
python src/python/dase_benchmark_fixed.py
```
**Duration**: ~10 minutes
**Purpose**: Long-term stability and stress testing

---

## Expected Output

### During Test:
```
=== ENDURANCE/STRESS TEST (10+ minutes) ===
Configuration:
  Mission Steps:    5,475,000
  Nodes:            1,024
  Iterations/Node:  30
  Total Operations: ~168.3 billion
  Expected Duration: ~10.0 minutes
  CPU Utilization:  100% (12/12 cores)

Starting endurance test... (this will take 10+ minutes)
Progress will be updated every minute...
Start time: 14:32:15

[... 10 minutes of processing ...]

End time: 14:42:18
run_mission(5,475,000) completed in 602.31s (10.04 min)
Operations/sec: 279,234,567
Speedup factor: 4,321.45x
Total operations: 168,192,000,000 (168.19 billion)
Time per operation: 3.58 ns/op
```

### Final Summary:
```
================================================================================
ENDURANCE/STRESS TEST SUMMARY REPORT
================================================================================
Engine Status:    native
Test Type:        endurance
Basic Operations: 5/5
Accuracy Tests:   4/4

PERFORMANCE RESULTS:
--------------------------------------------------------------------------------
Total Operations:  168,192,000,000 (168.19 billion)
Mission Steps:     5,475,000
Test Duration:     602.31 seconds (10.04 minutes)
Throughput:        279,234,567 ops/sec
Time per Op:       3.58 ns/op
Speedup Factor:    4,321.45x

Expected Operations: 168,192,000,000 (168.19 billion)
Actual Operations:   168,192,000,000 (168.19 billion)
Test Accuracy:       100.00%

[OK] ENDURANCE TEST PASSED: 10+ minute duration achieved

Detailed results saved to: dase_benchmark_results_20251023_143218.json
```

---

## Test Objectives

### Primary Goals:
1. **Stability**: Verify engine runs without crashes for extended periods
2. **Consistency**: Confirm performance remains stable (no degradation)
3. **Thermal**: Test CPU thermal management under sustained load
4. **Memory**: Verify no memory leaks over long runs
5. **Accuracy**: Confirm numerical accuracy maintained throughout

### Success Criteria:
- ✅ Completes all 168.3 billion operations without errors
- ✅ Duration ≥ 10 minutes (600 seconds)
- ✅ Operation count matches expected value (100% accuracy)
- ✅ All basic operations pass (5/5)
- ✅ All accuracy tests pass (4/4)
- ✅ No crashes, hangs, or exceptions
- ✅ Performance remains within expected range (±10% of 280M ops/sec)

### Monitoring During Test:
1. **CPU Usage**: Should maintain ~100% across all 12 cores
2. **Temperature**: Watch for thermal throttling (sustained 100% load)
3. **Memory**: Monitor RAM usage (should remain stable, no leaks)
4. **Disk I/O**: Should be minimal (computation-only workload)

---

## Thermal Considerations

**⚠️ WARNING**: This test will run the CPU at 100% utilization for 10+ minutes.

### Recommended Precautions:
1. **Cooling**: Ensure adequate cooling (laptop cooling pad, room temperature)
2. **Power**: Use AC power (not battery) for laptops
3. **Background Tasks**: Close unnecessary applications
4. **Monitoring**: Watch CPU temperature with tools like:
   - Windows: HWMonitor, Core Temp
   - Mac: iStat Menus
   - Linux: `sensors` command

### Expected CPU Behavior:
- **0-2 minutes**: CPU at maximum turbo frequency (~4.9 GHz for i7-12700)
- **2-5 minutes**: Thermal throttling may begin (~4.5 GHz)
- **5-10 minutes**: Sustained frequency (~4.2-4.5 GHz depending on cooling)

### Safe Temperature Ranges:
- **Intel i7-12700**: TjMax = 100°C
  - Safe: < 85°C
  - Warning: 85-95°C (throttling likely)
  - Critical: > 95°C (auto-throttle for protection)

---

## Benchmark Results File

After completion, results are saved to JSON file:
- **Filename**: `dase_benchmark_results_YYYYMMDD_HHMMSS.json`
- **Location**: Current working directory
- **Format**: JSON with full metrics and system info

### JSON Structure:
```json
{
  "metadata": { ... system info ... },
  "cpu_caps": { "avx2": true, "fma": true },
  "basic_ops": { ... 5 basic operation tests ... },
  "performance": {
    "mode": "native",
    "test_type": "endurance",
    "elapsed_s": 602.31,
    "elapsed_min": 10.04,
    "current_ops_per_second": 279234567,
    "speedup_factor": 4321.45,
    "total_operations": 168192000000,
    "cycles": 5475000,
    "ops_per_ns": 3.58
  },
  "accuracy": { ... 4 accuracy tests ... },
  "summary": { ... test summary ... }
}
```

---

## Reverting to Standard Test

To switch back to the quick 3-second test:

### Option 1: Edit main() function
```python
# In dase_benchmark_fixed.py, line 443:
bench.test_performance(cycles=3_000, test_type="standard")
```

### Option 2: Create separate test script
```python
# Create: quick_benchmark.py
from dase_benchmark_fixed import DASEBenchmark

bench = DASEBenchmark()
bench.initialize_engine(num_nodes=128)
bench.test_basic_ops()
bench.test_performance(cycles=3_000, test_type="standard")
bench.test_accuracy()
bench.summarize()
bench.save()
```

---

## Comparison: Standard vs. Endurance

| Metric | Standard Test | Endurance Test |
|--------|--------------|----------------|
| Duration | ~0.3 seconds | ~600 seconds (10 min) |
| Mission Steps | 3,000 | 5,475,000 |
| Total Operations | 92.16 million | 168.19 billion |
| CPU Load | Brief spike | Sustained 100% |
| Thermal Impact | Negligible | Significant |
| Purpose | Quick verification | Stability/stress testing |

---

## Next Steps

1. **User Confirmation**: ⚠️ Awaiting user approval to run test
2. **Pre-Test Checks**:
   - Close unnecessary applications
   - Ensure adequate cooling
   - Monitor system temperature tools ready
   - Save any important work (system will be under load)
3. **Run Test**: Execute `python src/python/dase_benchmark_fixed.py`
4. **Monitor**: Watch CPU usage, temperature, and memory during test
5. **Analyze Results**: Review JSON output and summary report
6. **Document**: Update optimization reports with endurance test results

---

## File Locations

- **Benchmark Script**: `src/python/dase_benchmark_fixed.py` (MODIFIED)
- **Configuration Doc**: `ENDURANCE_TEST_CONFIG.md` (this file)
- **Results Output**: `dase_benchmark_results_YYYYMMDD_HHMMSS.json` (generated after test)
- **Optimization Report**: `docs/FINAL_OPTIMIZATION_REPORT.md` (previous results)

---

**Last Updated**: October 23, 2025
**Configuration Status**: ✅ READY TO RUN (awaiting user confirmation)
**Estimated Test Duration**: 10.0 minutes (600 seconds)
**Test Status**: ⚠️ NOT YET EXECUTED
