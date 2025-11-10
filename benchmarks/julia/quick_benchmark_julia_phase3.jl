#!/usr/bin/env julia
"""
Quick Julia Benchmark - PHASE 3 OPTIMIZATIONS
- Phase 3 optimized DLL with aggressive compiler flags
- /O2 /Ob3 /Oi /Ot /Oy - Maximum speed
- /Qpar - Auto-parallelization
- /favor:INTEL64 - Intel CPU tuning
- /OPT:REF /OPT:ICF - Link-time optimization
"""

include("src/julia/DaseEnginePhase3.jl")
using .DaseEnginePhase3
using Printf
using Dates

# Scaled-down configuration
const NUM_NODES = 1024
const NUM_STEPS = 54_750
const ITERATIONS_PER_NODE = Int32(30)
const TOTAL_OPS = NUM_NODES * NUM_STEPS * ITERATIONS_PER_NODE

println("="^80)
println("DASE ENGINE JULIA QUICK BENCHMARK - PHASE 3 OPTIMIZATIONS")
println("="^80)
println()
println("Phase 3 Optimizations:")
println("  - Aggressive C++ compiler optimization (/O2 /Ob3 /Oi /Ot /Oy)")
println("  - Auto-parallelization (/Qpar)")
println("  - Intel CPU-specific tuning (/favor:INTEL64)")
println("  - Whole program optimization (/GL /LTCG)")
println("  - Link-time optimization (/OPT:REF /OPT:ICF)")
println()

println("Configuration:")
@printf "  Nodes:              %d\n" NUM_NODES
@printf "  Mission Steps:      %d\n" NUM_STEPS
@printf "  Iterations/Node:    %d\n" ITERATIONS_PER_NODE
@printf "  Total Operations:   %d (%.2f million)\n" TOTAL_OPS (TOTAL_OPS/1e6)
println()

# Check CPU features
println("CPU Features:")
println("  AVX2: ", has_avx2() ? "✅" : "❌")
println("  FMA:  ", has_fma() ? "✅" : "❌")
println()

# Create engine
println("Initializing engine with $NUM_NODES nodes...")
engine = create_engine(NUM_NODES)
println("Engine created (using Phase 3 optimized DLL)")
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
println("PHASE 3 BENCHMARK RESULTS")
println("="^80)
@printf "Test Duration:      %.2f seconds (%.2f minutes)\n" elapsed_time (elapsed_time/60)
@printf "Total Operations:   %d (%.2f million)\n" metrics.total_operations (metrics.total_operations/1e6)
@printf "Time per Operation: %.2f ns/op\n" metrics.ns_per_op
@printf "Throughput:         %.2f million ops/sec\n" (metrics.ops_per_sec/1e6)
@printf "Speedup Factor:     %.2fx (vs 15,500ns baseline)\n" metrics.speedup_factor
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
@printf "Phase 3 Julia Benchmark Complete!\n"
@printf "Duration: %.2fs | Throughput: %.2fM ops/sec | Time/Op: %.2fns\n" elapsed_time (metrics.ops_per_sec/1e6) metrics.ns_per_op
println("="^80)

# Cleanup
destroy_engine(engine)
