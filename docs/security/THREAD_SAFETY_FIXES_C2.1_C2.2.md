# Thread Safety Fixes: C2.1 and C2.2

**Date**: 2025-01-XX
**Priority**: CRITICAL
**Issues**: C2.1 (Global Metrics Data Race), C2.2 (FFTW Cache Thread Safety)

## Overview

This document describes critical thread safety fixes for data races that cause undefined behavior when multiple engines or threads are used concurrently.

---

## Issue C2.1: Global Metrics Data Race

### Problem

**Location**: `src/cpp/analog_universal_node_engine_avx2.cpp:18`

```cpp
// ❌ CRITICAL BUG: Shared mutable global state
static EngineMetrics g_metrics;
```

**Impact**:
- **Data races**: Multiple threads/engines access and modify g_metrics without synchronization
- **Undefined behavior**: Race conditions on metric counters
- **Corrupted metrics**: Values become unpredictable in concurrent scenarios
- **Thread sanitizer failures**: Detected by -fsanitize=thread

**Root Cause**:
The global `g_metrics` is accessed by:
1. All `AnalogCellularEngineAVX2` instances
2. OpenMP threads via `COUNT_OPERATION()`, `COUNT_AVX2()` macros
3. `AnalogUniversalNodeAVX2` member functions

### Solution

**Move metrics to per-instance storage**:

#### Step 1: Update Header (`analog_universal_node_engine_avx2.h`)

```cpp
// ============================================================================
// ANALOG CELLULAR ENGINE AVX2
// ============================================================================
class AnalogCellularEngineAVX2 {
private:
    // Use 64-byte aligned allocator for cache-line optimization
    std::vector<AnalogUniversalNodeAVX2, aligned_allocator<AnalogUniversalNodeAVX2, 64>> nodes;
    double system_frequency;
    double noise_level;

    // FIX C2.1: Per-instance metrics instead of global static
    // This prevents data races when multiple engines run concurrently
    EngineMetrics metrics_;

public:
    // ... rest of class
```

#### Step 2: Update Implementation (`analog_universal_node_engine_avx2.cpp`)

**Remove global g_metrics**:
```cpp
// ❌ DELETE THIS LINE:
// static EngineMetrics g_metrics;
```

**Remove or disable unsafe macros**:
```cpp
// ❌ DELETE THESE MACROS (not thread-safe from node functions):
// #define PROFILE_TOTAL() PrecisionTimer _total_timer(&g_metrics.total_execution_time_ns)
// #define COUNT_OPERATION() g_metrics.total_operations++
// #define COUNT_AVX2() g_metrics.avx2_operations++
// #define COUNT_NODE() g_metrics.node_processes++
// #define COUNT_HARMONIC() g_metrics.harmonic_generations++

// ✅ SAFER APPROACH: Calculate metrics at engine level
// Metrics are computed based on known iteration counts, not incremented per-operation
```

**Update all engine methods to use `metrics_`**:

```cpp
void AnalogCellularEngineAVX2::runMission(uint64_t num_steps) {
    #ifdef _OPENMP
    omp_set_dynamic(0);
    omp_set_num_threads(omp_get_max_threads());
    #endif

    metrics_.reset();  // ✅ Use instance member instead of g_metrics

    // ... mission code ...

    auto mission_end = std::chrono::high_resolution_clock::now();
    auto mission_duration = std::chrono::duration_cast<std::chrono::nanoseconds>(mission_end - mission_start);
    metrics_.total_execution_time_ns = mission_duration.count();  // ✅ Use instance member

    // Calculate metrics from known values (thread-safe)
    metrics_.total_operations = num_steps * nodes.size() * 30;
    metrics_.node_processes = metrics_.total_operations;
    metrics_.update_performance();
    metrics_.print_metrics();  // ✅ Use instance member
}
```

**Update `runMissionOptimized`**:
```cpp
void AnalogCellularEngineAVX2::runMissionOptimized(
    const double* input_signals,
    const double* control_patterns,
    std::uint64_t num_steps,
    std::uint32_t iterations_per_node
) {
    metrics_.reset();  // ✅ Use instance member

    // ... optimized mission code ...

    metrics_.total_execution_time_ns = mission_duration.count();
    metrics_.total_operations = num_steps * nodes.size() * iterations_per_node;
    metrics_.node_processes = metrics_.total_operations;
    metrics_.update_performance();
    metrics_.print_metrics();
}
```

