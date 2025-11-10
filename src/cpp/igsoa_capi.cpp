/**
 * IGSOA Complex Engine C API Implementation
 */

#include "igsoa_capi.h"
#include "igsoa_complex_engine.h"
#include <memory>

using namespace dase::igsoa;

// Opaque struct wrapping the C++ engine
struct IGSOAComplexEngine_C {
    std::unique_ptr<IGSOAComplexEngine> engine;
};

extern "C" {

IGSOA_API IGSOAEngineHandle igsoa_create_engine(
    uint32_t num_nodes,
    double R_c,
    double kappa,
    double gamma,
    double dt
) {
    try {
        IGSOAComplexConfig config;
        config.num_nodes = num_nodes;
        config.R_c_default = R_c;
        config.kappa = kappa;
        config.gamma = gamma;
        config.dt = dt;

        auto wrapper = new IGSOAComplexEngine_C();
        wrapper->engine = std::make_unique<IGSOAComplexEngine>(config);

        return wrapper;

    } catch (...) {
        return nullptr;
    }
}

IGSOA_API void igsoa_destroy_engine(IGSOAEngineHandle engine) {
    if (engine) {
        delete engine;
    }
}

IGSOA_API void igsoa_set_node_psi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double psi_real,
    double psi_imag
) {
    if (engine && engine->engine) {
        engine->engine->setNodePsi(node_index, psi_real, psi_imag);
    }
}

IGSOA_API void igsoa_get_node_psi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double* out_psi_real,
    double* out_psi_imag
) {
    if (engine && engine->engine && out_psi_real && out_psi_imag) {
        engine->engine->getNodePsi(node_index, *out_psi_real, *out_psi_imag);
    }
}

IGSOA_API void igsoa_set_node_phi(
    IGSOAEngineHandle engine,
    uint32_t node_index,
    double phi
) {
    if (engine && engine->engine) {
        engine->engine->setNodePhi(node_index, phi);
    }
}

IGSOA_API double igsoa_get_node_phi(
    IGSOAEngineHandle engine,
    uint32_t node_index
) {
    if (engine && engine->engine) {
        return engine->engine->getNodePhi(node_index);
    }
    return 0.0;
}

IGSOA_API double igsoa_get_node_F(
    IGSOAEngineHandle engine,
    uint32_t node_index
) {
    if (engine && engine->engine) {
        return engine->engine->getNodeF(node_index);
    }
    return 0.0;
}

IGSOA_API void igsoa_run_mission(
    IGSOAEngineHandle engine,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps
) {
    if (engine && engine->engine) {
        engine->engine->runMission(num_steps, input_signals, control_patterns);
    }
}

IGSOA_API void igsoa_get_metrics(
    IGSOAEngineHandle engine,
    double* out_ns_per_op,
    double* out_ops_per_sec,
    double* out_speedup_factor,
    uint64_t* out_total_ops
) {
    if (engine && engine->engine) {
        engine->engine->getMetrics(
            *out_ns_per_op,
            *out_ops_per_sec,
            *out_speedup_factor,
            *out_total_ops
        );
    }
}

IGSOA_API double igsoa_get_total_energy(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return engine->engine->getTotalEnergy();
    }
    return 0.0;
}

IGSOA_API double igsoa_get_total_entropy_rate(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return engine->engine->getTotalEntropyRate();
    }
    return 0.0;
}

IGSOA_API double igsoa_get_average_F(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return engine->engine->getAverageInformationalDensity();
    }
    return 0.0;
}

IGSOA_API double igsoa_get_average_phase(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return engine->engine->getAveragePhase();
    }
    return 0.0;
}

IGSOA_API void igsoa_reset_engine(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        engine->engine->reset();
    }
}

IGSOA_API uint32_t igsoa_get_num_nodes(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return static_cast<uint32_t>(engine->engine->getNumNodes());
    }
    return 0;
}

IGSOA_API double igsoa_get_current_time(IGSOAEngineHandle engine) {
    if (engine && engine->engine) {
        return engine->engine->getCurrentTime();
    }
    return 0.0;
}

} // extern "C"
