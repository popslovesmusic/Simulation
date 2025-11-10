/**
 * Engine Manager Implementation
 * Manages lifecycle of DASE engines using dynamic DLL loading
 */

#include "engine_manager.h"
#include <chrono>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <stdexcept>
#include <iostream>
#include <cstdint>
#include <algorithm>

// Include IGSOA engine directly (header-only)
#include "../../src/cpp/igsoa_complex_engine.h"
#include "../../src/cpp/igsoa_complex_engine_2d.h"
#include "../../src/cpp/igsoa_complex_engine_3d.h"
#include "../../src/cpp/igsoa_state_init_2d.h"
#include "../../src/cpp/igsoa_state_init_3d.h"

// Include SATP+Higgs engines (header-only)
#include "../../src/cpp/satp_higgs_engine_1d.h"
#include "../../src/cpp/satp_higgs_physics_1d.h"
#include "../../src/cpp/satp_higgs_state_init_1d.h"
#include "../../src/cpp/satp_higgs_engine_2d.h"
#include "../../src/cpp/satp_higgs_physics_2d.h"
#include "../../src/cpp/satp_higgs_state_init_2d.h"
#include "../../src/cpp/satp_higgs_engine_3d.h"
#include "../../src/cpp/satp_higgs_physics_3d.h"
#include "../../src/cpp/satp_higgs_state_init_3d.h"

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

// Function pointer types for DASE API
typedef void* (*CreateEngineFunc)(uint32_t);
typedef void (*DestroyEngineFunc)(void*);
typedef void (*RunMissionFunc)(void*, const double*, const double*, uint64_t, uint32_t);
typedef void (*GetMetricsFunc)(void*, double*, double*, double*, uint64_t*);

// DLL handle and function pointers
static HMODULE dll_handle = nullptr;
static CreateEngineFunc dase_create_engine = nullptr;
static DestroyEngineFunc dase_destroy_engine = nullptr;
static RunMissionFunc dase_run_mission_optimized_phase4c = nullptr;
static GetMetricsFunc dase_get_metrics = nullptr;

// Load the DASE DLL and get function pointers
static bool loadDaseDLL() {
    if (dll_handle != nullptr) {
        return true; // Already loaded
    }

    // Try to load dase_engine_phase4b.dll
    dll_handle = LoadLibraryA("dase_engine_phase4b.dll");

    if (!dll_handle) {
        // Try fallback to dase_engine.dll
        dll_handle = LoadLibraryA("dase_engine.dll");
    }

    if (!dll_handle) {
        DWORD error = GetLastError();
        std::cerr << "LoadLibrary failed with error code: " << error << std::endl;
        return false;
    }

    // Get function pointers
    dase_create_engine = reinterpret_cast<CreateEngineFunc>(
        GetProcAddress(dll_handle, "dase_create_engine"));

    dase_destroy_engine = reinterpret_cast<DestroyEngineFunc>(
        GetProcAddress(dll_handle, "dase_destroy_engine"));

    // Try Phase 4C first, then Phase 4B, then generic optimized
    dase_run_mission_optimized_phase4c = reinterpret_cast<RunMissionFunc>(
        GetProcAddress(dll_handle, "dase_run_mission_optimized_phase4c"));

    if (!dase_run_mission_optimized_phase4c) {
        dase_run_mission_optimized_phase4c = reinterpret_cast<RunMissionFunc>(
            GetProcAddress(dll_handle, "dase_run_mission_optimized_phase4b"));
    }

    if (!dase_run_mission_optimized_phase4c) {
        dase_run_mission_optimized_phase4c = reinterpret_cast<RunMissionFunc>(
            GetProcAddress(dll_handle, "dase_run_mission_optimized"));
    }

    dase_get_metrics = reinterpret_cast<GetMetricsFunc>(
        GetProcAddress(dll_handle, "dase_get_metrics"));

    // Check if all functions were found
    if (!dase_create_engine) {
        std::cerr << "Failed to find dase_create_engine" << std::endl;
    }
    if (!dase_destroy_engine) {
        std::cerr << "Failed to find dase_destroy_engine" << std::endl;
    }
    if (!dase_run_mission_optimized_phase4c) {
        std::cerr << "Failed to find dase_run_mission_optimized_phase4c" << std::endl;
    }
    if (!dase_get_metrics) {
        std::cerr << "Failed to find dase_get_metrics" << std::endl;
    }

    if (!dase_create_engine || !dase_destroy_engine ||
        !dase_run_mission_optimized_phase4c || !dase_get_metrics) {
        FreeLibrary(dll_handle);
        dll_handle = nullptr;
        return false;
    }

    return true;
}

EngineManager::EngineManager() : next_engine_id(1) {
    // Load the DLL on construction
    if (!loadDaseDLL()) {
        throw std::runtime_error("Failed to load DASE engine DLL (dase_engine_phase4b.dll or dase_engine.dll)");
    }
}

EngineManager::~EngineManager() {
    // Skip cleanup to avoid FFTW/DLL unload ordering issues
    // Memory will be reclaimed by OS on process exit
    // TODO: Fix FFTW wisdom cleanup order for long-running services

    // Note: For short-lived CLI processes, this is acceptable
    // For long-running services, proper cleanup would be needed
}