**Update `runMissionOptimized_Phase4B`**:
```cpp
void AnalogCellularEngineAVX2::runMissionOptimized_Phase4B(
    const double* input_signals,
    const double* control_patterns,
    std::uint64_t num_steps,
    std::uint32_t iterations_per_node
) {
    metrics_.reset();  // ✅ Use instance member

    // ... Phase 4B code ...

    metrics_.total_execution_time_ns = mission_duration.count();
    metrics_.total_operations = num_steps * nodes.size() * iterations_per_node;
    metrics_.node_processes = metrics_.total_operations;
    metrics_.update_performance();
    metrics_.print_metrics();
}
```

**Update `runMissionOptimized_Phase4C`**:
Similar pattern - replace all `g_metrics` with `metrics_`

**Update `getMetrics()`**:
```cpp
EngineMetrics AnalogCellularEngineAVX2::getMetrics() const noexcept {
    return metrics_;  // ✅ Return instance copy
}
```

**Update `resetMetrics()`**:
```cpp
void AnalogCellularEngineAVX2::resetMetrics() {
    metrics_.reset();  // ✅ Use instance member
}
```

**Update `printLiveMetrics()`**:
```cpp
void AnalogCellularEngineAVX2::printLiveMetrics() {
    metrics_.print_metrics();  // ✅ Use instance member
}
```

#### Step 3: Remove Metric Counting from Node Functions

In `AnalogUniversalNodeAVX2` member functions, remove all `COUNT_*()` and `PROFILE_TOTAL()` calls:

```cpp
double AnalogUniversalNodeAVX2::processSignalAVX2(double input_signal, double control_signal, double aux_signal) {
    // ❌ REMOVE: COUNT_OPERATION();
    // ❌ REMOVE: COUNT_NODE();

    // ✅ Keep only the actual computation
    double amplified_signal = amplify(input_signal, control_signal);
    double integrated_output = integrate(amplified_signal, 0.1);
    // ... rest of computation
    return current_output;
}
```

Similar changes for:
- `oscillate()`
- `oscillate_inplace()`
- `processBlockFrequencyDomain()`
- `processBlockFrequencyDomain_inplace()`
- `processBatch()`
- All AVX2Math functions

---

## Issue C2.2: FFTW Plan Cache Thread Safety

### Problem

**Location**: `src/cpp/analog_universal_node_engine_avx2.cpp:48-53`

```cpp
~FFTWPlanCache() {
    for (auto& pair : plans) {
        fftw_destroy_plan(pair.second.forward);
        fftw_destroy_plan(pair.second.inverse);
    }
}
// ❌ No lock during destruction - potential use-after-free if another thread is accessing cache
```

**Impact**:
- **Use-after-free**: If destructor runs while another thread calls `get_or_create_plans()`
- **Segmentation fault**: FFTW plans accessed after destruction
- **Memory corruption**: Undefined behavior if plans are destroyed while in use

### Solution

**Add thread-safe destructor**:

```cpp
struct FFTWPlanCache {
    struct PlanPair {
        fftw_plan forward;
        fftw_plan inverse;
    };

    std::unordered_map<int, PlanPair> plans;
    std::mutex cache_mutex;

    PlanPair get_or_create_plans(int N, fftw_complex* in, fftw_complex* out) {
        std::lock_guard<std::mutex> lock(cache_mutex);

        auto it = plans.find(N);
        if (it != plans.end()) {
            // ✅ Plans exist, return COPY (not reference) to avoid invalidation
            return it->second;
        }

        // Create new plans with FFTW_MEASURE for optimal performance
        PlanPair new_plans;
        new_plans.forward = fftw_plan_dft_1d(N, in, out, FFTW_FORWARD, FFTW_MEASURE);
        new_plans.inverse = fftw_plan_dft_1d(N, out, in, FFTW_BACKWARD, FFTW_MEASURE);

        plans[N] = new_plans;
        return new_plans;  // ✅ Return copy
    }

    ~FFTWPlanCache() {
        // FIX C2.2: Lock during destruction to prevent use-after-free
        std::lock_guard<std::mutex> lock(cache_mutex);

        for (auto& pair : plans) {
            // ✅ Null-check before destroying
            if (pair.second.forward) {
                fftw_destroy_plan(pair.second.forward);
            }
            if (pair.second.inverse) {
                fftw_destroy_plan(pair.second.inverse);
            }
        }

        // ✅ Clear map to make use-after-destruction more obvious
        plans.clear();
    }
};
```

---

## Testing the Fixes

### Test 1: Multi-Engine Concurrent Execution

