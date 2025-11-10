"""
DaseEnginePhase4A.jl - Using Phase 4A optimized DLL

Phase 4A Optimizations:
- Hot-path version without profiling counters
- FORCE_INLINE for trivial functions
- Direct pointer access
- Removed thread-local storage overhead
- Bulk metrics calculation
"""
module DaseEnginePhase4A

using Printf

# Use Phase 4A optimized DLL
const DASE_LIB = joinpath(@__DIR__, "..", "..", "dase_engine_phase4a.dll")

function create_engine(num_nodes::Integer)
    handle = ccall((:dase_create_engine, DASE_LIB),
                   Ptr{Cvoid}, (Cuint,), num_nodes)
    if handle == C_NULL
        error("Failed to create DASE engine (allocation failed)")
    end
    return handle
end

function destroy_engine(handle::Ptr{Cvoid})
    ccall((:dase_destroy_engine, DASE_LIB),
          Cvoid, (Ptr{Cvoid},), handle)
end

@inline function run_mission_optimized!(
    handle::Ptr{Cvoid},
    input_signals::Vector{Float64},
    control_patterns::Vector{Float64},
    iterations_per_node::Int32 = Int32(30)
)::Nothing
    num_steps::Int = length(input_signals)
    @assert length(control_patterns) == num_steps "Array length mismatch"

    ccall((:dase_run_mission_optimized, DASE_LIB),
          Cvoid,
          (Ptr{Cvoid}, Ptr{Cdouble}, Ptr{Cdouble}, Culonglong, Cuint),
          handle,
          pointer(input_signals),
          pointer(control_patterns),
          UInt64(num_steps),
          UInt32(iterations_per_node))

    return nothing
end

function get_metrics(handle::Ptr{Cvoid})
    ns_per_op = Ref{Cdouble}(0.0)
    ops_per_sec = Ref{Cdouble}(0.0)
    speedup = Ref{Cdouble}(0.0)
    total_ops = Ref{Culonglong}(0)

    ccall((:dase_get_metrics, DASE_LIB),
          Cvoid,
          (Ptr{Cvoid}, Ptr{Cdouble}, Ptr{Cdouble}, Ptr{Cdouble}, Ptr{Culonglong}),
          handle, ns_per_op, ops_per_sec, speedup, total_ops)

    return (ns_per_op = ns_per_op[],
            ops_per_sec = ops_per_sec[],
            speedup_factor = speedup[],
            total_operations = total_ops[])
end

function has_avx2()
    result = ccall((:dase_has_avx2, DASE_LIB), Cint, ())
    return result != 0
end

function has_fma()
    result = ccall((:dase_has_fma, DASE_LIB), Cint, ())
    return result != 0
end

@inline function compute_signals_simd(num_steps::Int)
    inputs = Vector{Float64}(undef, num_steps)
    controls = Vector{Float64}(undef, num_steps)

    @inbounds @simd for i in 1:num_steps
        x = (i - 1) * 0.01
        inputs[i] = sin(x)
        controls[i] = cos(x)
    end

    return inputs, controls
end

export create_engine, destroy_engine, run_mission_optimized!, get_metrics
export has_avx2, has_fma, compute_signals_simd

end # module
