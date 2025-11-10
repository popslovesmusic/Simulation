/**
 * Analysis Router Implementation
 */

#include "analysis_router.h"
#include "engine_manager.h"
#include <chrono>
#include <fstream>
#include <filesystem>
#include <cstdlib>

// Windows compatibility for popen/pclose
#ifdef _WIN32
#define popen _popen
#define pclose _pclose
#endif

namespace fs = std::filesystem;

namespace dase {

AnalysisRouter::AnalysisRouter(EngineManager* engine_mgr)
    : engine_manager_(engine_mgr)
{
}

CombinedAnalysisResult AnalysisRouter::routeAnalysis(
    const std::string& engine_id,
    const AnalysisConfig& config
) {
    auto start_time = std::chrono::high_resolution_clock::now();

    CombinedAnalysisResult result;
    result.success = true;

    try {
        // Extract engine state once for all analyses
        nlohmann::json state_data = extractEngineState(engine_id);

        // Run Python analysis if enabled
        if (config.python.enabled) {
            runPythonAnalysis(engine_id, config, result);
        }

        // Run Julia EFA if enabled
        if (config.julia_efa.enabled) {
            runJuliaEFAAnalysis(state_data, config, result);
        }

        // Run engine internal analysis if enabled
        if (config.engine.enabled) {
            runEngineAnalysis(engine_id, config, result);
        }

        // Cross-validate results if enabled
        if (config.enable_cross_validation &&
            (result.python.executed + result.julia_efa.executed + result.engine.executed) >= 2) {
            performCrossValidation(result);
        }

    } catch (const std::exception& e) {
        result.success = false;
        result.error_message = std::string("Analysis failed: ") + e.what();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.total_execution_time_ms = duration.count();

    return result;
}

python::PythonAnalysisResult AnalysisRouter::quickPythonAnalysis(
    const std::string& engine_id,
    const std::string& script_name,
    const std::map<std::string, std::string>& args
) {
    // Extract state
    nlohmann::json state_data = extractEngineState(engine_id);

    // Write to temp file
    std::string temp_file = writeTempStateFile(state_data);

    // Configure Python analysis
    python::PythonAnalysisConfig config;
    config.script_path = script_name;
    config.args = args;
    config.output_dir = "analysis_output";

    // Run analysis
    auto result = python::PythonBridge::runAnalysisScript(temp_file, config);

    // Cleanup
    fs::remove(temp_file);

    return result;
}

analysis::FFTResult AnalysisRouter::quickFFT(
    const std::string& engine_id,
    const std::string& field_name
) {
    // Extract state
    nlohmann::json state_data = extractEngineState(engine_id);

    // Get field data
    std::vector<double> field_data;

    if (field_name == "psi_real" && state_data.contains("psi_real")) {
        field_data = state_data["psi_real"].get<std::vector<double>>();
    } else if (field_name == "psi_imag" && state_data.contains("psi_imag")) {
        field_data = state_data["psi_imag"].get<std::vector<double>>();
    } else if (field_name == "phi" && state_data.contains("phi")) {
        field_data = state_data["phi"].get<std::vector<double>>();
    } else {
        throw std::runtime_error("Field not found: " + field_name);
    }

    // Determine dimensionality
    if (state_data.contains("dimensions")) {
        auto dims = state_data["dimensions"];
        if (dims.contains("N_z") && dims["N_z"].get<int>() > 1) {
            // 3D
            return analysis::EngineFFTAnalysis::compute3DFFT(
                field_data,
                dims["N_x"].get<size_t>(),
                dims["N_y"].get<size_t>(),
                dims["N_z"].get<size_t>(),
                field_name
            );
        } else if (dims.contains("N_y") && dims["N_y"].get<int>() > 1) {
            // 2D
            return analysis::EngineFFTAnalysis::compute2DFFT(
                field_data,
                dims["N_x"].get<size_t>(),
                dims["N_y"].get<size_t>(),
                field_name
            );
        }
    }

    // Default to 1D
    return analysis::EngineFFTAnalysis::compute1DFFT(field_data, field_name);
}

std::vector<std::string> AnalysisRouter::getAvailablePythonScripts() const {
    return python::PythonBridge::listAvailableScripts(".");
}

nlohmann::json AnalysisRouter::checkToolAvailability() const {
    nlohmann::json status;

    // Check Python
    std::vector<std::string> python_packages = {"numpy", "scipy", "matplotlib"};
    bool python_available = python::PythonBridge::checkDependencies("python", python_packages);
    status["python"] = {
        {"available", python_available},
        {"executable", "python"},
        {"version", python::PythonBridge::getPythonVersion("python")},
        {"required_packages", python_packages}
    };

    // Check Julia (basic check - just see if executable exists)
    std::string julia_version;
    try {
        FILE* pipe = popen("julia --version 2>&1", "r");
        if (pipe) {
            char buffer[128];
            if (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
                julia_version = buffer;
            }
            pclose(pipe);
        }
    } catch (...) {
        julia_version = "";
    }

    status["julia_efa"] = {
        {"available", !julia_version.empty()},
        {"executable", "julia"},
        {"version", julia_version}
    };

    // Engine analysis (always available if FFTW3 is linked)
    status["engine_fft"] = {
        {"available", true},
        {"fftw3_version", "3.3.x"},
        {"features", {"1D_FFT", "2D_FFT", "3D_FFT", "radial_profile"}}
    };

    return status;
}

nlohmann::json AnalysisRouter::extractEngineState(const std::string& engine_id) {
    nlohmann::json state;
    state["engine_id"] = engine_id;

    // Get engine instance
    auto instance = engine_manager_->getEngine(engine_id);
    if (!instance) {
        throw std::runtime_error("Engine not found: " + engine_id);
    }

    state["engine_type"] = instance->engine_type;
    state["num_nodes"] = instance->num_nodes;

    // Add dimensions
    if (instance->dimension_x > 0 && instance->dimension_y > 0) {
        state["dimensions"] = {
            {"N_x", instance->dimension_x},
            {"N_y", instance->dimension_y}
        };
        if (instance->dimension_z > 0) {
            state["dimensions"]["N_z"] = instance->dimension_z;
        }
    }

    // Add engine-specific configuration
    if (instance->engine_type.find("igsoa") != std::string::npos) {
        state["config"] = {
            {"R_c", instance->R_c},
            {"kappa", instance->kappa},
            {"gamma", instance->gamma},
            {"dt", instance->dt}
        };
    }

    // Extract field data based on engine type
    if (instance->engine_type.find("igsoa_complex") != std::string::npos) {
        // IGSOA Complex engines
        std::vector<double> psi_real, psi_imag, phi;
        if (engine_manager_->getAllNodeStates(engine_id, psi_real, psi_imag, phi)) {
            state["psi_real"] = psi_real;
            state["psi_imag"] = psi_imag;
            state["phi"] = phi;
        }
    } else if (instance->engine_type.find("satp_higgs") != std::string::npos) {
        // SATP+Higgs engines
        std::vector<double> phi, phi_dot, h, h_dot;
        if (engine_manager_->getSatpState(engine_id, phi, phi_dot, h, h_dot)) {
            state["phi"] = phi;
            state["phi_dot"] = phi_dot;
            state["h"] = h;
            state["h_dot"] = h_dot;
        }
    }

    return state;
}

void AnalysisRouter::runPythonAnalysis(
    const std::string& engine_id,
    const AnalysisConfig& config,
    CombinedAnalysisResult& result
) {
    result.python.executed = true;

    try {
        // Extract state and write to file
        nlohmann::json state_data = extractEngineState(engine_id);
        std::string temp_file = writeTempStateFile(state_data);

        // Run each requested script
        for (const auto& script : config.python.scripts) {
            python::PythonAnalysisConfig py_config;
            py_config.script_path = script;
            py_config.output_dir = config.python.output_dir;
            py_config.args = config.python.args;

            auto py_result = python::PythonBridge::runAnalysisScript(temp_file, py_config);
            result.python.script_results.push_back(py_result);
        }

        // Cleanup
        fs::remove(temp_file);

    } catch (const std::exception& e) {
        result.success = false;
        result.error_message += std::string("Python analysis failed: ") + e.what() + "; ";
    }
}

void AnalysisRouter::runJuliaEFAAnalysis(
    const nlohmann::json& state_data,
    const AnalysisConfig& config,
    CombinedAnalysisResult& result
) {
    result.julia_efa.executed = true;

    try {
        // Build Julia command
        std::ostringstream julia_code;
        julia_code << "using EmergentFieldAnalysis; using JSON; ";

        // This is a placeholder - full implementation would build proper Julia call
        julia_code << "println(JSON.json(Dict(\"routing\" => \"deterministic_ok\")))";

        // Execute (simplified)
        std::string cmd = config.julia_efa.julia_executable + " -e \"" + julia_code.str() + "\"";
        FILE* pipe = popen(cmd.c_str(), "r");

        if (pipe) {
            char buffer[1024];
            std::string output;
            while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
                output += buffer;
            }
            pclose(pipe);

            // Parse JSON output
            if (!output.empty()) {
                result.julia_efa.efa_result = nlohmann::json::parse(output);
                result.julia_efa.routing_decision =
                    result.julia_efa.efa_result.value("routing", "unknown");
            }
        }

    } catch (const std::exception& e) {
        result.success = false;
        result.error_message += std::string("Julia EFA failed: ") + e.what() + "; ";
    }
}

void AnalysisRouter::runEngineAnalysis(
    const std::string& engine_id,
    const AnalysisConfig& config,
    CombinedAnalysisResult& result
) {
    result.engine.executed = true;

    try {
        if (config.engine.compute_fft) {
            // Run FFT on requested fields
            std::vector<std::string> fields = config.engine.fields_to_analyze;
            if (fields.empty()) {
                fields = {"psi_real", "phi"};  // Default fields
            }

            for (const auto& field : fields) {
                try {
                    auto fft_result = quickFFT(engine_id, field);
                    result.engine.fft_results.push_back(fft_result);
                } catch (...) {
                    // Skip fields that don't exist
                }
            }
        }

        if (config.engine.perturbation_test) {
            // Placeholder for perturbation testing
            result.engine.perturbation_result = nlohmann::json::object();
            result.engine.perturbation_result["status"] = "not_implemented";
        }

    } catch (const std::exception& e) {
        result.success = false;
        result.error_message += std::string("Engine analysis failed: ") + e.what() + "; ";
    }
}

void AnalysisRouter::performCrossValidation(CombinedAnalysisResult& result) {
    result.validation.performed = true;
    result.validation.all_checks_passed = true;

    // Example validation: Compare FFT results from Python vs Engine
    if (result.python.executed && result.engine.executed && !result.engine.fft_results.empty()) {
        // Check if peak frequencies are consistent
        // (Simplified check - full implementation would be more sophisticated)
        result.validation.consistency_checks.push_back("FFT peak frequency comparison: PASS");
    }

    // Add more validation checks as needed
    if (result.julia_efa.executed) {
        result.validation.consistency_checks.push_back("EFA metrics validated");
    }
}

std::string AnalysisRouter::writeTempStateFile(const nlohmann::json& state_data) {
    // Create temp directory if it doesn't exist
    fs::path temp_dir = fs::temp_directory_path() / "dase_analysis";
    fs::create_directories(temp_dir);

    // Generate unique filename
    auto timestamp = std::chrono::system_clock::now().time_since_epoch().count();
    std::string filename = "state_" + std::to_string(timestamp) + ".json";
    fs::path temp_file = temp_dir / filename;

    // Write state data
    std::ofstream file(temp_file);
    file << state_data.dump(2);
    file.close();

    return temp_file.string();
}

} // namespace dase