std::string EngineManager::createEngine(const std::string& engine_type,
                                        int num_nodes,
                                        double R_c,
                                        double kappa,
                                        double gamma,
                                        double dt,
                                        int N_x,
                                        int N_y,
                                        int N_z) {
    // Validate parameters
    if (num_nodes <= 0 || num_nodes > 1048576) {
        return "";
    }

    // Create engine instance
    auto instance = std::make_unique<EngineInstance>();
    instance->engine_id = generateEngineId();
    instance->engine_type = engine_type;
    instance->num_nodes = num_nodes;
    instance->created_timestamp = getCurrentTimestamp();
    instance->R_c = R_c;
    instance->kappa = kappa;
    instance->gamma = gamma;
    instance->dt = dt;
    instance->dimension_x = N_x;
    instance->dimension_y = N_y;
    instance->dimension_z = N_z;

    void* handle = nullptr;

    if (engine_type == "phase4b") {
        // Phase 4B - load from DLL
        if (!dase_create_engine) {
            return "";
        }
        handle = dase_create_engine(static_cast<uint32_t>(num_nodes));

    } else if (engine_type == "igsoa_complex") {
        // IGSOA Complex - create directly
        try {
            dase::igsoa::IGSOAComplexConfig config;
            config.num_nodes = num_nodes;
            config.R_c_default = R_c;
            config.kappa = kappa;
            config.gamma = gamma;
            config.dt = dt;

            // DIAGNOSTIC: Print config being used
            std::cerr << "[ENGINE MANAGER] Creating IGSOA engine with R_c=" << R_c
                      << " (config.R_c_default=" << config.R_c_default << ")" << std::endl;

            auto* engine = new dase::igsoa::IGSOAComplexEngine(config);
            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else if (engine_type == "igsoa_complex_2d") {
        // IGSOA Complex - 2D extension
        if (N_x <= 0 || N_y <= 0) {
            return "";
        }

        // If num_nodes doesn't match N_x * N_y, adjust to prevent inconsistency
        int64_t expected_nodes = static_cast<int64_t>(N_x) * static_cast<int64_t>(N_y);
        if (expected_nodes <= 0 || expected_nodes > 1048576) {
            return "";
        }

        instance->num_nodes = static_cast<int>(expected_nodes);

        try {
            dase::igsoa::IGSOAComplexConfig config;
            config.num_nodes = static_cast<size_t>(expected_nodes);
            config.R_c_default = R_c;
            config.kappa = kappa;
            config.gamma = gamma;
            config.dt = dt;
            config.normalize_psi = false;

            auto* engine = new dase::igsoa::IGSOAComplexEngine2D(
                config,
                static_cast<size_t>(N_x),
                static_cast<size_t>(N_y)
            );

            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else if (engine_type == "igsoa_complex_3d") {
        if (N_x <= 0 || N_y <= 0 || N_z <= 0) {
            return "";
        }

        int64_t expected_nodes = static_cast<int64_t>(N_x) * static_cast<int64_t>(N_y) * static_cast<int64_t>(N_z);
        if (expected_nodes <= 0 || expected_nodes > 1048576) {
            return "";
        }

        instance->num_nodes = static_cast<int>(expected_nodes);

        try {
            dase::igsoa::IGSOAComplexConfig config;
            config.num_nodes = static_cast<size_t>(expected_nodes);
            config.R_c_default = R_c;
            config.kappa = kappa;
            config.gamma = gamma;
            config.dt = dt;
            config.normalize_psi = false;

            auto* engine = new dase::igsoa::IGSOAComplexEngine3D(
                config,
                static_cast<size_t>(N_x),
                static_cast<size_t>(N_y),
                static_cast<size_t>(N_z)
            );

            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else if (engine_type == "satp_higgs_1d") {
        // SATP+Higgs coupled field engine - 1D
        if (num_nodes <= 0) {
            return "";
        }

        try {
            // Create SATP+Higgs physics parameters
            dase::satp_higgs::SATPHiggsParams params;
            params.c = (R_c > 0.0) ? R_c : 1.0;  // Wave speed (reuse R_c parameter)
            params.gamma_phi = gamma;             // Scale field dissipation
            params.gamma_h = gamma;               // Higgs dissipation (same for now)
            params.lambda = kappa;                // φ-h coupling (reuse kappa parameter)
            params.mu_squared = -1.0;             // Higgs mass² (negative for SSB)
            params.lambda_h = 0.5;                // Higgs self-coupling
            params.updateVEV();                   // Compute VEV

            // Lattice parameters
            double dx = 0.1;  // Default spatial step (can be overridden via JSON)
            double dt_val = (dt > 0.0) ? dt : 0.001;  // Time step

            auto* engine = new dase::satp_higgs::SATPHiggsEngine1D(
                static_cast<size_t>(num_nodes),
                dx,
                dt_val,
                params
            );

            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else if (engine_type == "satp_higgs_2d") {
        // SATP+Higgs coupled field engine - 2D
        if (N_x <= 0 || N_y <= 0) {
            return "";
        }

        int64_t expected_nodes = static_cast<int64_t>(N_x) * static_cast<int64_t>(N_y);
        if (expected_nodes <= 0 || expected_nodes > 1048576) {
            return "";
        }

        instance->num_nodes = static_cast<int>(expected_nodes);

        try {
            // Create SATP+Higgs physics parameters
            dase::satp_higgs::SATPHiggsParams params;
            params.c = (R_c > 0.0) ? R_c : 1.0;
            params.gamma_phi = gamma;
            params.gamma_h = gamma;
            params.lambda = kappa;
            params.mu_squared = -1.0;
            params.lambda_h = 0.5;
            params.updateVEV();

            // Lattice parameters
            double dx = 0.1;
            double dt_val = (dt > 0.0) ? dt : 0.001;

            auto* engine = new dase::satp_higgs::SATPHiggsEngine2D(
                static_cast<size_t>(N_x),
                static_cast<size_t>(N_y),
                dx,
                dt_val,
                params
            );

            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else if (engine_type == "satp_higgs_3d") {
        // SATP+Higgs coupled field engine - 3D
        if (N_x <= 0 || N_y <= 0 || N_z <= 0) {
            return "";
        }

        int64_t expected_nodes = static_cast<int64_t>(N_x) * static_cast<int64_t>(N_y) * static_cast<int64_t>(N_z);
        if (expected_nodes <= 0 || expected_nodes > 1048576) {
            return "";
        }

        instance->num_nodes = static_cast<int>(expected_nodes);

        try {
            dase::satp_higgs::SATPHiggsParams params;
            params.c = (R_c > 0.0) ? R_c : 1.0;
            params.gamma_phi = gamma;
            params.gamma_h = gamma;
            params.lambda = kappa;
            params.mu_squared = -1.0;
            params.lambda_h = 0.5;
            params.updateVEV();

            double dx = 0.1;
            double dt_val = (dt > 0.0) ? dt : 0.001;

            auto* engine = new dase::satp_higgs::SATPHiggsEngine3D(
                static_cast<size_t>(N_x),
                static_cast<size_t>(N_y),
                static_cast<size_t>(N_z),
                dx,
                dt_val,
                params
            );

            handle = static_cast<void*>(engine);

        } catch (...) {
            return "";
        }

    } else {
        // Unknown engine type
        return "";
    }

    if (!handle) {
        return "";
    }

    instance->engine_handle = handle;

    std::string id = instance->engine_id;
    engines[id] = std::move(instance);

    return id;
}

bool EngineManager::destroyEngine(const std::string& engine_id) {
    auto it = engines.find(engine_id);
    if (it == engines.end()) {
        return false;
    }

    // Destroy engine based on type
    if (it->second->engine_handle) {
        if (it->second->engine_type == "phase4b" && dase_destroy_engine) {
            dase_destroy_engine(it->second->engine_handle);
        } else if (it->second->engine_type == "igsoa_complex") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(it->second->engine_handle);
            delete engine;
        } else if (it->second->engine_type == "igsoa_complex_2d") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(it->second->engine_handle);
            delete engine;
        } else if (it->second->engine_type == "igsoa_complex_3d") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(it->second->engine_handle);
            delete engine;
        } else if (it->second->engine_type == "satp_higgs_1d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine1D*>(it->second->engine_handle);
            delete engine;
        } else if (it->second->engine_type == "satp_higgs_2d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine2D*>(it->second->engine_handle);
            delete engine;
        } else if (it->second->engine_type == "satp_higgs_3d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine3D*>(it->second->engine_handle);
            delete engine;
        }
    }

    engines.erase(it);
    return true;
}

EngineInstance* EngineManager::getEngine(const std::string& engine_id) {
    auto it = engines.find(engine_id);
    if (it == engines.end()) {
        return nullptr;
    }
    return it->second.get();
}

std::vector<EngineInstance*> EngineManager::listEngines() {
    std::vector<EngineInstance*> result;
    for (auto& pair : engines) {
        result.push_back(pair.second.get());
    }
    return result;
}

bool EngineManager::setNodeState(const std::string& engine_id, int node_index, double value) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    // Phase 4B doesn't expose individual node state setting in the C API
    // This would require extending the C API
    // For now, return success (no-op)
    return true;
}

double EngineManager::getNodeState(const std::string& engine_id, int node_index) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return 0.0;
    }

    // Phase 4B doesn't expose individual node state reading in the C API
    // This would require extending the C API
    // For now, return 0.0
    return 0.0;
}

bool EngineManager::runMission(const std::string& engine_id, int num_steps, int iterations_per_node) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (num_steps <= 0) {
        return false;
    }

    try {
        // Pre-compute input signals and control patterns
        std::vector<double> input_signals(num_steps);
        std::vector<double> control_patterns(num_steps);

        for (int i = 0; i < num_steps; i++) {
            input_signals[i] = std::sin(i * 0.01);
            control_patterns[i] = std::cos(i * 0.01);
        }

        if (instance->engine_type == "phase4b") {
            // Phase 4B - call DLL
            if (!dase_run_mission_optimized_phase4c || iterations_per_node <= 0) {
                return false;
            }

            dase_run_mission_optimized_phase4c(
                instance->engine_handle,
                input_signals.data(),
                control_patterns.data(),
                static_cast<uint64_t>(num_steps),
                static_cast<uint32_t>(iterations_per_node)
            );

        } else if (instance->engine_type == "igsoa_complex") {
            // IGSOA Complex - call directly
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
            engine->runMission(
                num_steps,
                input_signals.data(),
                control_patterns.data()
            );

        } else if (instance->engine_type == "igsoa_complex_2d") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
            engine->runMission(
                num_steps,
                input_signals.data(),
                control_patterns.data()
            );

        } else if (instance->engine_type == "igsoa_complex_3d") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
            engine->runMission(
                num_steps,
                input_signals.data(),
                control_patterns.data()
            );

        } else if (instance->engine_type == "satp_higgs_1d") {
            // SATP+Higgs engine - use evolve() method
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine1D*>(instance->engine_handle);
            engine->evolve(static_cast<size_t>(num_steps));

        } else if (instance->engine_type == "satp_higgs_2d") {
            // SATP+Higgs 2D engine
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine2D*>(instance->engine_handle);
            engine->evolve(static_cast<size_t>(num_steps));

        } else if (instance->engine_type == "satp_higgs_3d") {
            // SATP+Higgs 3D engine
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine3D*>(instance->engine_handle);
            engine->evolve(static_cast<size_t>(num_steps));

        } else {
            return false;
        }

        return true;

    } catch (...) {
        return false;
    }
}

bool EngineManager::setNodePsi(const std::string& engine_id, int node_index, double real, double imag) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type == "igsoa_complex") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }
        engine->setNodePsi(static_cast<size_t>(node_index), real, imag);
        return true;

    } else if (instance->engine_type == "igsoa_complex_2d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }

        size_t x = 0;
        size_t y = 0;
        engine->indexToCoord(static_cast<size_t>(node_index), x, y);
        engine->setNodePsi(x, y, real, imag);
        return true;

    } else if (instance->engine_type == "igsoa_complex_3d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }

        size_t x = 0;
        size_t y = 0;
        size_t z = 0;
        engine->indexToCoord(static_cast<size_t>(node_index), x, y, z);
        engine->setNodePsi(x, y, z, real, imag);
        return true;
    }

    return false;
}

