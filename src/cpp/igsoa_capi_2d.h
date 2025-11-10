/**
 * IGSOA C API - 2D Engine Interface
 *
 * C-compatible API for interfacing with the 2D IGSOA engine from CLI/Python/other languages.
 * Follows the same pattern as the 1D C API (igsoa_capi.h).
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

// Opaque handle to 2D engine instance
typedef void* IGSOA2DEngineHandle;

/**
 * Create a 2D IGSOA engine
 *
 * @param N_x Number of nodes in x-direction
 * @param N_y Number of nodes in y-direction
 * @param R_c Causal radius (default coupling range)
 * @param kappa Coupling strength (default: 1.0)
 * @param gamma Dissipation rate (default: 0.1)
 * @param dt Time step (default: 0.01)
 * @return Handle to engine instance (NULL on failure)
 */
IGSOA2DEngineHandle igsoa2d_create_engine(
    size_t N_x,
    size_t N_y,
    double R_c,
    double kappa,
    double gamma,
    double dt
);

/**
 * Destroy a 2D IGSOA engine
 *
 * @param handle Engine handle
 */
void igsoa2d_destroy_engine(IGSOA2DEngineHandle handle);

/**
 * Get lattice dimensions
 *
 * @param handle Engine handle
 * @param N_x_out Output: number of nodes in x-direction
 * @param N_y_out Output: number of nodes in y-direction
 */
void igsoa2d_get_dimensions(
    IGSOA2DEngineHandle handle,
    size_t* N_x_out,
    size_t* N_y_out
);

/**
 * Get total number of nodes
 *
 * @param handle Engine handle
 * @return Total nodes (N_x * N_y)
 */
size_t igsoa2d_get_total_nodes(IGSOA2DEngineHandle handle);

/**
 * Set quantum state for a specific node
 *
 * @param handle Engine handle
 * @param x X-coordinate
 * @param y Y-coordinate
 * @param psi_real Real part of Ψ
 * @param psi_imag Imaginary part of Ψ
 */
void igsoa2d_set_node_psi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double psi_real,
    double psi_imag
);

/**
 * Get quantum state for a specific node
 *
 * @param handle Engine handle
 * @param x X-coordinate
 * @param y Y-coordinate
 * @param psi_real_out Output: real part of Ψ
 * @param psi_imag_out Output: imaginary part of Ψ
 */
void igsoa2d_get_node_psi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double* psi_real_out,
    double* psi_imag_out
);

/**
 * Set realized field for a specific node
 *
 * @param handle Engine handle
 * @param x X-coordinate
 * @param y Y-coordinate
 * @param phi Φ value
 */
void igsoa2d_set_node_phi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double phi
);

/**
 * Get realized field for a specific node
 *
 * @param handle Engine handle
 * @param x X-coordinate
 * @param y Y-coordinate
 * @return Φ value
 */
double igsoa2d_get_node_phi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y
);

/**
 * Run time evolution mission
 *
 * @param handle Engine handle
 * @param num_steps Number of time steps
 * @return true on success
 */
bool igsoa2d_run_mission(
    IGSOA2DEngineHandle handle,
    uint64_t num_steps
);

/**
 * Get performance metrics
 *
 * @param handle Engine handle
 * @param ns_per_op_out Output: nanoseconds per operation
 * @param ops_per_sec_out Output: operations per second
 * @param speedup_out Output: speedup factor vs baseline
 * @param total_ops_out Output: total operations completed
 */
void igsoa2d_get_metrics(
    IGSOA2DEngineHandle handle,
    double* ns_per_op_out,
    double* ops_per_sec_out,
    double* speedup_out,
    uint64_t* total_ops_out
);

/**
 * Extract full state (all nodes)
 *
 * @param handle Engine handle
 * @param psi_real_out Output array: real parts of Ψ (size: N_x*N_y)
 * @param psi_imag_out Output array: imaginary parts of Ψ (size: N_x*N_y)
 * @param phi_out Output array: Φ values (size: N_x*N_y)
 * @return true on success
 *
 * NOTE: Caller must allocate arrays with size N_x*N_y before calling.
 * Data is returned in row-major order: index = y*N_x + x
 */
bool igsoa2d_get_all_states(
    IGSOA2DEngineHandle handle,
    double* psi_real_out,
    double* psi_imag_out,
    double* phi_out
);

/**
 * Initialize 2D circular Gaussian profile
 *
 * @param handle Engine handle
 * @param amplitude Peak amplitude
 * @param center_x X-coordinate of center
 * @param center_y Y-coordinate of center
 * @param sigma Gaussian width (isotropic)
 * @param baseline_phi Background Φ value
 * @param mode "overwrite", "add", or "blend"
 * @param beta Blend factor (0-1) for "blend" mode
 * @return true on success
 */
bool igsoa2d_init_circular_gaussian(
    IGSOA2DEngineHandle handle,
    double amplitude,
    double center_x,
    double center_y,
    double sigma,
    double baseline_phi,
    const char* mode,
    double beta
);

/**
 * Initialize 2D elliptical Gaussian profile
 *
 * @param handle Engine handle
 * @param amplitude Peak amplitude
 * @param center_x X-coordinate of center
 * @param center_y Y-coordinate of center
 * @param sigma_x Gaussian width in x-direction
 * @param sigma_y Gaussian width in y-direction
 * @param baseline_phi Background Φ value
 * @param mode "overwrite", "add", or "blend"
 * @param beta Blend factor (0-1) for "blend" mode
 * @return true on success
 */
bool igsoa2d_init_gaussian(
    IGSOA2DEngineHandle handle,
    double amplitude,
    double center_x,
    double center_y,
    double sigma_x,
    double sigma_y,
    double baseline_phi,
    const char* mode,
    double beta
);

/**
 * Compute center of mass of |Ψ|² distribution
 *
 * @param handle Engine handle
 * @param x_cm_out Output: X-coordinate of center of mass
 * @param y_cm_out Output: Y-coordinate of center of mass
 * @return true on success
 */
bool igsoa2d_compute_center_of_mass(
    IGSOA2DEngineHandle handle,
    double* x_cm_out,
    double* y_cm_out
);

/**
 * Reset engine to initial state
 *
 * @param handle Engine handle
 */
void igsoa2d_reset(IGSOA2DEngineHandle handle);

/**
 * Get total system energy
 *
 * @param handle Engine handle
 * @return Total energy E = ∑[|Ψ|² + Φ²]
 */
double igsoa2d_get_total_energy(IGSOA2DEngineHandle handle);

/**
 * Get total entropy production rate
 *
 * @param handle Engine handle
 * @return Total entropy rate Ṡ_total
 */
double igsoa2d_get_entropy_rate(IGSOA2DEngineHandle handle);

#ifdef __cplusplus
}
#endif
