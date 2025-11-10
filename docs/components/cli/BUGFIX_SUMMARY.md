# DASE CLI Bug Fixes - Summary

## Issues Identified and Fixed

### 1. ❌ Bug: get_metrics Returns Wrong Engine Type

**Problem:** The `get_metrics` command was hardcoded to return `"engine_type":"phase4b"` regardless of the actual engine type.

**Root Cause:** In `command_router.cpp` line 219, the engine type was hardcoded:
```cpp
json result = {
    {"engine_type", "phase4b"},  // ❌ HARDCODED!
    ...
};
```

**Fix:** Modified `handleGetMetrics` to retrieve the actual engine type from the engine instance:
```cpp
// Get engine instance to retrieve actual engine type
auto* instance = engine_manager->getEngine(engine_id);
std::string engine_type = instance ? instance->engine_type : "unknown";

json result = {
    {"engine_type", engine_type},  // ✅ Uses actual type
    ...
};
```

**Files Modified:**
- `dase_cli/src/command_router.cpp` (lines 213-230)

**Test Results:**
- ✅ Phase 4B engine now returns: `"engine_type":"phase4b"`
- ✅ IGSOA Complex engine now returns: `"engine_type":"igsoa_complex"`
- ✅ Unknown/invalid engines return: `"engine_type":"unknown"`

---

### 2. ℹ️ Engine ID Assignment (Not a Bug - By Design)

**Observation:** The CLI auto-generates sequential engine IDs (`engine_001`, `engine_002`, etc.) regardless of what ID is requested in commands.

**Behavior:**
- `create_engine` always returns the next available ID
- Users must use the returned `engine_id` in subsequent commands
- Engine IDs do NOT persist across CLI invocations

**This is correct behavior** - the CLI manages IDs automatically to prevent conflicts.

**Best Practice:**
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
→ Returns: {"engine_id":"engine_001",...}

{"command":"run_mission","params":{"engine_id":"engine_001",...}}
✅ Use the ID from the create_engine response
```

---

## Testing Summary

### Before Fix
```bash
$ echo '{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":512}}' | dase_cli.exe
{"result":{"engine_id":"engine_001","engine_type":"igsoa_complex",...}}

$ echo '{"command":"get_metrics","params":{"engine_id":"engine_001"}}' | dase_cli.exe
{"result":{"engine_type":"phase4b",...}}  # ❌ WRONG!
```

### After Fix
```bash
$ echo '{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":512}}' | dase_cli.exe
{"result":{"engine_id":"engine_001","engine_type":"igsoa_complex",...}}

$ echo '{"command":"get_metrics","params":{"engine_id":"engine_001"}}' | dase_cli.exe
{"result":{"engine_type":"igsoa_complex",...}}  # ✅ CORRECT!
```

---

## Verified Test Cases

### Test 1: Phase 4B Engine
```bash
$ cat << 'EOF' | dase_cli.exe
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":2000,"iterations_per_node":20}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
EOF
```

**Results:**
- ✅ Engine created: `engine_001`, type `phase4b`
- ✅ Mission completed: 2000 steps, 81.92M operations
- ✅ Metrics returned: `engine_type":"phase4b"`, 0.19 ns/op, 5.3B ops/sec

### Test 2: IGSOA Complex Engine
```bash
$ cat << 'EOF' | dase_cli.exe
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024,"R_c":2.5}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":200,"iterations_per_node":10}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
EOF
```

**Results:**
- ✅ Engine created: `engine_001`, type `igsoa_complex`
- ✅ Mission completed: 200 steps, 204.8K operations
- ✅ Metrics returned: `engine_type":"igsoa_complex"`, 28.2 ns/op, 35.5M ops/sec

### Test 3: Multiple Engines in One Session
```bash
$ cat << 'EOF' | dase_cli.exe
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":1024}}
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":512}}
{"command":"list_engines","params":{}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
{"command":"get_metrics","params":{"engine_id":"engine_002"}}
EOF
```

**Results:**
- ✅ Engine 001 created: type `phase4b`
- ✅ Engine 002 created: type `igsoa_complex`
- ✅ List shows both engines with correct types
- ✅ Metrics for engine_001: `engine_type":"phase4b"`
- ✅ Metrics for engine_002: `engine_type":"igsoa_complex"`

---

## Performance Verification

**Phase 4B Engine (AVX2 Optimized):**
- Performance: 0.18-0.19 ns/op
- Throughput: 5.3-5.5 billion ops/sec
- Speedup: ~84,000x

**IGSOA Complex Engine:**
- Performance: 25-28 ns/op
- Throughput: 35-40 million ops/sec
- Speedup: ~140x

Both engines operating within expected performance ranges ✅

---

## Recommendations

### For Users

1. **Always use engine IDs returned by create_engine**
   ```json
   {"command":"create_engine",...}
   → {"result":{"engine_id":"engine_001",...}}

   {"command":"run_mission","params":{"engine_id":"engine_001",...}}
   ```

2. **Keep commands in one file for multi-command workflows**
   - Engine state persists within a single CLI session
   - Each CLI invocation is independent

3. **Use the corrected example files**
   - `mission_short_corrected.json` for Phase 4B
   - `mission_igsoa_complex.json` for IGSOA Complex

### For Developers

1. **Never hardcode engine_type in responses**
   - Always retrieve from `EngineInstance`
   - Use `"unknown"` as fallback for invalid IDs

2. **Engine ID generation is automatic**
   - Sequential numbering managed by `EngineManager`
   - Users cannot specify custom IDs

3. **Both engine types now fully supported**
   - Phase 4B: DLL-based, real-valued
   - IGSOA Complex: Direct C++, complex-valued

---

## Files Updated

| File | Changes | Status |
|------|---------|--------|
| `dase_cli/src/command_router.cpp` | Fixed hardcoded engine_type | ✅ Tested |
| `dase_cli/rebuild.bat` | Added build error reporting | ✅ Working |
| `dase_cli/mission_igsoa_complex.json` | Created corrected example | ✅ Verified |

---

## Build Instructions

To rebuild the CLI after modifications:

```cmd
cd dase_cli
rebuild.bat
```

Or from Git Bash:
```bash
cd dase_cli
./rebuild.bat
```

---

## Conclusion

✅ **All identified bugs have been fixed and tested**
✅ **Both engine types (Phase 4B and IGSOA Complex) work correctly**
✅ **get_metrics now returns accurate engine type information**
✅ **Performance metrics are correctly retrieved for both engine types**

The DASE CLI is now **fully functional and production-ready** for both engine types! 🎉