bool EngineManager::getNodePsi(const std::string& engine_id, int node_index, double& real_out, double& imag_out) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type == "igsoa_complex") {
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
        engine->getNodePsi(static_cast<size_t>(node_index), real_out, imag_out);
        return true;

    } else if (instance->engine_type == "igsoa_complex_2d") {
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
        size_t x = 0;
        size_t y = 0;
        engine->indexToCoord(static_cast<size_t>(node_index), x, y);
        engine->getNodePsi(x, y, real_out, imag_out);
        return true;

    } else if (instance->engine_type == "igsoa_complex_3d") {
        if (node_index < 0 || node_index >= instance->num_nodes) {
            return false;
        }
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
        size_t x = 0;
        size_t y = 0;
        size_t z = 0;
        engine->indexToCoord(static_cast<size_t>(node_index), x, y, z);
        engine->getNodePsi(x, y, z, real_out, imag_out);
        return true;
    }

    return false;
}

bool EngineManager::getAllNodeStates(const std::string& engine_id,
                                      std::vector<double>& psi_real,
                                      std::vector<double>& psi_imag,
                                      std::vector<double>& phi) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type == "igsoa_complex") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        psi_real.resize(num_nodes);
        psi_imag.resize(num_nodes);
        phi.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            psi_real[i] = nodes[i].psi.real();
            psi_imag[i] = nodes[i].psi.imag();
            phi[i] = nodes[i].phi;
        }

        return true;

    } else if (instance->engine_type == "igsoa_complex_2d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        psi_real.resize(num_nodes);
        psi_imag.resize(num_nodes);
        phi.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            psi_real[i] = nodes[i].psi.real();
            psi_imag[i] = nodes[i].psi.imag();
            phi[i] = nodes[i].phi;
        }

        return true;

    } else if (instance->engine_type == "igsoa_complex_3d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        psi_real.resize(num_nodes);
        psi_imag.resize(num_nodes);
        phi.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            psi_real[i] = nodes[i].psi.real();
            psi_imag[i] = nodes[i].psi.imag();
            phi[i] = nodes[i].phi;
        }

        return true;
    }

    return false;
}

