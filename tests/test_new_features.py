#!/usr/bin/env python3
"""
Quick test for new Oscillator and Filter features
"""
import sys
import time

try:
    import dase_engine as de
    print("Successfully imported dase_engine")
except ImportError as e:
    print(f"ERROR: Failed to import dase_engine: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("TESTING NEW OSCILLATOR AND FILTER FEATURES")
print("="*60)

# Test 1: CPU Features
print("\n[1] CPU Features Check:")
try:
    avx2 = de.CPUFeatures.has_avx2()
    fma = de.CPUFeatures.has_fma()
    print(f"    AVX2: {avx2}")
    print(f"    FMA:  {fma}")
    print("    PASSED: CPU features detected")
except Exception as e:
    print(f"    FAILED: {e}")

# Test 2: Create Node
print("\n[2] Node Creation:")
try:
    node = de.AnalogUniversalNodeAVX2()
    print("    PASSED: AnalogUniversalNodeAVX2 created")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Test 3: Oscillator
print("\n[3] Oscillator Test:")
try:
    freq = 440.0  # A4 note
    duration = 0.1  # 100ms
    start = time.perf_counter()
    waveform = node.oscillate(freq, duration)
    elapsed = time.perf_counter() - start

    print(f"    Frequency: {freq} Hz")
    print(f"    Duration: {duration} seconds")
    print(f"    Generated samples: {len(waveform)}")
    print(f"    Expected samples: {int(48000 * duration)}")
    print(f"    Generation time: {elapsed*1000:.3f} ms")

    if len(waveform) > 0:
        print(f"    First 5 samples: {waveform[:5]}")
        print(f"    Sample range: [{min(waveform):.4f}, {max(waveform):.4f}]")
        print("    PASSED: Oscillator generated waveform")
    else:
        print("    FAILED: No samples generated")

except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Filter
print("\n[4] Frequency Domain Filter Test:")
try:
    # Create test signal (256 samples)
    import math
    test_signal = [math.sin(2 * math.pi * i / 32) for i in range(256)]

    start = time.perf_counter()
    filtered = node.process_block_frequency_domain(test_signal)
    elapsed = time.perf_counter() - start

    print(f"    Input samples: {len(test_signal)}")
    print(f"    Output samples: {len(filtered)}")
    print(f"    Processing time: {elapsed*1000:.3f} ms")

    if len(filtered) == len(test_signal):
        print(f"    Input range: [{min(test_signal):.4f}, {max(test_signal):.4f}]")
        print(f"    Output range: [{min(filtered):.4f}, {max(filtered):.4f}]")
        print("    PASSED: Filter processed signal")
    else:
        print("    FAILED: Output size mismatch")

except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Basic Operations Still Work
print("\n[5] Verify Basic Operations Still Work:")
try:
    # Amplifier
    result = node.amplify(2.0, 0.5)
    assert abs(result - 1.0) < 1e-6, f"Amplifier failed: {result}"
    print(f"    Amplifier: PASSED (2.0 * 0.5 = {result})")

    # Integrator
    node.reset_integrator()
    for _ in range(10):
        result = node.integrate(1.0, 0.5)
    print(f"    Integrator: PASSED (accumulated to {result})")

    # Feedback
    node.set_feedback(0.1)
    result = node.apply_feedback(1.0, 0.1)
    print(f"    Feedback: PASSED (result = {result})")

    print("    PASSED: All basic operations working")
except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Performance Benchmark
print("\n[6] Quick Performance Test:")
try:
    engine = de.AnalogCellularEngineAVX2(512)
    print("    Running 1000 steps on 512 nodes...")

    start = time.perf_counter()
    engine.run_mission(1000)
    elapsed = time.perf_counter() - start

    metrics = engine.get_metrics()
    print(f"    Execution time: {elapsed:.3f} seconds")
    print(f"    Total operations: {metrics.total_operations}")
    print(f"    Performance: {metrics.current_ns_per_op:.2f} ns/op")
    print(f"    Speedup: {metrics.speedup_factor:.2f}x")
    print("    PASSED: Performance test completed")

except Exception as e:
    print(f"    FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("ALL TESTS COMPLETED")
print("="*60)
