/**
 * Python Bridge - Interface for calling existing Python analysis scripts
 *
 * Enables dase_cli to invoke Python analysis tools:
 * - analyze_igsoa_state.py
 * - analyze_igsoa_2d.py
 * - plot_satp_state.py
 * - compute_autocorrelation.py
 */

#pragma once

#include <string>
#include <vector>
#include <map>
#include "json.hpp"

namespace dase {
namespace python {

struct PythonAnalysisConfig {
    std::string script_path;
    std::string python_executable = "python";
    std::string output_dir = "analysis_output";
    std::map<std::string, std::string> args;  // Command-line arguments
    int timeout_ms = 120000;  // 2 minutes default
};

struct PythonAnalysisResult {
    bool success;
    int exit_code;
    std::string stdout_output;
    std::string stderr_output;
    std::vector<std::string> generated_files;
    double execution_time_ms;
    std::string error_message;
};

class PythonBridge {
public:
    /**
     * Run Python analysis script with state data
     *
     * @param state_json_path Path to JSON file with engine state
     * @param config Python script configuration
     * @return Analysis result with outputs and generated files
     */
    static PythonAnalysisResult runAnalysisScript(
        const std::string& state_json_path,
        const PythonAnalysisConfig& config
    );

    /**
     * Check if Python is available and has required packages
     *
     * @param python_exe Path to Python executable
     * @param required_packages List of required packages (numpy, scipy, etc.)
     * @return true if all dependencies are available
     */
    static bool checkDependencies(
        const std::string& python_exe,
        const std::vector<std::string>& required_packages
    );

    /**
     * Get Python version
     *
     * @param python_exe Path to Python executable
     * @return Version string (e.g., "3.11.0")
     */
    static std::string getPythonVersion(const std::string& python_exe);

    /**
     * List available analysis scripts in directory
     *
     * @param scripts_dir Directory to search (default: dase_cli)
     * @return List of available .py scripts
     */
    static std::vector<std::string> listAvailableScripts(
        const std::string& scripts_dir = "."
    );

    /**
     * Write engine state to temporary JSON file for Python consumption
     *
     * @param state_data State data as JSON
     * @param output_path Output file path
     * @return true if successful
     */
    static bool writeStateToFile(
        const nlohmann::json& state_data,
        const std::string& output_path
    );

private:
    static std::string buildCommandLine(
        const std::string& script_path,
        const std::string& state_json_path,
        const PythonAnalysisConfig& config
    );

    static std::vector<std::string> findGeneratedFiles(
        const std::string& output_dir,
        const std::vector<std::string>& extensions = {".png", ".pdf", ".svg", ".txt", ".json"}
    );
};

} // namespace python
} // namespace dase