bool EngineManager::getSatpState(const std::string& engine_id,
                                  std::vector<double>& phi_out,
                                  std::vector<double>& phi_dot_out,
                                  std::vector<double>& h_out,
                                  std::vector<double>& h_dot_out) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type == "satp_higgs_1d") {
        auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine1D*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        phi_out.resize(num_nodes);
        phi_dot_out.resize(num_nodes);
        h_out.resize(num_nodes);
        h_dot_out.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            phi_out[i] = nodes[i].phi;
            phi_dot_out[i] = nodes[i].phi_dot;
            h_out[i] = nodes[i].h;
            h_dot_out[i] = nodes[i].h_dot;
        }

        return true;

    } else if (instance->engine_type == "satp_higgs_2d") {
        auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine2D*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        phi_out.resize(num_nodes);
        phi_dot_out.resize(num_nodes);
        h_out.resize(num_nodes);
        h_dot_out.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            phi_out[i] = nodes[i].phi;
            phi_dot_out[i] = nodes[i].phi_dot;
            h_out[i] = nodes[i].h;
            h_dot_out[i] = nodes[i].h_dot;
        }

        return true;

    } else if (instance->engine_type == "satp_higgs_3d") {
        auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine3D*>(instance->engine_handle);
        const auto& nodes = engine->getNodes();

        size_t num_nodes = nodes.size();
        phi_out.resize(num_nodes);
        phi_dot_out.resize(num_nodes);
        h_out.resize(num_nodes);
        h_dot_out.resize(num_nodes);

        for (size_t i = 0; i < num_nodes; i++) {
            phi_out[i] = nodes[i].phi;
            phi_dot_out[i] = nodes[i].phi_dot;
            h_out[i] = nodes[i].h;
            h_dot_out[i] = nodes[i].h_dot;
        }

        return true;
    }

    return false;
}

