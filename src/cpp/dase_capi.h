#ifndef DASE_CAPI_H
#define DASE_CAPI_H

/**
 * D-ASE Engine C API
 *
 * This header provides a C-compatible interface for the DASE Engine,
 * enabling zero-copy FFI integration with Julia, Rust, and other languages.
 *
 * Performance Note: The optimized mission function eliminates the serial
 * sin/cos bottleneck by accepting pre-computed arrays, unlocking full
 * CPU utilization (~90% vs 12% with Python).
 */

// DLL Export/Import declarations for Windows
#ifdef _WIN32
    #ifdef DASE_BUILD_DLL
        #define DASE_API __declspec(dllexport)
    #else
        #define DASE_API __declspec(dllimport)
    #endif
#else
    #define DASE_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

// =============================================================================
// STATUS CODES
// =============================================================================

/**
 * Status codes for DASE Engine operations
 *
 * These provide detailed error information for proper error handling
 * in host languages (Julia, Rust, Python, etc.)
 */
typedef enum {
    DASE_SUCCESS = 0,
    DASE_ERROR_OUT_OF_MEMORY = 100,
    DASE_ERROR_NULL_HANDLE = 200,
    DASE_ERROR_NULL_POINTER = 201,
    DASE_ERROR_INVALID_PARAM = 202,
    DASE_ERROR_UNKNOWN = 999
} DaseStatus;

/**
 * Get string description of status code
 *
 * @param status Status code
 * @return Null-terminated string describing the error
 */
DASE_API const char* dase_status_string(DaseStatus status);

// =============================================================================
// OPAQUE ENGINE HANDLE
// =============================================================================

/**
 * Opaque pointer to the C++ AnalogCellularEngineAVX2 instance.
 * Host language (Julia/Rust) holds this handle and passes it to all functions.
 */
typedef struct AnalogCellularEngineAVX2_C* DaseEngineHandle;

// =============================================================================
// ENGINE LIFECYCLE
// =============================================================================

/**
 * Create a new DASE engine with the specified number of nodes.
 *
 * @param num_nodes Number of analog nodes to create (typically 128-1024)
 * @return Handle to the engine (must be freed with dase_destroy_engine)
 *
 * @deprecated Use dase_create_engine_ex() for proper error handling
 */
DASE_API DaseEngineHandle dase_create_engine(uint32_t num_nodes);

/**
 * Create a new DASE engine with proper error reporting.
 *
 * @param num_nodes Number of analog nodes to create
 * @param out_handle Output parameter for engine handle (set only on success)
 * @param error_msg_buffer Optional buffer for error message (can be NULL)
 * @param error_msg_size Size of error_msg_buffer
 * @return Status code (DASE_SUCCESS on success)
 */
DASE_API DaseStatus dase_create_engine_ex(
    uint32_t num_nodes,
    DaseEngineHandle* out_handle,
    char* error_msg_buffer,
    uint32_t error_msg_size
);

/**
 * Destroy the engine and free all allocated memory.
 *
 * @param engine Handle returned from dase_create_engine
 */
DASE_API void dase_destroy_engine(DaseEngineHandle engine);

// =============================================================================
// HIGH-PERFORMANCE MISSION EXECUTION
// =============================================================================

/**
 * Run optimized mission with pre-computed input signals (ZERO-COPY).
 *
 * This is the high-performance version that eliminates the serial sin/cos
 * bottleneck present in the original runMission(). Instead of computing
 * sin/cos 5.475M times serially, the host language (Julia) pre-computes
 * them in parallel and passes the arrays directly.
 *
 * Key optimizations:
 * - Zero-copy: Arrays are passed by pointer (no marshalling overhead)
 * - Parallel pre-computation: Julia/Rust computes sin/cos in parallel
 * - Single parallel region: Uses collapse(2) to eliminate 5.475M barriers
 * - Cache-optimized: Processes all nodes for each step (better locality)
 *
 * Expected performance:
 * - CPU utilization: ~90% (vs 12% with Python)
 * - Throughput: ~1.67 billion ops/sec (vs 234M with Python)
 * - Time per op: ~0.6 ns (vs 4.27 ns with Python)
 *
 * @param engine Handle to the engine
 * @param input_signals Array of pre-computed input signals (length: num_steps)
 *                      Typically sin(step * 0.01) for each step
 * @param control_patterns Array of pre-computed control patterns (length: num_steps)
 *                         Typically cos(step * 0.01) for each step
 * @param num_steps Number of mission steps (e.g., 5,475,000 for endurance test)
 * @param iterations_per_node Number of iterations to process per node (default: 30)
 */
DASE_API void dase_run_mission_optimized(
    DaseEngineHandle engine,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
);

/**
 * Run Phase 4B optimized mission with single parallel region.
 *
 * This version eliminates 54,750 OpenMP barriers by using a single parallel
 * region with manual work distribution instead of creating a new parallel
 * region for each step.
 *
 * Key Phase 4B improvements:
 * - Single parallel region (eliminates 54,750 barriers)
 * - Manual thread work distribution
 * - Better cache locality (each thread works on its node slice)
 * - Expected 20-30% improvement over Phase 4A
 *
 * @param engine Handle to the engine
 * @param input_signals Array of pre-computed input signals (length: num_steps)
 * @param control_patterns Array of pre-computed control patterns (length: num_steps)
 * @param num_steps Number of mission steps
 * @param iterations_per_node Number of iterations to process per node (default: 30)
 */
DASE_API void dase_run_mission_optimized_phase4b(
    DaseEngineHandle engine,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
);

/**
 * Run Phase 4C optimized mission with AVX2 spatial vectorization.
 *
 * This version processes 4 nodes in parallel using AVX2 SIMD instructions,
 * improving AVX2 utilization from ~9% to ~40-60%.
 *
 * Key Phase 4C improvements:
 * - Spatial vectorization (4 nodes processed in parallel)
 * - Full AVX2 intrinsics for arithmetic operations
 * - Retains Phase 4B's single parallel region
 * - Expected 50-100% improvement over Phase 4B
 *
 * @param engine Handle to the engine
 * @param input_signals Array of pre-computed input signals (length: num_steps)
 * @param control_patterns Array of pre-computed control patterns (length: num_steps)
 * @param num_steps Number of mission steps
 * @param iterations_per_node Number of iterations to process per node (default: 30)
 */
DASE_API void dase_run_mission_optimized_phase4c(
    DaseEngineHandle engine,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
);

// =============================================================================
// METRICS RETRIEVAL
// =============================================================================

/**
 * Get performance metrics from the last mission run.
 *
 * @param engine Handle to the engine
 * @param out_ns_per_op Output: Nanoseconds per operation
 * @param out_ops_per_sec Output: Operations per second
 * @param out_speedup_factor Output: Speedup vs 15,500ns baseline
 * @param out_total_ops Output: Total operations completed
 */
DASE_API void dase_get_metrics(
    DaseEngineHandle engine,
    double* out_ns_per_op,
    double* out_ops_per_sec,
    double* out_speedup_factor,
    uint64_t* out_total_ops
);

// =============================================================================
// CPU FEATURES
// =============================================================================

/**
 * Check if the CPU supports AVX2 instructions.
 *
 * @return 1 if AVX2 is supported, 0 otherwise
 */
DASE_API int dase_has_avx2(void);

/**
 * Check if the CPU supports FMA (Fused Multiply-Add) instructions.
 *
 * @return 1 if FMA is supported, 0 otherwise
 */
DASE_API int dase_has_fma(void);

#ifdef __cplusplus
}
#endif

#endif // DASE_CAPI_H
