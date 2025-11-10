/**
 * Engine Manager - Manages lifecycle of DASE engines
 * Handles both Phase 4B (real) and IGSOA Complex (complex) engines
 */

#pragma once

#include <string>
#include <map>
#include <memory>
#include <vector>
#include <atomic>
#include "json.hpp"

// Engine instance wrapper
struct EngineInstance {
    std::string engine_id;
    std::string engine_type; // "phase4b", "igsoa_complex", or IGSOA lattice variants
    void* engine_handle;      // Opaque handle to DLL engine
    int num_nodes;
    double created_timestamp;
    int dimension_x;
    int dimension_y;
    int dimension_z;
    double R_c;
    double kappa;
    double gamma;
    double dt;

    EngineInstance()
        : engine_handle(nullptr)
        , num_nodes(0)
        , created_timestamp(0)
        , dimension_x(0)
        , dimension_y(0)
        , dimension_z(0)
        , R_c(1.0)
        , kappa(1.0)
        , gamma(0.1)
        , dt(0.01) {}
};

class EngineManager {
public:
    EngineManager();
    ~EngineManager();

    // Engine lifecycle
    std::string createEngine(const std::string& engine_type,
                             int num_nodes,
                             double R_c = 1.0,
                             double kappa = 1.0,
                             double gamma = 0.1,
                             double dt = 0.01,
                             int N_x = 0,
                             int N_y = 0,
                             int N_z = 0);
    bool destroyEngine(const std::string& engine_id);
    EngineInstance* getEngine(const std::string& engine_id);

    // List all engines
    std::vector<EngineInstance*> listEngines();

    // Engine operations (Phase 4B)
    bool setNodeState(const std::string& engine_id, int node_index, double value);
    double getNodeState(const std::string& engine_id, int node_index);
    bool runMission(const std::string& engine_id, int num_steps, int iterations_per_node);

    // Engine operations (IGSOA Complex)
    bool setNodePsi(const std::string& engine_id, int node_index, double real, double imag);
    bool getNodePsi(const std::string& engine_id, int node_index, double& real_out, double& imag_out);

    // Bulk state extraction (for spectral analysis)
    bool getAllNodeStates(const std::string& engine_id,
                          std::vector<double>& psi_real,
                          std::vector<double>& psi_imag,
                          std::vector<double>& phi);

    // Bulk state extraction (for SATP+Higgs engines)
    bool getSatpState(const std::string& engine_id,
                      std::vector<double>& phi_out,
                      std::vector<double>& phi_dot_out,
                      std::vector<double>& h_out,
                      std::vector<double>& h_dot_out);

    // Bulk state initialization (for IGSOA engines)
    bool setIgsoaState(const std::string& engine_id,
                       const std::string& profile_type,
                       const nlohmann::json& params);

    // Bulk state initialization (for SATP+Higgs engines)
    bool setSatpState(const std::string& engine_id,
                      const std::string& profile_type,
                      const nlohmann::json& params);

    // 2D analysis helpers
    bool computeCenterOfMass2D(const std::string& engine_id,
                               double& x_cm_out,
                               double& y_cm_out);
    bool computeCenterOfMass3D(const std::string& engine_id,
                               double& x_cm_out,
                               double& y_cm_out,
                               double& z_cm_out);

    // Metrics
    struct EngineMetrics {
        double ns_per_op;
        double ops_per_sec;
        uint64_t total_operations;
        double speedup_factor;
    };

    EngineMetrics getMetrics(const std::string& engine_id);

private:
    std::map<std::string, std::unique_ptr<EngineInstance>> engines;
    std::atomic<int> next_engine_id;

    std::string generateEngineId();
    double getCurrentTimestamp();
};