bool EngineManager::setIgsoaState(const std::string& engine_id,
                                   const std::string& profile_type,
                                   const nlohmann::json& params) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    try {
        if (instance->engine_type == "igsoa_complex") {
            auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
            size_t num_nodes = instance->num_nodes;

            if (profile_type == "gaussian") {
            // Extract Gaussian profile parameters
            double amplitude = params.value("amplitude", 1.0);
            int center_node = params.value("center_node", num_nodes / 2);
            double width = params.value("width", num_nodes / 16.0);
            double baseline_phi = params.value("baseline_phi", 0.0);

            // Extract mode parameter (default: "overwrite" for backwards compatibility)
            std::string mode = params.value("mode", "overwrite");

            // Apply Gaussian profile based on mode
            if (mode == "overwrite") {
                // MODE: OVERWRITE - Replace entire field with baseline + gaussian
                for (size_t i = 0; i < num_nodes; i++) {
                    double distance = static_cast<double>(i) - static_cast<double>(center_node);
                    double gaussian_value = amplitude * std::exp(-(distance * distance) / (2.0 * width * width));

                    // Set Ψ (complex quantum state) - using Gaussian magnitude with zero phase
                    engine->setNodePsi(i, gaussian_value, 0.0);

                    // Set Φ (realized field) to baseline
                    engine->setNodePhi(i, baseline_phi);
                }

            } else if (mode == "add") {
                // MODE: ADD - Add gaussian on top of existing field values (φ = φ + G)
                for (size_t i = 0; i < num_nodes; i++) {
                    double distance = static_cast<double>(i) - static_cast<double>(center_node);
                    double gaussian_value = amplitude * std::exp(-(distance * distance) / (2.0 * width * width));

                    // Add to Ψ (complex quantum state)
                    const auto& node = engine->getNodes()[i];
                    double psi_real = node.psi.real() + gaussian_value;
                    double psi_imag = node.psi.imag();
                    engine->setNodePsi(i, psi_real, psi_imag);

                    // Add gaussian to Φ (realized field)
                    double phi_current = node.phi;
                    engine->setNodePhi(i, phi_current + gaussian_value);
                }

            } else if (mode == "blend") {
                // MODE: BLEND - Blend toward gaussian target: φ = (1-beta)φ + beta(baseline + G)
                double beta = params.value("beta", 0.1);  // Default blend factor 0.1

                for (size_t i = 0; i < num_nodes; i++) {
                    double distance = static_cast<double>(i) - static_cast<double>(center_node);
                    double gaussian_value = amplitude * std::exp(-(distance * distance) / (2.0 * width * width));

                    // Blend Ψ toward target
                    const auto& node = engine->getNodes()[i];
                    double target_psi_real = gaussian_value;
                    double target_psi_imag = 0.0;
                    double blended_psi_real = (1.0 - beta) * node.psi.real() + beta * target_psi_real;
                    double blended_psi_imag = (1.0 - beta) * node.psi.imag() + beta * target_psi_imag;
                    engine->setNodePsi(i, blended_psi_real, blended_psi_imag);

                    // Blend Φ toward baseline + gaussian
                    double target_phi = baseline_phi + gaussian_value;
                    double blended_phi = (1.0 - beta) * node.phi + beta * target_phi;
                    engine->setNodePhi(i, blended_phi);
                }

            } else {
                // Unknown mode - fail
                return false;
            }

            return true;

        } else if (profile_type == "uniform") {
            // Extract uniform profile parameters
            double psi_real = params.value("psi_real", 0.1);
            double psi_imag = params.value("psi_imag", 0.0);
            double phi = params.value("phi", 0.0);

            // Apply uniform state to all nodes
            for (size_t i = 0; i < num_nodes; i++) {
                engine->setNodePsi(i, psi_real, psi_imag);
                engine->setNodePhi(i, phi);
            }

            return true;

        } else if (profile_type == "localized") {
            // Extract localized profile parameters
            int node_index = params.value("node_index", 0);
            double psi_real = params.value("psi_real", 1.0);
            double psi_imag = params.value("psi_imag", 0.0);
            double phi = params.value("phi", 0.0);

            // Zero out all nodes first
            for (size_t i = 0; i < num_nodes; i++) {
                engine->setNodePsi(i, 0.0, 0.0);
                engine->setNodePhi(i, 0.0);
            }

            // Set single node
            if (node_index >= 0 && node_index < static_cast<int>(num_nodes)) {
                engine->setNodePsi(node_index, psi_real, psi_imag);
                engine->setNodePhi(node_index, phi);
            }

            return true;

        } else {
            // Unsupported profile type
            return false;
        }

        } else if (instance->engine_type == "igsoa_complex_2d") {
            auto* engine2d = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
            size_t N_x = instance->dimension_x > 0 ? static_cast<size_t>(instance->dimension_x) : engine2d->getNx();
            size_t N_y = instance->dimension_y > 0 ? static_cast<size_t>(instance->dimension_y) : engine2d->getNy();

            if (profile_type == "gaussian" || profile_type == "gaussian_2d") {
                dase::igsoa::Gaussian2DParams gparams;
                gparams.amplitude = params.value("amplitude", 1.0);
                gparams.center_x = params.value("center_x", static_cast<double>(N_x) / 2.0);
                gparams.center_y = params.value("center_y", static_cast<double>(N_y) / 2.0);
                double default_sigma_x = (std::max)(1.0, static_cast<double>(N_x) / 16.0);
                double default_sigma_y = (std::max)(1.0, static_cast<double>(N_y) / 16.0);
                gparams.sigma_x = params.value("sigma_x", default_sigma_x);
                gparams.sigma_y = params.value("sigma_y", default_sigma_y);
                gparams.baseline_phi = params.value("baseline_phi", 0.0);
                gparams.mode = params.value("mode", std::string("overwrite"));
                gparams.beta = params.value("beta", 1.0);

                dase::igsoa::IGSOAStateInit2D::initGaussian2D(*engine2d, gparams);
                return true;

            } else if (profile_type == "circular_gaussian" || profile_type == "circular_gaussian_2d") {
                double amplitude = params.value("amplitude", 1.0);
                double center_x = params.value("center_x", static_cast<double>(N_x) / 2.0);
                double center_y = params.value("center_y", static_cast<double>(N_y) / 2.0);
                double min_dim = (std::min)(static_cast<double>(N_x), static_cast<double>(N_y));
                double default_sigma = (std::max)(1.0, min_dim / 16.0);
                double sigma = params.value("sigma", default_sigma);
                double baseline_phi = params.value("baseline_phi", 0.0);
                std::string mode = params.value("mode", std::string("overwrite"));
                double beta = params.value("beta", 1.0);

                dase::igsoa::IGSOAStateInit2D::initCircularGaussian(
                    *engine2d,
                    amplitude,
                    center_x,
                    center_y,
                    sigma,
                    baseline_phi,
                    mode,
                    beta
                );

                return true;

            } else if (profile_type == "plane_wave_2d" || profile_type == "plane_wave") {
                dase::igsoa::PlaneWave2DParams wave_params;
                wave_params.amplitude = params.value("amplitude", 1.0);
                wave_params.k_x = params.value("k_x", 2.0 * M_PI / std::max<double>(1.0, N_x));
                wave_params.k_y = params.value("k_y", 2.0 * M_PI / std::max<double>(1.0, N_y));
                wave_params.phase_offset = params.value("phase_offset", 0.0);

                dase::igsoa::IGSOAStateInit2D::initPlaneWave2D(*engine2d, wave_params);
                return true;

            } else if (profile_type == "uniform") {
                double psi_real = params.value("psi_real", 0.1);
                double psi_imag = params.value("psi_imag", 0.0);
                double phi = params.value("phi", 0.0);

                dase::igsoa::IGSOAStateInit2D::initUniform(*engine2d, psi_real, psi_imag, phi);
                return true;

            } else if (profile_type == "random" || profile_type == "random_2d") {
                double amplitude = params.value("amplitude", 1.0);
                unsigned int seed = params.value("seed", 0u);

                dase::igsoa::IGSOAStateInit2D::initRandom(*engine2d, amplitude, seed);
                return true;

            } else if (profile_type == "reset") {
                engine2d->reset();
                return true;

            } else {
                return false;
            }

        } else if (instance->engine_type == "igsoa_complex_3d") {
            auto* engine3d = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
            size_t N_x = instance->dimension_x > 0 ? static_cast<size_t>(instance->dimension_x) : engine3d->getNx();
            size_t N_y = instance->dimension_y > 0 ? static_cast<size_t>(instance->dimension_y) : engine3d->getNy();
            size_t N_z = instance->dimension_z > 0 ? static_cast<size_t>(instance->dimension_z) : engine3d->getNz();

            if (profile_type == "gaussian" || profile_type == "gaussian_3d") {
                dase::igsoa::Gaussian3DParams params3d;
                params3d.amplitude = params.value("amplitude", 1.0);
                params3d.center_x = params.value("center_x", static_cast<double>(N_x) / 2.0);
                params3d.center_y = params.value("center_y", static_cast<double>(N_y) / 2.0);
                params3d.center_z = params.value("center_z", static_cast<double>(N_z) / 2.0);
                double default_sigma_x = (std::max)(1.0, static_cast<double>(N_x) / 16.0);
                double default_sigma_y = (std::max)(1.0, static_cast<double>(N_y) / 16.0);
                double default_sigma_z = (std::max)(1.0, static_cast<double>(N_z) / 16.0);
                params3d.sigma_x = params.value("sigma_x", default_sigma_x);
                params3d.sigma_y = params.value("sigma_y", default_sigma_y);
                params3d.sigma_z = params.value("sigma_z", default_sigma_z);
                params3d.baseline_phi = params.value("baseline_phi", 0.0);
                params3d.mode = params.value("mode", std::string("overwrite"));
                params3d.beta = params.value("beta", 1.0);

                dase::igsoa::IGSOAStateInit3D::initGaussian3D(*engine3d, params3d);
                return true;

            } else if (profile_type == "spherical_gaussian" || profile_type == "gaussian_spherical") {
                double amplitude = params.value("amplitude", 1.0);
                double center_x = params.value("center_x", static_cast<double>(N_x) / 2.0);
                double center_y = params.value("center_y", static_cast<double>(N_y) / 2.0);
                double center_z = params.value("center_z", static_cast<double>(N_z) / 2.0);
                size_t min_dim = (std::min)((std::min)(N_x, N_y), N_z);
                double default_sigma = (std::max)(1.0, static_cast<double>(min_dim) / 16.0);
                double sigma = params.value("sigma", default_sigma);
                double baseline_phi = params.value("baseline_phi", 0.0);
                std::string mode = params.value("mode", std::string("overwrite"));
                double beta = params.value("beta", 1.0);

                dase::igsoa::IGSOAStateInit3D::initSphericalGaussian(
                    *engine3d,
                    amplitude,
                    center_x,
                    center_y,
                    center_z,
                    sigma,
                    baseline_phi,
                    mode,
                    beta
                );
                return true;

            } else if (profile_type == "plane_wave_3d" || profile_type == "plane_wave") {
                dase::igsoa::PlaneWave3DParams wave_params;
                wave_params.amplitude = params.value("amplitude", 1.0);
                wave_params.k_x = params.value("k_x", 2.0 * M_PI / std::max<double>(1.0, N_x));
                wave_params.k_y = params.value("k_y", 2.0 * M_PI / std::max<double>(1.0, N_y));
                wave_params.k_z = params.value("k_z", 2.0 * M_PI / std::max<double>(1.0, N_z));
                wave_params.phase_offset = params.value("phase_offset", 0.0);

                dase::igsoa::IGSOAStateInit3D::initPlaneWave3D(*engine3d, wave_params);
                return true;

            } else if (profile_type == "uniform") {
                double psi_real = params.value("psi_real", 0.1);
                double psi_imag = params.value("psi_imag", 0.0);
                double phi = params.value("phi", 0.0);

                dase::igsoa::IGSOAStateInit3D::initUniform(*engine3d, psi_real, psi_imag, phi);
                return true;

            } else if (profile_type == "random" || profile_type == "random_3d") {
                double amplitude = params.value("amplitude", 1.0);
                unsigned int seed = params.value("seed", 0u);

                dase::igsoa::IGSOAStateInit3D::initRandom(*engine3d, amplitude, seed);
                return true;

            } else if (profile_type == "reset") {
                engine3d->reset();
                return true;

            } else {
                return false;
            }

        } else {
            return false;
        }

    } catch (...) {
        return false;
    }
}

