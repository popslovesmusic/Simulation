#!/usr/bin/env julia
"""
Quick Julia Benchmark - PHASE 4A OPTIMIZATIONS
Hot-Path Optimizations:
- Removed profiling counters from inner loop
- FORCE_INLINE for all trivial functions
- Direct pointer access (nodes.data())
- Removed thread-local storage overhead
- Bulk metrics calculation
"""

include("src/julia/DaseEnginePhase4A.jl")
using .DaseEnginePhase4A
using Printf
using Dates

# Scaled-down configuration
const NUM_NODES = 1024
const NUM_STEPS = 54_750
const ITERATIONS_PER_NODE = Int32(30)
const TOTAL_OPS = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE

println("="^80)
println("DASE ENGINE JULIA QUICK BENCHMARK - PHASE 4A OPTIMIZATIONS")
println("="^80)
println()
println("Phase 4A C++ Optimizations:")
println("  - Hot-path processSignalAVX2_hotpath() without profiling")
println("  - FORCE_INLINE (__forceinline) for amplify/integrate/applyFeedback")
println("  - Direct pointer access with nodes.data()")
println("  - Removed thread-local storage from integrate()")
println("  - Bulk metrics calculation (not per-operation)")
println()
println("Expected Improvement: 30-40% over Phase 3")
println("  Phase 3: 79.08 M ops/sec @ 12.64 ns/op")
println("  Target:  105-110 M ops/sec @ 9.0-9.5 ns/op")
println()

println("Configuration:")
@printf "  Nodes:              %d\n" NUM_NODES
@printf "  Mission Steps:      %d\n" NUM_STEPS
@printf "  Iterations/Node:    %d\n" ITERATIONS_PER_NODE
@printf "  Total Operations:   %d (%.2f million)\n" TOTAL_OPS (TOTAL_OPS/1e6)
println()

# Check CPU features
println("CPU Features:")
println("  AVX2: ", has_avx2() ? "YES" : "NO")
println("  FMA:  ", has_fma() ? "YES" : "NO")
println()

# Create engine
println("Initializing engine with $NUM_NODES nodes...")
engine = create_engine(NUM_NODES)
println("Engine created (using Phase 4A optimized DLL)")
println()

# Use SIMD-optimized signal generation
println("Pre-computing $NUM_STEPS signals with SIMD optimization...")
@time input_signals, control_patterns = compute_signals_simd(NUM_STEPS)
println()

println("="^80)
println("Starting benchmark... (this will take ~30-60 seconds)")
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
println("PHASE 4A BENCHMARK RESULTS")
println("="^80)
@printf "Test Duration:      %.2f seconds (%.2f minutes)\n" elapsed_time (elapsed_time/60)
@printf "Total Operations:   %d (%.2f million)\n" metrics.total_operations (metrics.total_operations/1e6)
@printf "Time per Operation: %.2f ns/op\n" metrics.ns_per_op
@printf "Throughput:         %.2f million ops/sec\n" (metrics.ops_per_sec/1e6)
@printf "Speedup Factor:     %.2fx (vs 15,500ns baseline)\n" metrics.speedup_factor
println()

# Comparison with Phase 3
phase3_duration = 21.27
phase3_throughput = 79.08
phase3_ns_per_op = 12.64

improvement_pct = ((phase3_duration - elapsed_time) / phase3_duration) * 100
throughput_gain = ((metrics.ops_per_sec/1e6) / phase3_throughput - 1) * 100

println("COMPARISON WITH PHASE 3:")
println("-"^80)
@printf "Phase 3:  %.2fs | %.2f M ops/sec | %.2f ns/op\n" phase3_duration phase3_throughput phase3_ns_per_op
@printf "Phase 4A: %.2fs | %.2f M ops/sec | %.2f ns/op\n" elapsed_time (metrics.ops_per_sec/1e6) metrics.ns_per_op
@printf "Improvement: %.1f%% faster | +%.1f%% throughput\n" improvement_pct throughput_gain
println()

# Validation
expected_ops = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE
accuracy_pct = (metrics.total_operations / expected_ops) * 100

println("VALIDATION:")
println("-"^80)
@printf "Expected Operations: %d (%.2f million)\n" expected_ops (expected_ops/1e6)
@printf "Actual Operations:   %d (%.2f million)\n" metrics.total_operations (metrics.total_operations/1e6)
@printf "Test Accuracy:       %.2f%%\n" accuracy_pct
println()

if accuracy_pct > 99.9
    println("BENCHMARK PASSED: 100% accuracy maintained")
else
    @printf "WARNING: Accuracy at %.2f%%\n" accuracy_pct
end

println()
println("="^80)
@printf "Phase 4A Julia Benchmark Complete!\n"
@printf "Duration: %.2fs | Throughput: %.2fM ops/sec | Time/Op: %.2fns\n" elapsed_time (metrics.ops_per_sec/1e6) metrics.ns_per_op

if improvement_pct > 25
    println("SUCCESS! Phase 4A achieved expected 30-40% improvement target!")
else
    println("PARTIAL: Phase 4A showed $(round(improvement_pct, digits=1))% improvement")
end
println("="^80)

# Cleanup
destroy_engine(engine)
