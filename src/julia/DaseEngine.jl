"""
DaseEngine.jl - Unified Julia FFI interface for DASE Engine

This module provides a clean, unified interface to the DASE C++ engine
with support for multiple optimization phases.

Usage:
    using DaseEngine

    # Use specific version
    set_dll_version(:phase4b)

    engine = create_engine(1024)
    inputs, controls = compute_signals_simd(54_750)
    run_mission!(engine, inputs, controls)
    metrics = get_metrics(engine)
    destroy_engine(engine)
"""
module DaseEngine

using Printf

# Export main API
export create_engine, destroy_engine, run_mission!, run_mission_optimized!
export get_metrics, has_avx2, has_fma
export compute_signals_simd

# ============================================================================
# DLL VERSION MANAGEMENT
# ============================================================================

# FIX C4.1: Flexible DLL path with environment variable fallback
const DASE_DLL_PATH = let
    # Try relative path first (development environment)
    local_dll = joinpath(@__DIR__, "..", "..", "dase_engine_phase4b.dll")
    if isfile(local_dll)
        local_dll
    else
        # Fallback to environment variable (production deployment)
        env_path = get(ENV, "DASE_DLL_PATH", "")
        if !isempty(env_path) && isfile(env_path)
            env_path
        else
            # Last resort: try system PATH
            "dase_engine_phase4b.dll"
        end
    end
end

# FIX C4.2: Validate DLL exists and can be loaded during module initialization
function __init__()
    if !isfile(DASE_DLL_PATH) && DASE_DLL_PATH != "dase_engine_phase4b.dll"
        error("""
        DASE DLL not found at: $DASE_DLL_PATH

        Please ensure:
        1. The DLL has been built (run CMake build in project root)
        2. Set DASE_DLL_PATH environment variable to the correct location, or
        3. Place the DLL in the project root directory

        Example:
            ENV["DASE_DLL_PATH"] = "C:/path/to/dase_engine_phase4b.dll"
        """)
    end

    # Try to load a simple function to verify DLL is loadable
    try
        ccall((:dase_has_avx2, DASE_DLL_PATH), Cint, ())
    catch e
        error("""
        Failed to load DASE DLL from: $DASE_DLL_PATH
        Error: $e

        This may be due to missing dependencies:
        - libfftw3-3.dll (FFTW3 library)
        - MSVC 2022 runtime libraries (vcruntime140.dll, msvcp140.dll)
        - Windows Universal CRT

        Please ensure all dependencies are in the system PATH or the same directory as the DLL.
        """)
    end

    @info "DASE Engine loaded successfully from: $DASE_DLL_PATH"
end

# ============================================================================
# ENGINE LIFECYCLE
# ============================================================================

"""
    create_engine(num_nodes::Integer) -> Ptr{Cvoid}

Create a new DASE engine with the specified number of nodes.

Arguments:
- num_nodes: Number of analog nodes (typically 128-1024)

Returns:
- Handle to the engine (must be freed with destroy_engine)
"""
function create_engine(num_nodes::Integer)
    handle = ccall((:dase_create_engine, DASE_DLL_PATH),
                   Ptr{Cvoid}, (Cuint,), num_nodes)
    if handle == C_NULL
        error("Failed to create DASE engine with $num_nodes nodes (allocation failed)")
    end
    return handle
end

"""
    destroy_engine(handle::Ptr{Cvoid})

Destroy the engine and free all allocated memory.
"""
function destroy_engine(handle::Ptr{Cvoid})
    ccall((:dase_destroy_engine, DASE_DLL_PATH),
          Cvoid, (Ptr{Cvoid},), handle)
end

# ============================================================================
# MISSION EXECUTION
# ============================================================================

"""
    run_mission!(handle, input_signals, control_patterns, iterations_per_node=30)

Run optimized Phase 4B mission with pre-computed input signals.

Arguments:
- handle: Engine handle from create_engine
- input_signals: Vector{Float64} of pre-computed input signals
- control_patterns: Vector{Float64} of pre-computed control patterns
- iterations_per_node: Number of iterations per node (default: 30)
"""
@inline function run_mission!(
    handle::Ptr{Cvoid},
    input_signals::Vector{Float64},
    control_patterns::Vector{Float64},
    iterations_per_node::Integer = 30
)::Nothing
    num_steps::Int = length(input_signals)
    @assert length(control_patterns) == num_steps "Array length mismatch"

    # Use Phase 4B optimized function (barrier elimination + cache locality)
    ccall((:dase_run_mission_optimized_phase4b, DASE_DLL_PATH),
          Cvoid,
          (Ptr{Cvoid}, Ptr{Cdouble}, Ptr{Cdouble}, Culonglong, Cuint),
          handle,
          pointer(input_signals),
          pointer(control_patterns),
          UInt64(num_steps),
          UInt32(iterations_per_node))

    return nothing
end

# Alias for backward compatibility
const run_mission_optimized! = run_mission!

# ============================================================================
# METRICS
# ============================================================================

"""
    get_metrics(handle::Ptr{Cvoid}) -> NamedTuple

Get performance metrics from the last mission run.
"""
function get_metrics(handle::Ptr{Cvoid})
    ns_per_op = Ref{Cdouble}(0.0)
    ops_per_sec = Ref{Cdouble}(0.0)
    speedup = Ref{Cdouble}(0.0)
    total_ops = Ref{Culonglong}(0)

    ccall((:dase_get_metrics, DASE_DLL_PATH),
          Cvoid,
          (Ptr{Cvoid}, Ptr{Cdouble}, Ptr{Cdouble}, Ptr{Cdouble}, Ptr{Culonglong}),
          handle, ns_per_op, ops_per_sec, speedup, total_ops)

    return (ns_per_op = ns_per_op[],
            ops_per_sec = ops_per_sec[],
            speedup_factor = speedup[],
            total_operations = total_ops[])
end

# ============================================================================
# CPU FEATURES
# ============================================================================

"""
    has_avx2() -> Bool

Check if the CPU supports AVX2 instructions.
"""
function has_avx2()
    result = ccall((:dase_has_avx2, DASE_DLL_PATH), Cint, ())
    return result != 0
end

"""
    has_fma() -> Bool

Check if the CPU supports FMA (Fused Multiply-Add) instructions.
"""
function has_fma()
    result = ccall((:dase_has_fma, DASE_DLL_PATH), Cint, ())
    return result != 0
end

# ============================================================================
# SIGNAL GENERATION
# ============================================================================

"""
    compute_signals_simd(num_steps::Int) -> (Vector{Float64}, Vector{Float64})

Pre-compute input signals and control patterns using SIMD optimization.
"""
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

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

function __init__()
    # Check if Phase 4B DLL exists
    if !isfile(DASE_DLL_PATH)
        @error "Phase 4B DLL not found at: $DASE_DLL_PATH"
        @error "Please compile the DLL using: python compile_dll_phase4b.py"
    else
        @info "DaseEngine initialized with Phase 4B (optimized)"
        @info "  DLL: $DASE_DLL_PATH"
        @info "  AVX2 support: $(has_avx2())"
        @info "  FMA support: $(has_fma())"
    end
end

end # module DaseEngine
