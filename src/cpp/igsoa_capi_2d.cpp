/**
 * IGSOA C API Implementation - 2D Engine
 */

#include "igsoa_capi_2d.h"
#include "igsoa_complex_engine_2d.h"
#include "igsoa_state_init_2d.h"
#include <cstring>
#include <string>

using namespace dase::igsoa;

// Create 2D engine
IGSOA2DEngineHandle igsoa2d_create_engine(
    size_t N_x,
    size_t N_y,
    double R_c,
    double kappa,
    double gamma,
    double dt
) {
    try {
        // Create configuration
        IGSOAComplexConfig config;
        config.num_nodes = N_x * N_y;  // Total nodes
        config.R_c_default = R_c;
        config.kappa = kappa;
        config.gamma = gamma;
        config.dt = dt;
        config.normalize_psi = false;  // Preserve amplitude for SATP validation

        // Create engine
        auto* engine = new IGSOAComplexEngine2D(config, N_x, N_y);
        return static_cast<IGSOA2DEngineHandle>(engine);
    } catch (...) {
        return nullptr;
    }
}

// Destroy engine
void igsoa2d_destroy_engine(IGSOA2DEngineHandle handle) {
    if (handle) {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
        delete engine;
    }
}

// Get dimensions
void igsoa2d_get_dimensions(
    IGSOA2DEngineHandle handle,
    size_t* N_x_out,
    size_t* N_y_out
) {
    if (!handle || !N_x_out || !N_y_out) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    *N_x_out = engine->getNx();
    *N_y_out = engine->getNy();
}

// Get total nodes
size_t igsoa2d_get_total_nodes(IGSOA2DEngineHandle handle) {
    if (!handle) return 0;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    return engine->getTotalNodes();
}

// Set node Ψ
void igsoa2d_set_node_psi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double psi_real,
    double psi_imag
) {
    if (!handle) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    engine->setNodePsi(x, y, psi_real, psi_imag);
}

// Get node Ψ
void igsoa2d_get_node_psi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double* psi_real_out,
    double* psi_imag_out
) {
    if (!handle || !psi_real_out || !psi_imag_out) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    engine->getNodePsi(x, y, *psi_real_out, *psi_imag_out);
}

// Set node Φ
void igsoa2d_set_node_phi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y,
    double phi
) {
    if (!handle) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    engine->setNodePhi(x, y, phi);
}

// Get node Φ
double igsoa2d_get_node_phi(
    IGSOA2DEngineHandle handle,
    size_t x,
    size_t y
) {
    if (!handle) return 0.0;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    return engine->getNodePhi(x, y);
}

// Run mission
bool igsoa2d_run_mission(
    IGSOA2DEngineHandle handle,
    uint64_t num_steps
) {
    if (!handle) return false;
    try {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
        engine->runMission(num_steps);
        return true;
    } catch (...) {
        return false;
    }
}

// Get metrics
void igsoa2d_get_metrics(
    IGSOA2DEngineHandle handle,
    double* ns_per_op_out,
    double* ops_per_sec_out,
    double* speedup_out,
    uint64_t* total_ops_out
) {
    if (!handle) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    engine->getMetrics(*ns_per_op_out, *ops_per_sec_out, *speedup_out, *total_ops_out);
}

// Get all states
bool igsoa2d_get_all_states(
    IGSOA2DEngineHandle handle,
    double* psi_real_out,
    double* psi_imag_out,
    double* phi_out
) {
    if (!handle || !psi_real_out || !psi_imag_out || !phi_out) return false;

    try {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
        const auto& nodes = engine->getNodes();

        size_t N_total = engine->getTotalNodes();
        for (size_t i = 0; i < N_total; i++) {
            psi_real_out[i] = nodes[i].psi.real();
            psi_imag_out[i] = nodes[i].psi.imag();
            phi_out[i] = nodes[i].phi;
        }

        return true;
    } catch (...) {
        return false;
    }
}

// Initialize circular Gaussian
bool igsoa2d_init_circular_gaussian(
    IGSOA2DEngineHandle handle,
    double amplitude,
    double center_x,
    double center_y,
    double sigma,
    double baseline_phi,
    const char* mode,
    double beta
) {
    if (!handle || !mode) return false;

    try {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
        std::string mode_str(mode);

        IGSOAStateInit2D::initCircularGaussian(
            *engine,
            amplitude,
            center_x,
            center_y,
            sigma,
            baseline_phi,
            mode_str,
            beta
        );

        return true;
    } catch (...) {
        return false;
    }
}

// Initialize elliptical Gaussian
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
) {
    if (!handle || !mode) return false;

    try {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);

        Gaussian2DParams params;
        params.amplitude = amplitude;
        params.center_x = center_x;
        params.center_y = center_y;
        params.sigma_x = sigma_x;
        params.sigma_y = sigma_y;
        params.baseline_phi = baseline_phi;
        params.mode = std::string(mode);
        params.beta = beta;

        IGSOAStateInit2D::initGaussian2D(*engine, params);

        return true;
    } catch (...) {
        return false;
    }
}

// Compute center of mass
bool igsoa2d_compute_center_of_mass(
    IGSOA2DEngineHandle handle,
    double* x_cm_out,
    double* y_cm_out
) {
    if (!handle || !x_cm_out || !y_cm_out) return false;

    try {
        auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
        IGSOAStateInit2D::computeCenterOfMass(*engine, *x_cm_out, *y_cm_out);
        return true;
    } catch (...) {
        return false;
    }
}

// Reset engine
void igsoa2d_reset(IGSOA2DEngineHandle handle) {
    if (!handle) return;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    engine->reset();
}

// Get total energy
double igsoa2d_get_total_energy(IGSOA2DEngineHandle handle) {
    if (!handle) return 0.0;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    return engine->getTotalEnergy();
}

// Get entropy rate
double igsoa2d_get_entropy_rate(IGSOA2DEngineHandle handle) {
    if (!handle) return 0.0;
    auto* engine = static_cast<IGSOAComplexEngine2D*>(handle);
    return engine->getTotalEntropyRate();
}