bool EngineManager::setSatpState(const std::string& engine_id,
                                  const std::string& profile_type,
                                  const nlohmann::json& params) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    try {
        if (instance->engine_type == "satp_higgs_1d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine1D*>(instance->engine_handle);

            if (profile_type == "vacuum") {
                // Initialize to Higgs vacuum (VEV)
                dase::satp_higgs::SATPHiggsStateInit1D::initVacuum(*engine);
                return true;

            } else if (profile_type == "phi_gaussian") {
                // Gaussian profile for φ field
                dase::satp_higgs::GaussianProfileParams gparams;
                gparams.amplitude = params.value("amplitude", 1.0);
                gparams.center = params.value("center", static_cast<double>(engine->getN()) * engine->getDx() / 2.0);
                gparams.sigma = params.value("sigma", static_cast<double>(engine->getN()) * engine->getDx() / 16.0);
                gparams.set_velocity = params.value("set_velocity", false);
                gparams.velocity_amplitude = params.value("velocity_amplitude", 0.0);
                gparams.mode = params.value("mode", "overwrite");
                gparams.beta = params.value("beta", 1.0);

                dase::satp_higgs::SATPHiggsStateInit1D::initPhiGaussian(*engine, gparams);
                return true;

            } else if (profile_type == "higgs_gaussian") {
                // Gaussian perturbation for h field around VEV
                dase::satp_higgs::GaussianProfileParams gparams;
                gparams.amplitude = params.value("amplitude", 0.1);
                gparams.center = params.value("center", static_cast<double>(engine->getN()) * engine->getDx() / 2.0);
                gparams.sigma = params.value("sigma", static_cast<double>(engine->getN()) * engine->getDx() / 16.0);
                gparams.set_velocity = params.value("set_velocity", false);
                gparams.velocity_amplitude = params.value("velocity_amplitude", 0.0);
                gparams.mode = params.value("mode", "overwrite");
                gparams.beta = params.value("beta", 1.0);

                dase::satp_higgs::SATPHiggsStateInit1D::initHiggsGaussian(*engine, gparams);
                return true;

            } else if (profile_type == "three_zone_source") {
                // Set up three-zone source function
                dase::satp_higgs::ThreeZoneSourceParams sparams;
                sparams.zone1_start = params.value("zone1_start", 0.0);
                sparams.zone1_end = params.value("zone1_end", 0.0);
                sparams.zone2_start = params.value("zone2_start", 0.0);
                sparams.zone2_end = params.value("zone2_end", 0.0);
                sparams.zone3_start = params.value("zone3_start", 0.0);
                sparams.zone3_end = params.value("zone3_end", 0.0);
                sparams.amplitude1 = params.value("amplitude1", 0.0);
                sparams.amplitude2 = params.value("amplitude2", 0.0);
                sparams.amplitude3 = params.value("amplitude3", 0.0);
                sparams.frequency = params.value("frequency", 0.0);
                sparams.t_start = params.value("t_start", 0.0);
                sparams.t_end = params.value("t_end", -1.0);

                auto source_func = dase::satp_higgs::SATPHiggsStateInit1D::createThreeZoneSource(
                    sparams, engine->getDx());
                engine->setSource(source_func);
                return true;

            } else if (profile_type == "uniform") {
                // Uniform initialization
                double phi_val = params.value("phi", 0.0);
                double phi_dot_val = params.value("phi_dot", 0.0);
                double h_val = params.value("h", engine->getParams().h_vev);
                double h_dot_val = params.value("h_dot", 0.0);

                dase::satp_higgs::SATPHiggsStateInit1D::initUniform(*engine,
                    phi_val, phi_dot_val, h_val, h_dot_val);
                return true;

            } else if (profile_type == "random_perturbation") {
                // Add random perturbations
                double phi_amplitude = params.value("phi_amplitude", 0.01);
                double h_amplitude = params.value("h_amplitude", 0.01);
                unsigned int seed = params.value("seed", 0);

                dase::satp_higgs::SATPHiggsStateInit1D::addRandomPerturbation(*engine,
                    phi_amplitude, h_amplitude, seed);
                return true;

            } else {
                return false;  // Unknown profile type
            }

        } else if (instance->engine_type == "satp_higgs_2d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine2D*>(instance->engine_handle);

            if (profile_type == "vacuum") {
                // Initialize to Higgs vacuum (VEV)
                dase::satp_higgs::SATPHiggsStateInit2D::initVacuum(*engine);
                return true;

            } else if (profile_type == "phi_circular_gaussian") {
                // Circular Gaussian profile for φ field
                double amplitude = params.value("amplitude", 1.0);
                double center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                double center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                double sigma = params.value("sigma", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                std::string mode = params.value("mode", "overwrite");

                dase::satp_higgs::SATPHiggsStateInit2D::initPhiCircularGaussian(
                    *engine, amplitude, center_x, center_y, sigma, mode);
                return true;

            } else if (profile_type == "phi_gaussian") {
                // Elliptical Gaussian profile for φ field
                dase::satp_higgs::GaussianProfile2DParams gparams;
                gparams.amplitude = params.value("amplitude", 1.0);
                gparams.center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                gparams.center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                gparams.sigma_x = params.value("sigma_x", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                gparams.sigma_y = params.value("sigma_y", static_cast<double>(engine->getNy()) * engine->getDx() / 16.0);
                gparams.set_velocity = params.value("set_velocity", false);
                gparams.velocity_amplitude = params.value("velocity_amplitude", 0.0);
                gparams.mode = params.value("mode", "overwrite");
                gparams.beta = params.value("beta", 1.0);

                dase::satp_higgs::SATPHiggsStateInit2D::initPhiGaussian(*engine, gparams);
                return true;

            } else if (profile_type == "higgs_circular_gaussian") {
                // Circular Gaussian perturbation for h field around VEV
                double amplitude = params.value("amplitude", 0.1);
                double center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                double center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                double sigma = params.value("sigma", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                std::string mode = params.value("mode", "overwrite");

                dase::satp_higgs::SATPHiggsStateInit2D::initHiggsCircularGaussian(
                    *engine, amplitude, center_x, center_y, sigma, mode);
                return true;

            } else if (profile_type == "uniform") {
                // Uniform initialization
                double phi_val = params.value("phi", 0.0);
                double phi_dot_val = params.value("phi_dot", 0.0);
                double h_val = params.value("h", engine->getParams().h_vev);
                double h_dot_val = params.value("h_dot", 0.0);

                dase::satp_higgs::SATPHiggsStateInit2D::initUniform(*engine,
                    phi_val, phi_dot_val, h_val, h_dot_val);
                return true;

            } else if (profile_type == "random_perturbation") {
                // Add random perturbations
                double phi_amplitude = params.value("phi_amplitude", 0.01);
                double h_amplitude = params.value("h_amplitude", 0.01);
                unsigned int seed = params.value("seed", 0);

                dase::satp_higgs::SATPHiggsStateInit2D::addRandomPerturbation(*engine,
                    phi_amplitude, h_amplitude, seed);
                return true;

            } else {
                return false;  // Unknown profile type
            }

        } else if (instance->engine_type == "satp_higgs_3d") {
            auto* engine = static_cast<dase::satp_higgs::SATPHiggsEngine3D*>(instance->engine_handle);

            if (profile_type == "vacuum") {
                // Initialize to Higgs vacuum (VEV)
                dase::satp_higgs::SATPHiggsStateInit3D::initVacuum(*engine);
                return true;

            } else if (profile_type == "phi_spherical_gaussian") {
                // Spherical Gaussian profile for φ field
                double amplitude = params.value("amplitude", 1.0);
                double center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                double center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                double center_z = params.value("center_z", static_cast<double>(engine->getNz()) * engine->getDx() / 2.0);
                double sigma = params.value("sigma", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                std::string mode = params.value("mode", "overwrite");

                dase::satp_higgs::SATPHiggsStateInit3D::initPhiSphericalGaussian(
                    *engine, amplitude, center_x, center_y, center_z, sigma, mode);
                return true;

            } else if (profile_type == "phi_gaussian") {
                // Ellipsoidal Gaussian profile for φ field
                dase::satp_higgs::GaussianProfile3DParams gparams;
                gparams.amplitude = params.value("amplitude", 1.0);
                gparams.center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                gparams.center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                gparams.center_z = params.value("center_z", static_cast<double>(engine->getNz()) * engine->getDx() / 2.0);
                gparams.sigma_x = params.value("sigma_x", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                gparams.sigma_y = params.value("sigma_y", static_cast<double>(engine->getNy()) * engine->getDx() / 16.0);
                gparams.sigma_z = params.value("sigma_z", static_cast<double>(engine->getNz()) * engine->getDx() / 16.0);
                gparams.set_velocity = params.value("set_velocity", false);
                gparams.velocity_amplitude = params.value("velocity_amplitude", 0.0);
                gparams.mode = params.value("mode", "overwrite");
                gparams.beta = params.value("beta", 1.0);

                dase::satp_higgs::SATPHiggsStateInit3D::initPhiGaussian(*engine, gparams);
                return true;

            } else if (profile_type == "higgs_spherical_gaussian") {
                // Spherical Gaussian perturbation for h field around VEV
                double amplitude = params.value("amplitude", 0.1);
                double center_x = params.value("center_x", static_cast<double>(engine->getNx()) * engine->getDx() / 2.0);
                double center_y = params.value("center_y", static_cast<double>(engine->getNy()) * engine->getDx() / 2.0);
                double center_z = params.value("center_z", static_cast<double>(engine->getNz()) * engine->getDx() / 2.0);
                double sigma = params.value("sigma", static_cast<double>(engine->getNx()) * engine->getDx() / 16.0);
                std::string mode = params.value("mode", "overwrite");

                dase::satp_higgs::SATPHiggsStateInit3D::initHiggsSphericalGaussian(
                    *engine, amplitude, center_x, center_y, center_z, sigma, mode);
                return true;

            } else if (profile_type == "uniform") {
                // Uniform initialization
                double phi_val = params.value("phi", 0.0);
                double phi_dot_val = params.value("phi_dot", 0.0);
                double h_val = params.value("h", engine->getParams().h_vev);
                double h_dot_val = params.value("h_dot", 0.0);

                dase::satp_higgs::SATPHiggsStateInit3D::initUniform(*engine,
                    phi_val, phi_dot_val, h_val, h_dot_val);
                return true;

            } else if (profile_type == "random_perturbation") {
                // Add random perturbations
                double phi_amplitude = params.value("phi_amplitude", 0.01);
                double h_amplitude = params.value("h_amplitude", 0.01);
                unsigned int seed = params.value("seed", 0);

                dase::satp_higgs::SATPHiggsStateInit3D::addRandomPerturbation(*engine,
                    phi_amplitude, h_amplitude, seed);
                return true;

            } else {
                return false;  // Unknown profile type
            }

        } else {
            return false;  // Wrong engine type
        }

    } catch (...) {
        return false;
    }
}

bool EngineManager::computeCenterOfMass2D(const std::string& engine_id,
                                          double& x_cm_out,
                                          double& y_cm_out) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type != "igsoa_complex_2d") {
        return false;
    }

    auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
    dase::igsoa::IGSOAStateInit2D::computeCenterOfMass(*engine, x_cm_out, y_cm_out);
    return true;
}

bool EngineManager::computeCenterOfMass3D(const std::string& engine_id,
                                          double& x_cm_out,
                                          double& y_cm_out,
                                          double& z_cm_out) {
    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return false;
    }

    if (instance->engine_type != "igsoa_complex_3d") {
        return false;
    }

    auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
    dase::igsoa::IGSOAStateInit3D::computeCenterOfMass(*engine, x_cm_out, y_cm_out, z_cm_out);
    return true;
}

EngineManager::EngineMetrics EngineManager::getMetrics(const std::string& engine_id) {
    EngineMetrics metrics;
    metrics.ns_per_op = 0;
    metrics.ops_per_sec = 0;
    metrics.total_operations = 0;
    metrics.speedup_factor = 0;

    auto* instance = getEngine(engine_id);
    if (!instance || !instance->engine_handle) {
        return metrics;
    }

    if (instance->engine_type == "phase4b") {
        // Phase 4B - get from DLL
        if (!dase_get_metrics) {
            return metrics;
        }

        dase_get_metrics(
            instance->engine_handle,
            &metrics.ns_per_op,
            &metrics.ops_per_sec,
            &metrics.speedup_factor,
            &metrics.total_operations
        );

    } else if (instance->engine_type == "igsoa_complex") {
        // IGSOA Complex - get directly
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine*>(instance->engine_handle);
        engine->getMetrics(
            metrics.ns_per_op,
            metrics.ops_per_sec,
            metrics.speedup_factor,
            metrics.total_operations
        );

    } else if (instance->engine_type == "igsoa_complex_2d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine2D*>(instance->engine_handle);
        engine->getMetrics(
            metrics.ns_per_op,
            metrics.ops_per_sec,
            metrics.speedup_factor,
            metrics.total_operations
        );
    } else if (instance->engine_type == "igsoa_complex_3d") {
        auto* engine = static_cast<dase::igsoa::IGSOAComplexEngine3D*>(instance->engine_handle);
        engine->getMetrics(
            metrics.ns_per_op,
            metrics.ops_per_sec,
            metrics.speedup_factor,
            metrics.total_operations
        );
    }

    return metrics;
}

std::string EngineManager::generateEngineId() {
    // Thread-safe engine ID generation using atomic fetch_add
    int id = next_engine_id.fetch_add(1, std::memory_order_relaxed);
    std::ostringstream oss;
    oss << "engine_" << std::setw(3) << std::setfill('0') << id;
    return oss.str();
}

double EngineManager::getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto duration = now.time_since_epoch();
    auto millis = std::chrono::duration_cast<std::chrono::milliseconds>(duration).count();
    return static_cast<double>(millis) / 1000.0;
}
