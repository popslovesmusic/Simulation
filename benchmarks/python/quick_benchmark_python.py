#!/usr/bin/env python3
"""
Quick Python Benchmark - Scaled down for fast comparison
Duration: ~30-60 seconds
"""

import time
import sys
from datetime import datetime

try:
    import dase_engine as de
except ImportError:
    print("ERROR: dase_engine module not found")
    sys.exit(1)

# Scaled-down configuration (1/100th of full endurance test)
NUM_NODES = 1024
NUM_STEPS = 54750  # reduced from 5,475,000
ITERATIONS_PER_NODE = 30
TOTAL_OPS = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE

print("="*80)
print("DASE ENGINE PYTHON QUICK BENCHMARK")
print("="*80)
print()

print("Configuration:")
print(f"  Nodes:              {NUM_NODES}")
print(f"  Mission Steps:      {NUM_STEPS:,}")
print(f"  Iterations/Node:    {ITERATIONS_PER_NODE}")
print(f"  Total Operations:   {TOTAL_OPS:,} ({TOTAL_OPS/1e6:.2f} million)")
print()

# Check CPU features
caps = de.CPUFeatures
print("CPU Features:")
print(f"  AVX2: {'YES' if caps.has_avx2() else 'NO'}")
print(f"  FMA:  {'YES' if caps.has_fma() else 'NO'}")
print()

# Create engine
print(f"Initializing engine with {NUM_NODES} nodes...")
engine = de.AnalogCellularEngineAVX2(NUM_NODES)
print("Engine created")
print()

# Pre-compute signals
print(f"Pre-computing {NUM_STEPS:,} input signals...")
import math
start = time.perf_counter()
input_signals = [math.sin(i * 0.01) for i in range(NUM_STEPS)]
elapsed = time.perf_counter() - start
print(f"  Completed in {elapsed:.3f}s")

print(f"Pre-computing {NUM_STEPS:,} control patterns...")
start = time.perf_counter()
control_patterns = [math.cos(i * 0.01) for i in range(NUM_STEPS)]
elapsed = time.perf_counter() - start
print(f"  Completed in {elapsed:.3f}s")
print()

print("="*80)
print("Starting benchmark... (this will take ~30-60 seconds)")
print("="*80)
print()

start_time = datetime.now()
print(f"Start time: {start_time.strftime('%H:%M:%S')}")
print()

# Run mission
start_perf = time.perf_counter()
engine.run_mission(NUM_STEPS)
elapsed_time = time.perf_counter() - start_perf

end_time = datetime.now()
print(f"End time: {end_time.strftime('%H:%M:%S')}")
print()

# Get metrics
metrics = engine.get_metrics()

# Display results
print("="*80)
print("QUICK BENCHMARK RESULTS")
print("="*80)
print(f"Test Duration:      {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
print(f"Total Operations:   {metrics.total_operations:,} ({metrics.total_operations/1e6:.2f} million)")
print(f"Time per Operation: {metrics.current_ns_per_op:.2f} ns/op")
print(f"Throughput:         {metrics.current_ops_per_second/1e6:.2f} million ops/sec")
print(f"Speedup Factor:     {metrics.speedup_factor:.2f}x (vs 15,500ns baseline)")
print()

# Validation
expected_ops = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE
accuracy_pct = (metrics.total_operations / expected_ops) * 100

print("VALIDATION:")
print("-"*80)
print(f"Expected Operations: {expected_ops:,} ({expected_ops/1e6:.2f} million)")
print(f"Actual Operations:   {metrics.total_operations:,} ({metrics.total_operations/1e6:.2f} million)")
print(f"Test Accuracy:       {accuracy_pct:.2f}%")
print()

if accuracy_pct > 99.9:
    print("BENCHMARK PASSED: 100% accuracy maintained")
else:
    print(f"WARNING: Accuracy at {accuracy_pct:.2f}%")

print()
print("="*80)
print(f"Python Benchmark Complete!")
print(f"Duration: {elapsed_time:.2f}s | Throughput: {metrics.current_ops_per_second/1e6:.2f}M ops/sec | Time/Op: {metrics.current_ns_per_op:.2f}ns")
print("="*80)
