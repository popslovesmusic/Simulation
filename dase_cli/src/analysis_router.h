/**
 * Analysis Router - Unified interface for multi-tool analysis
 *
 * Coordinates analysis across three systems:
 * 1. Python tools (numpy, scipy, matplotlib)
 * 2. Julia EFA (Emergent Field Analysis)
 * 3. DASE engines (internal FFTW3, perturbation tests)
 */

#pragma once

#include <string>
#include <vector>
#include <memory>
#include "json.hpp"
#include "python_bridge.h"
#include "engine_fft_analysis.h"
#include "engine_manager.h"

namespace dase {

enum class AnalysisType {
    PYTHON_ONLY,
    JULIA_EFA_ONLY,
    ENGINE_ONLY,
    COMBINED_ALL
};

struct AnalysisConfig {
    AnalysisType type = AnalysisType::COMBINED_ALL;

    // Python configuration
    struct {
        bool enabled = false;
        std::vector<std::string> scripts;
        std::string output_dir = "python_analysis";
        std::map<std::string, std::string> args;
    } python;

    // Julia EFA configuration
    struct {
        bool enabled = false;
        std::string efa_project_path = "D:/Emergent-Field-Analysis";
        std::string julia_executable = "julia";
        std::string policy_path;
        std::string log_path;
    } julia_efa;

    // Engine analysis configuration
    struct {
        bool enabled = false;
        bool compute_fft = false;
        bool perturbation_test = false;
        std::vector<std::string> fields_to_analyze;  // Which fields to FFT
    } engine;

    // Cross-validation
    bool enable_cross_validation = true;
};

struct CombinedAnalysisResult {
    bool success = false;
    std::string error_message;
    double total_execution_time_ms = 0.0;

    // Python results
    struct {
        bool executed = false;
        std::vector<python::PythonAnalysisResult> script_results;
    } python;

    // Julia EFA results
    struct {
        bool executed = false;
        nlohmann::json efa_result;
        std::string routing_decision;  // "deterministic_ok" or "llm_review_needed"
    } julia_efa;

    // Engine analysis results
    struct {
        bool executed = false;
        std::vector<analysis::FFTResult> fft_results;
        nlohmann::json perturbation_result;
    } engine;

    // Cross-validation results
    struct {
        bool performed = false;
        std::vector<std::string> consistency_checks;
        bool all_checks_passed = true;
    } validation;
};

class AnalysisRouter {
public:
    AnalysisRouter(EngineManager* engine_mgr);

    /**
     * Route analysis request to appropriate tools
     *
     * @param engine_id Engine to analyze
     * @param config Analysis configuration
     * @return Combined results from all requested analyses
     */
    CombinedAnalysisResult routeAnalysis(
        const std::string& engine_id,
        const AnalysisConfig& config
    );

    /**
     * Quick analysis using Python tools only
     *
     * @param engine_id Engine to analyze
     * @param script_name Python script to run (e.g., "analyze_igsoa_state.py")
     * @param args Script arguments
     * @return Python analysis result
     */
    python::PythonAnalysisResult quickPythonAnalysis(
        const std::string& engine_id,
        const std::string& script_name,
        const std::map<std::string, std::string>& args
    );

    /**
     * Quick FFT using engine's internal FFTW3
     *
     * @param engine_id Engine to analyze
     * @param field_name Field to analyze (e.g., "psi_real", "phi")
     * @return FFT result
     */
    analysis::FFTResult quickFFT(
        const std::string& engine_id,
        const std::string& field_name
    );

    /**
     * Get available Python analysis scripts
     *
     * @return List of script paths
     */
    std::vector<std::string> getAvailablePythonScripts() const;

    /**
     * Check if all analysis tools are available
     *
     * @return JSON with tool availability status
     */
    nlohmann::json checkToolAvailability() const;

private:
    EngineManager* engine_manager_;

    // Extract engine state to JSON for analysis
    nlohmann::json extractEngineState(const std::string& engine_id);

    // Run Python analysis
    void runPythonAnalysis(
        const std::string& engine_id,
        const AnalysisConfig& config,
        CombinedAnalysisResult& result
    );

    // Run Julia EFA analysis
    void runJuliaEFAAnalysis(
        const nlohmann::json& state_data,
        const AnalysisConfig& config,
        CombinedAnalysisResult& result
    );

    // Run engine internal analysis
    void runEngineAnalysis(
        const std::string& engine_id,
        const AnalysisConfig& config,
        CombinedAnalysisResult& result
    );

    // Cross-validate results from multiple tools
    void performCrossValidation(CombinedAnalysisResult& result);

    // Write temporary state file for tool consumption
    std::string writeTempStateFile(const nlohmann::json& state_data);
};

} // namespace dase