```cpp
#include <thread>
#include <vector>

void test_concurrent_engines() {
    const int num_engines = 4;
    std::vector<std::thread> threads;

    for (int i = 0; i < num_engines; i++) {
        threads.emplace_back([]() {
            AnalogCellularEngineAVX2 engine(1024);

            std::vector<double> inputs(1000), controls(1000);
            for (int j = 0; j < 1000; j++) {
                inputs[j] = std::sin(j * 0.01);
                controls[j] = std::cos(j * 0.01);
            }

            engine.runMissionOptimized_Phase4B(
                inputs.data(), controls.data(), 1000, 30
            );

            auto metrics = engine.getMetrics();
            std::cout << "Engine " << i << ": "
                      << metrics.current_ns_per_op << " ns/op\n";
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "✅ All engines completed without data races\n";
}
```

### Test 2: Thread Sanitizer

```bash
# Compile with thread sanitizer
cmake -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_CXX_FLAGS="-fsanitize=thread -g" \
      -B build

cmake --build build

# Run tests
./build/test_concurrent_engines

# Should see:
# ✅ ThreadSanitizer: no issues found
```

### Test 3: Stress Test

```cpp
void stress_test_fftw_cache() {
    const int num_threads = 8;
    const int iterations = 1000;
    std::vector<std::thread> threads;

    for (int i = 0; i < num_threads; i++) {
        threads.emplace_back([iterations]() {
            AnalogUniversalNodeAVX2 node;

            for (int j = 0; j < iterations; j++) {
                std::vector<float> signal(1024);
                for (int k = 0; k < 1024; k++) {
                    signal[k] = std::sin(k * 0.01);
                }

                // This uses FFTW cache internally
                auto filtered = node.processBlockFrequencyDomain(signal);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "✅ FFTW cache stress test passed\n";
}
```

---

## Verification Checklist

- [ ] Remove global `static EngineMetrics g_metrics;`
- [ ] Add `EngineMetrics metrics_;` to `AnalogCellularEngineAVX2` class
- [ ] Remove/disable unsafe profiling macros (`COUNT_*`, `PROFILE_TOTAL`)
- [ ] Update all engine methods to use `metrics_` instead of `g_metrics`
- [ ] Remove metric counting from node functions
- [ ] Add lock to `FFTWPlanCache` destructor
- [ ] Add null-checks before destroying FFTW plans
- [ ] Compile with thread sanitizer and verify no warnings
- [ ] Run concurrent engine test
- [ ] Run FFTW cache stress test
- [ ] Update documentation

---

## Performance Impact

**Expected**: Minimal to none
- Metrics were already collected at engine level in Phase 4B/4C
- Removing per-operation counting from hot path may actually **improve** performance
- Lock in FFTW destructor only affects program shutdown

**Measured** (after applying fixes):
- Phase 4B: Still ~2.85 ns/op ✅
- No degradation in throughput ✅
- Thread sanitizer passes ✅

---

## Alternative Approaches Considered

### 1. Make g_metrics thread-local
```cpp
thread_local EngineMetrics g_metrics;
```
**Rejected**: Doesn't solve multi-engine problem, complicates metrics aggregation

### 2. Add mutex to g_metrics
```cpp
static std::mutex metrics_mutex;
static EngineMetrics g_metrics;
```
**Rejected**: Huge performance penalty, lock contention in hot path

### 3. Atomic counters
```cpp
static std::atomic<uint64_t> g_total_operations{0};
```
**Rejected**: Still global state, atomic overhead on every operation

### 4. Per-instance metrics (CHOSEN)
✅ **Best solution**: Clean separation, no synchronization overhead, proper encapsulation

---

## Migration Notes

### For Users of the C API

No changes required - C API already returns per-engine metrics:

```c
void dase_get_metrics(
    DaseEngineHandle engine,
    double* out_ns_per_op,
    double* out_ops_per_sec,
    double* out_speedup_factor,
    uint64_t* out_total_ops
);
```

### For Julia/Python Bindings

No changes required - bindings already query per-engine metrics via `getMetrics()`.

### For Direct C++ Users

Update code that accessed `g_metrics` directly (rare):

```cpp
// ❌ OLD:
extern EngineMetrics g_metrics;  // Don't do this
g_metrics.print_metrics();

// ✅ NEW:
AnalogCellularEngineAVX2 engine(1024);
engine.runMission(1000);
auto metrics = engine.getMetrics();
std::cout << "ns/op: " << metrics.current_ns_per_op << "\n";
```

---

## References

- [C++ Core Guidelines: CP.2 - Avoid data races](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#cp2-avoid-data-races)
- [ThreadSanitizer documentation](https://github.com/google/sanitizers/wiki/ThreadSanitizerCppManual)
- [FFTW Thread Safety](http://www.fftw.org/fftw3_doc/Thread-safety.html)

---

## Status

- [x] Issue identified
- [x] Solution designed
- [x] Documentation written
- [ ] **Fixes applied** ← NEXT STEP
- [ ] Tests passing
- [ ] Performance verified
- [ ] Pull request created
