/**
 * IGSOA Complex Engine C API
 *
 * C-compatible interface for the IGSOA Complex engine,
 * enabling integration with CLI, Julia, Python, and other languages.
 */

#ifndef IGSOA_CAPI_H
#define IGSOA_CAPI_H

#ifdef _WIN32
    #ifdef IGSOA_BUILD_DLL
        #define IGSOA_API __declspec(dllexport)
    #else
        #define IGSOA_API __declspec(dllimport)
    #endif
#else
    #define IGSOA_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

// =============================================================================
// OPAQUE ENGINE HANDLE
// =============================================================================

/**
 * Opaque pointer to the C++ IGSOAComplexEngine instance
 */
typedef struct IGSOAComplexEngine_C* IGSOAEngineHandle;

// =============================================================================
// ENGINE LIFECYCLE
// =============================================================================

/**
 * Create a new IGSOA Complex engine
 *
 * @param num_nodes Number of nodes in the network
 * @param R_c Causal resistance (default: 1e-34)
 * @param kappa Φ-Ψ coupling strength (default: 1.0)
 * @param gamma Dissipation coefficient (default: 0.1)
 * @param dt Time step (default: 0.01)
 * @return Handle to the engine (must be freed with igsoa_destroy_engine)
 */
IGSOA_API IGSOAEngineHandle igsoa_create_engine(
    uint32_t num_nodes,
    double R_c,
    double kappa,
    double gamma,
    double dt
);

/**
 * Destroy the engine and free all allocated memory
 *
 * @param engine Handle returned from igsoa_create_engine
 */
IGSOA_API void igsoa_destroy_engine(IGSOAEngineHandle engine);

// =============================================================================
// NODE STATE MANIPULATION
// =============================================================================

/**
 * Set quantum state for a specific node
 *
 * @param engine Engine handle
 * @param node_index Node index
 * @param psi_real Real part of Ψ
 * @param psi_imag Imaginary part of Ψ
 */
IGSOA_API void igsoa_set_node_psi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double psi_real,
    double psi_imag
);

/**
 * Get quantum state for a specific node
 *
 * @param engine Engine handle
 * @param node_index Node index
 * @param out_psi_real Output: real part of Ψ
 * @param out_psi_imag Output: imaginary part of Ψ
 */
IGSOA_API void igsoa_get_node_psi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double* out_psi_real,
    double* out_psi_imag
);

/**
 * Set realized field for a specific node
 *
 * @param engine Engine handle
 * @param node_index Node index
 * @param phi Φ value
 */
IGSOA_API void igsoa_set_node_phi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double phi
);

/**
 * Get realized field for a specific node
 *
 * @param engine Engine handle
 * @param node_index Node index
 * @return Φ value
 */
IGSOA_API double igsoa_get_node_phi(
    IGSOAEngineHandle engine,
    uint32_t node_index
);

/**
 * Get informational density for a specific node
 *
 * @param engine Engine handle
 * @param node_index Node index
 * @return F = |Ψ|²
 */
IGSOA_API double igsoa_get_node_F(
    IGSOAEngineHandle engine,
    uint32_t node_index
);

// =============================================================================
// MISSION EXECUTION
// =============================================================================

/**
 * Run mission with optional driving signals
 *
 * @param engine Engine handle
 * @param input_signals Array of input signals (length: num_steps), can be NULL
 * @param control_patterns Array of control patterns (length: num_steps), can be NULL
 * @param num_steps Number of time steps to execute
 */
IGSOA_API void igsoa_run_mission(
    IGSOAEngineHandle engine,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps
);

// =============================================================================
// METRICS RETRIEVAL
// =============================================================================

/**
 * Get performance metrics from the last mission run
 *
 * @param engine Engine handle
 * @param out_ns_per_op Output: Nanoseconds per operation
 * @param out_ops_per_sec Output: Operations per second
 * @param out_speedup_factor Output: Speedup vs 15,500ns baseline
 * @param out_total_ops Output: Total operations completed
 */
IGSOA_API void igsoa_get_metrics(
    IGSOAEngineHandle engine,
    double* out_ns_per_op,
    double* out_ops_per_sec,
    double* out_speedup_factor,
    uint64_t* out_total_ops
);

/**
 * Get total system energy
 *
 * @param engine Engine handle
 * @return E = ∑_i [|Ψ_i|² + Φ_i²]
 */
IGSOA_API double igsoa_get_total_energy(IGSOAEngineHandle engine);

/**
 * Get total entropy production rate
 *
 * @param engine Engine handle
 * @return Ṡ_total = ∑_i Ṡ_i
 */
IGSOA_API double igsoa_get_total_entropy_rate(IGSOAEngineHandle engine);

/**
 * Get average informational density
 *
 * @param engine Engine handle
 * @return <F> = (1/N) ∑_i |Ψ_i|²
 */
IGSOA_API double igsoa_get_average_F(IGSOAEngineHandle engine);

/**
 * Get average phase
 *
 * @param engine Engine handle
 * @return <θ> = (1/N) ∑_i arg(Ψ_i)
 */
IGSOA_API double igsoa_get_average_phase(IGSOAEngineHandle engine);

// =============================================================================
// ENGINE CONTROL
// =============================================================================

/**
 * Reset engine to initial state
 *
 * @param engine Engine handle
 */
IGSOA_API void igsoa_reset_engine(IGSOAEngineHandle engine);

/**
 * Get number of nodes in the engine
 *
 * @param engine Engine handle
 * @return Number of nodes
 */
IGSOA_API uint32_t igsoa_get_num_nodes(IGSOAEngineHandle engine);

/**
 * Get current simulation time
 *
 * @param engine Engine handle
 * @return Current time
 */
IGSOA_API double igsoa_get_current_time(IGSOAEngineHandle engine);

#ifdef __cplusplus
}
#endif

#endif // IGSOA_CAPI_H
