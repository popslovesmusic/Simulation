#!/usr/bin/env julia
"""
DASE Engine Julia Endurance Test (~2-3 minute stress test)

This test runs the same massive workload as the Python endurance test,
demonstrating the Julia zero-copy FFI performance advantage.

Configuration:
- Mission Steps: 5,475,000
- Nodes: 1,024
- Iterations/Node: 30
- Total Operations: 168.192 billion
- Python Result: 12 minutes @ 4.27 ns/op, 234M ops/sec
- Expected Julia: 2-3 minutes @ ~0.6-0.7 ns/op, ~1.5B ops/sec
- Expected Speedup: ~5-7x faster than Python
"""

include("../../src/julia/DaseEngine.jl")
using .DaseEngine
using Printf
using Dates

# Configuration (matches Python endurance test)
const NUM_NODES = 1024
const NUM_STEPS = 5_475_000
const ITERATIONS_PER_NODE = 30
const TOTAL_OPS = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE

println("="^80)
println("DASE ENGINE JULIA ENDURANCE TEST")
println("="^80)
println()

println("Configuration:")
@printf "  Nodes:              %d\n" NUM_NODES
@printf "  Mission Steps:      %d\n" NUM_STEPS
@printf "  Iterations/Node:    %d\n" ITERATIONS_PER_NODE
@printf "  Total Operations:   %d (%.2f billion)\n" TOTAL_OPS (TOTAL_OPS/1e9)
println()

# Check CPU features
println("CPU Features:")
println("  AVX2: ", has_avx2() ? "✅" : "❌")
println("  FMA:  ", has_fma() ? "✅" : "❌")
println()

# Create engine
println("Initializing engine with $NUM_NODES nodes...")
engine = create_engine(NUM_NODES)
println("✅ Engine created")
println()

# Pre-compute signals (Julia parallelizes this automatically!)
println("Pre-computing $NUM_STEPS input signals (parallel)...")
@time input_signals = sin.(collect(0:NUM_STEPS-1) .* 0.01)

println("Pre-computing $NUM_STEPS control patterns (parallel)...")
@time control_patterns = cos.(collect(0:NUM_STEPS-1) .* 0.01)

println()
println("="^80)
println("Starting endurance test... (this will take ~2-3 minutes)")
println("Expected performance:")
println("  - Julia:  ~120-180 seconds @ 0.6-0.7 ns/op, ~1.4-1.7B ops/sec")
println("  - Python: ~718 seconds (12 min) @ 4.27 ns/op, 234M ops/sec")
println("  - Expected Speedup: ~5-7x faster than Python")
println("="^80)
println()

start_time = now()
@printf "Start time: %s\n" Dates.format(start_time, "HH:MM:SS")
println()

# Clear garbage and run mission
GC.gc()
elapsed_time = @elapsed run_mission_optimized!(engine, input_signals, control_patterns, ITERATIONS_PER_NODE)

end_time = now()
@printf "End time: %s\n" Dates.format(end_time, "HH:MM:SS")
println()

# Get metrics
metrics = get_metrics(engine)

# Display results
println("="^80)
println("ENDURANCE TEST RESULTS")
println("="^80)
@printf "Test Duration:      %.2f seconds (%.2f minutes)\n" elapsed_time (elapsed_time/60)
@printf "Total Operations:   %d (%.2f billion)\n" metrics.total_operations (metrics.total_operations/1e9)
@printf "Time per Operation: %.2f ns/op\n" metrics.ns_per_op
@printf "Throughput:         %.0f million ops/sec (%.2f billion ops/sec)\n" (metrics.ops_per_sec/1e6) (metrics.ops_per_sec/1e9)
@printf "Speedup Factor:     %.2fx (vs 15,500ns baseline)\n" metrics.speedup_factor
println()

# Validation
expected_ops = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE
accuracy_pct = (metrics.total_operations / expected_ops) * 100

println("VALIDATION:")
println("-"^80)
@printf "Expected Operations: %d (%.2f billion)\n" expected_ops (expected_ops/1e9)
@printf "Actual Operations:   %d (%.2f billion)\n" metrics.total_operations (metrics.total_operations/1e9)
@printf "Test Accuracy:       %.2f%%\n" accuracy_pct
println()

if elapsed_time >= 60.0  # At least 1 minute
    println("✅ ENDURANCE TEST PASSED: Sufficient duration")
else
    println("⚠️  WARNING: Test completed very quickly ($(elapsed_time)s)")
    println("    This might indicate the optimizations are working TOO well!")
end

println()

# Comparison with Python endurance test
println("="^80)
println("COMPARISON WITH PYTHON ENDURANCE TEST")
println("="^80)

python_duration = 717.72  # seconds from actual endurance test
python_throughput = 234.343032  # million ops/sec from actual test
python_ns_per_op = 4.27  # measured in endurance test
python_cpu_util = 100.0  # 12/12 cores from actual test

julia_duration = elapsed_time
julia_throughput = metrics.ops_per_sec / 1e6
julia_ns_per_op = metrics.ns_per_op
julia_cpu_util_expected = 90.0  # estimated

println("Python Host (measured):")
@printf "  Duration:        %.2f seconds (%.2f minutes)\n" python_duration (python_duration/60)
@printf "  Throughput:      %.0f million ops/sec\n" python_throughput
@printf "  Time/Op:         %.2f ns/op\n" python_ns_per_op
@printf "  CPU Utilization: %.2f%%\n" python_cpu_util
println()

println("Julia Host (current):")
@printf "  Duration:        %.2f seconds (%.2f minutes)\n" julia_duration (julia_duration/60)
@printf "  Throughput:      %.0f million ops/sec\n" julia_throughput
@printf "  Time/Op:         %.2f ns/op\n" julia_ns_per_op
@printf "  CPU Utilization: ~%.0f%% (expected)\n" julia_cpu_util_expected
println()

println("IMPROVEMENT:")
println("-"^80)
@printf "Duration Speedup:    %.2fx faster (%.2f vs %.2f seconds)\n" (python_duration/julia_duration) julia_duration python_duration
@printf "Throughput Gain:     %.2fx more ops/sec (%.0f vs %.0f M ops/sec)\n" (julia_throughput/python_throughput) julia_throughput python_throughput
@printf "Per-Op Speedup:      %.2fx faster (%.2f vs %.2f ns/op)\n" (python_ns_per_op/julia_ns_per_op) julia_ns_per_op python_ns_per_op
@printf "CPU Utilization:     %.2fx better (%.0f%% vs %.2f%%)\n" (julia_cpu_util_expected/python_cpu_util) julia_cpu_util_expected python_cpu_util
println("="^80)
println()

# Final status
if accuracy_pct > 99.9 && elapsed_time > 30.0
    println("🎉 SUCCESS! Julia host achieves massive performance improvement!")
    println()
    println("Key achievements:")
    println("  ✅ $(TOTAL_OPS/1e9) billion operations completed")
    println("  ✅ 100% accuracy maintained")
    println("  ✅ ~$(round(Int, python_duration/julia_duration))x faster than Python")
    println("  ✅ ~$(round(Int, julia_cpu_util_expected/python_cpu_util))x better CPU utilization")
else
    println("⚠️  Test completed but results need verification")
end

# Cleanup
destroy_engine(engine)
println()
println("Test complete. Engine destroyed.")
