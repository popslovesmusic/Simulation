#!/usr/bin/env python3
"""
Final verification test for Oscillator and Filter implementation
"""
import sys
import json
import time
from datetime import datetime

try:
    import dase_engine as de
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

results = {
    "timestamp": datetime.now().isoformat(),
    "tests": {}
}

print("="*70)
print("FINAL VERIFICATION: OSCILLATOR AND FILTER IMPLEMENTATION")
print("="*70)

# Test 1: Oscillator Waveform Generation
print("\n[TEST 1] Oscillator - Waveform Generation")
print("-" * 70)
node = de.AnalogUniversalNodeAVX2()

test_cases = [
    (440.0, 0.05),   # A4, 50ms
    (1000.0, 0.1),   # 1kHz, 100ms
    (100.0, 0.2),    # 100Hz, 200ms
]

for freq, duration in test_cases:
    start = time.perf_counter()
    waveform = node.oscillate(freq, duration)
    elapsed = time.perf_counter() - start

    expected_samples = int(48000 * duration)
    actual_samples = len(waveform)
    min_val = min(waveform)
    max_val = max(waveform)

    # Check correctness
    size_ok = actual_samples == expected_samples
    range_ok = -1.0 <= min_val <= 1.0 and -1.0 <= max_val <= 1.0
    status = "PASS" if (size_ok and range_ok) else "FAIL"

    print(f"  {freq:6.1f} Hz, {duration*1000:5.1f}ms: ", end="")
    print(f"{actual_samples:5d} samples [{min_val:+.4f}, {max_val:+.4f}] ", end="")
    print(f"({elapsed*1000:.3f}ms) - {status}")

    results["tests"][f"oscillator_{freq}hz"] = {
        "frequency_hz": freq,
        "duration_s": duration,
        "samples": actual_samples,
        "range": [min_val, max_val],
        "time_ms": elapsed * 1000,
        "status": status
    }

# Test 2: Filter - Frequency Domain Processing
print("\n[TEST 2] Filter - Frequency Domain Processing")
print("-" * 70)

import math

test_sizes = [64, 128, 256, 512, 1024]
for size in test_sizes:
    # Create test signal (mixture of frequencies)
    signal = []
    for i in range(size):
        val = 0.5 * math.sin(2 * math.pi * i / 8)   # Low frequency
        val += 0.3 * math.sin(2 * math.pi * i / 4)   # Mid frequency
        val += 0.2 * math.sin(2 * math.pi * i / 2)   # High frequency
        signal.append(val)

    start = time.perf_counter()
    filtered = node.process_block_frequency_domain(signal)
    elapsed = time.perf_counter() - start

    # Measure energy reduction (filter should reduce high and low frequencies)
    input_energy = sum(x*x for x in signal)
    output_energy = sum(x*x for x in filtered)
    energy_ratio = output_energy / input_energy if input_energy > 0 else 0

    size_ok = len(filtered) == len(signal)
    status = "PASS" if size_ok else "FAIL"

    print(f"  {size:4d} samples: ", end="")
    print(f"Energy: {input_energy:8.3f} -> {output_energy:8.3f} ", end="")
    print(f"(ratio: {energy_ratio:.4f}) ({elapsed*1000:.3f}ms) - {status}")

    results["tests"][f"filter_{size}samples"] = {
        "samples": size,
        "input_energy": input_energy,
        "output_energy": output_energy,
        "energy_ratio": energy_ratio,
        "time_ms": elapsed * 1000,
        "status": status
    }

# Test 3: Integration with Engine
print("\n[TEST 3] Integration - Full Engine Test")
print("-" * 70)

engine = de.AnalogCellularEngineAVX2(1024)
print("  Engine: 1024 nodes, 3000 mission steps")

start = time.perf_counter()
engine.run_mission(3000)
elapsed = time.perf_counter() - start

metrics = engine.get_metrics()

print(f"  Execution time: {elapsed:.3f} seconds")
print(f"  Total operations: {metrics.total_operations:,}")
print(f"  AVX2 operations: {metrics.avx2_operations:,} ({100*metrics.avx2_operations/metrics.total_operations:.1f}%)")
print(f"  Performance: {metrics.current_ns_per_op:.2f} ns/op")
print(f"  Speedup: {metrics.speedup_factor:.2f}x vs baseline")
print(f"  Throughput: {metrics.current_ops_per_second/1e6:.2f} million ops/sec")

target_achieved = metrics.current_ns_per_op <= 8000.0
status = "PASS" if target_achieved else "FAIL"
print(f"  Target (8000 ns/op): {'ACHIEVED' if target_achieved else 'NOT ACHIEVED'} - {status}")

results["tests"]["engine_integration"] = {
    "nodes": 1024,
    "steps": 3000,
    "elapsed_s": elapsed,
    "total_operations": metrics.total_operations,
    "avx2_operations": metrics.avx2_operations,
    "avx2_percentage": 100 * metrics.avx2_operations / metrics.total_operations,
    "ns_per_op": metrics.current_ns_per_op,
    "speedup": metrics.speedup_factor,
    "ops_per_second": metrics.current_ops_per_second,
    "target_achieved": target_achieved,
    "status": status
}

# Summary
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)

all_tests = results["tests"]
passed = sum(1 for t in all_tests.values() if t["status"] == "PASS")
total = len(all_tests)

print(f"Tests Passed: {passed}/{total}")
print(f"Status: {'ALL TESTS PASSED' if passed == total else 'SOME TESTS FAILED'}")

results["summary"] = {
    "passed": passed,
    "total": total,
    "all_passed": passed == total
}

# Save results
output_file = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nDetailed results saved to: {output_file}")
print("="*70)
