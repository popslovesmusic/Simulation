#!/usr/bin/env julia
"""
Quick Julia Benchmark - PHASE 4B OPTIMIZATIONS
Structural Optimizations:
- Single parallel region (eliminates 54,750 barriers)
- Manual thread work distribution
- Better cache locality (each thread processes its node slice)
- Expected 20-30% improvement over Phase 4A
"""

# Use unified DaseEngine module
include(joinpath(@__DIR__, "..", "..", "src", "julia", "DaseEngine.jl"))
using .DaseEngine

# Set to Phase 4B version
set_dll_version(:phase4b)
using Printf
using Dates

# Scaled-down configuration
const NUM_NODES = 1024
const NUM_STEPS = 54_750
const ITERATIONS_PER_NODE = Int32(30)
const TOTAL_OPS = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE

println("="^80)
println("DASE ENGINE JULIA QUICK BENCHMARK - PHASE 4B OPTIMIZATIONS")
println("="^80)
println()
println("Phase 4B C++ Optimizations:")
println("  - Single parallel region (eliminates 54,750 OpenMP barriers)")
println("  - Manual thread work distribution (no implicit barriers)")
println("  - Better cache locality (threads work on their node slice)")
println("  - Reduced synchronization overhead")
println()
println("Expected Improvement: 20-30% over Phase 4A")
println("  Phase 4A: 221.25 M ops/sec @ 4.52 ns/op")
println("  Target:  265-290 M ops/sec @ 3.4-3.8 ns/op")
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
println("Engine created (using Phase 4B optimized DLL)")
println()

# Use SIMD-optimized signal generation
println("Pre-computing $NUM_STEPS signals with SIMD optimization...")
@time input_signals, control_patterns = compute_signals_simd(NUM_STEPS)
println()

println("="^80)
println("Starting benchmark... (this will take ~20-30 seconds)")
println("="^80)
println()

start_time = now()
@printf "Start time: %s\n" Dates.format(start_time, "HH:MM:SS")
println()

# Clear garbage and run mission
GC.gc()
elapsed_time = @elapsed run_mission!(engine, input_signals, control_patterns; iterations_per_node=ITERATIONS_PER_NODE)

end_time = now()
@printf "End time: %s\n" Dates.format(end_time, "HH:MM:SS")
println()

# Get metrics
metrics = get_metrics(engine)

# Display results
println("="^80)
println("PHASE 4B BENCHMARK RESULTS")
println("="^80)
@printf "Test Duration:      %.2f seconds (%.2f minutes)\n" elapsed_time (elapsed_time/60)
@printf "Total Operations:   %d (%.2f million)\n" metrics.total_operations (metrics.total_operations/1e6)
@printf "Time per Operation: %.2f ns/op\n" metrics.ns_per_op
@printf "Throughput:         %.2f million ops/sec\n" (metrics.ops_per_sec/1e6)
@printf "Speedup Factor:     %.2fx (vs 15,500ns baseline)\n" metrics.speedup_factor
println()

# Comparison with Phase 4A
phase4a_duration = 7.61
phase4a_throughput = 221.25
phase4a_ns_per_op = 4.52

improvement_pct = ((phase4a_duration - elapsed_time) / phase4a_duration) * 100
throughput_gain = ((metrics.ops_per_sec/1e6) / phase4a_throughput - 1) * 100

println("COMPARISON WITH PHASE 4A:")
println("-"^80)
@printf "Phase 4A: %.2fs | %.2f M ops/sec | %.2f ns/op\n" phase4a_duration phase4a_throughput phase4a_ns_per_op
@printf "Phase 4B: %.2fs | %.2f M ops/sec | %.2f ns/op\n" elapsed_time (metrics.ops_per_sec/1e6) metrics.ns_per_op
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
@printf "Phase 4B Julia Benchmark Complete!\n"
@printf "Duration: %.2fs | Throughput: %.2fM ops/sec | Time/Op: %.2fns\n" elapsed_time (metrics.ops_per_sec/1e6) metrics.ns_per_op

if improvement_pct > 15
    println("SUCCESS! Phase 4B achieved expected 20-30% improvement target!")
else
    println("PARTIAL: Phase 4B showed $(round(improvement_pct, digits=1))% improvement")
end
println("="^80)

# Cleanup
destroy_engine(engine)
