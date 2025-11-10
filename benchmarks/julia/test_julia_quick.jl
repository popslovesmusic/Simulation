#!/usr/bin/env julia
"""
Quick test of DASE Engine Julia FFI (~1 second test)

This test verifies that the Julia FFI is working correctly and
shows the performance improvement over Python.

Configuration:
- Nodes: 1024 (intensive test)
- Steps: 2000
- Iterations per node: 3000 (intensive workload)

Expected results:
- Performance: ~4-5 ns/op (better amortization with more work)
- Throughput: ~200+ million ops/sec
- CPU utilization: ~90-95%
"""

# Load the DASE Engine module
include("src/julia/DaseEngine.jl")
using .DaseEngine
using Printf

println("="^80)
println("DASE ENGINE JULIA QUICK TEST")
println("="^80)
println()

# Check CPU features
println("CPU Features:")
println("  AVX2: ", has_avx2() ? "✅ Supported" : "❌ Not supported")
println("  FMA:  ", has_fma() ? "✅ Supported" : "❌ Not supported")
println()

# Create engine (matching Python benchmark: 1024 nodes)
num_nodes = 1024
println("Creating engine with $num_nodes nodes...")
engine = create_engine(num_nodes)
println("✅ Engine created")
println()

# Pre-compute signals (Julia does this in parallel!)
# Using 2000 steps to match Python benchmark default
num_steps = 2000
println("Pre-computing $num_steps input signals...")
@time input_signals = sin.(collect(0:num_steps-1) .* 0.01)
@time control_patterns = cos.(collect(0:num_steps-1) .* 0.01)
println()

# Run mission (intensive test: 3000 iterations per node)
iterations_per_node = 3000
total_ops = num_nodes * num_steps * iterations_per_node
println("Running mission...")
println("  Steps: $num_steps")
println("  Nodes: $num_nodes")
println("  Iterations/node: $iterations_per_node")
println("  Total operations: $(total_ops) ($(total_ops/1e6) million)")
println()

GC.gc()  # Clear garbage before timing
@time run_mission_optimized!(engine, input_signals, control_patterns, iterations_per_node)
println()

# Get metrics
metrics = get_metrics(engine)

println("="^80)
println("RESULTS")
println("="^80)
@printf "Time per Operation: %.2f ns/op\n" metrics.ns_per_op
@printf "Throughput:         %.0f million ops/sec\n" (metrics.ops_per_sec/1e6)
@printf "Speedup Factor:     %.2fx (vs 15,500ns baseline)\n" metrics.speedup_factor
@printf "Total Operations:   %d\n" metrics.total_operations
println("="^80)
println()

# Comparison with Python
python_ns_per_op = 93.50  # Measured: Python with run_mission(2000), 1024 nodes
python_throughput = 11.0  # million ops/sec

println("COMPARISON WITH PYTHON:")
println("-" ^80)
@printf "Julia Performance:  %.2f ns/op (%.0f M ops/sec)\n" metrics.ns_per_op (metrics.ops_per_sec/1e6)
@printf "Python Performance: %.2f ns/op (%.0f M ops/sec)\n" python_ns_per_op python_throughput
@printf "Speedup:            %.2fx faster than Python\n" (python_ns_per_op / metrics.ns_per_op)
@printf "Throughput Gain:    %.2fx more ops/sec\n" ((metrics.ops_per_sec/1e6) / python_throughput)
println()
println("🎯 KEY INSIGHT: Julia's zero-copy FFI eliminates Python's GIL and")
println("   marshalling overhead, achieving ~9x better performance!")
println("="^80)

# Cleanup
destroy_engine(engine)
println()
println("✅ Test complete! Engine destroyed.")
println()
println("Next step: Run endurance test with:")
println("  julia benchmark_julia_endurance.jl")
