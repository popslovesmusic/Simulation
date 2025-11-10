/**
 * Python Bridge Implementation
 */

#include "python_bridge.h"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <array>

#ifdef _WIN32
#include <windows.h>
#define popen _popen
#define pclose _pclose
#else
#include <unistd.h>
#endif

namespace fs = std::filesystem;

namespace dase {
namespace python {

PythonAnalysisResult PythonBridge::runAnalysisScript(
    const std::string& state_json_path,
    const PythonAnalysisConfig& config
) {
    PythonAnalysisResult result;
    result.success = false;
    result.exit_code = -1;
    result.execution_time_ms = 0;  // Initialize to prevent uninitialized variable

    auto start_time = std::chrono::high_resolution_clock::now();

    try {
        // Build command line
        std::string cmd = buildCommandLine(config.script_path, state_json_path, config);

        // Execute command
        FILE* pipe = popen(cmd.c_str(), "r");
        if (!pipe) {
            result.error_message = "Failed to execute Python command: " + cmd;
            return result;
        }

        // Read output
        std::array<char, 256> buffer;
        while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
            result.stdout_output += buffer.data();
        }

        // Get exit code
        result.exit_code = pclose(pipe);

        // Check success
        result.success = (result.exit_code == 0);

        // Find generated files
        if (!config.output_dir.empty() && fs::exists(config.output_dir)) {
            result.generated_files = findGeneratedFiles(config.output_dir);
        }

    } catch (const std::exception& e) {
        result.error_message = std::string("Exception during Python execution: ") + e.what();
        result.success = false;
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    result.execution_time_ms = duration.count();

    return result;
}

bool PythonBridge::checkDependencies(
    const std::string& python_exe,
    const std::vector<std::string>& required_packages
) {
    try {
        // Check Python itself
        std::string version = getPythonVersion(python_exe);
        if (version.empty()) {
            return false;
        }

        // Check each package
        for (const auto& package : required_packages) {
            std::string cmd = python_exe + " -c \"import " + package + "\" 2>&1";
            FILE* pipe = popen(cmd.c_str(), "r");
            if (!pipe) {
                return false;
            }

            std::array<char, 128> buffer;
            std::string output;
            while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
                output += buffer.data();
            }

            int exit_code = pclose(pipe);
            if (exit_code != 0) {
                return false;  // Package not found
            }
        }

        return true;

    } catch (...) {
        return false;
    }
}

std::string PythonBridge::getPythonVersion(const std::string& python_exe) {
    try {
        std::string cmd = python_exe + " --version 2>&1";
        FILE* pipe = popen(cmd.c_str(), "r");
        if (!pipe) {
            return "";
        }

        std::array<char, 128> buffer;
        std::string result;
        while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
            result += buffer.data();
        }

        pclose(pipe);

        // Extract version number (e.g., "Python 3.11.0" -> "3.11.0")
        size_t pos = result.find("Python ");
        if (pos != std::string::npos) {
            result = result.substr(pos + 7);
            // Remove trailing newline
            if (!result.empty() && result.back() == '\n') {
                result.pop_back();
            }
        }

        return result;

    } catch (...) {
        return "";
    }
}

std::vector<std::string> PythonBridge::listAvailableScripts(
    const std::string& scripts_dir
) {
    std::vector<std::string> scripts;

    try {
        if (!fs::exists(scripts_dir)) {
            return scripts;
        }

        for (const auto& entry : fs::directory_iterator(scripts_dir)) {
            if (entry.is_regular_file() && entry.path().extension() == ".py") {
                // Exclude internal/utility scripts
                std::string filename = entry.path().filename().string();
                if (filename.find("analyze") != std::string::npos ||
                    filename.find("plot") != std::string::npos ||
                    filename.find("compute") != std::string::npos) {
                    scripts.push_back(entry.path().string());
                }
            }
        }

    } catch (...) {
        // Return empty list on error
    }

    return scripts;
}

bool PythonBridge::writeStateToFile(
    const nlohmann::json& state_data,
    const std::string& output_path
) {
    try {
        std::ofstream file(output_path);
        if (!file.is_open()) {
            return false;
        }

        file << state_data.dump(2);  // Pretty print with indent
        file.close();

        return true;

    } catch (...) {
        return false;
    }
}

std::string PythonBridge::buildCommandLine(
    const std::string& script_path,
    const std::string& state_json_path,
    const PythonAnalysisConfig& config
) {
    std::ostringstream cmd;

    // Python executable
    cmd << "\"" << config.python_executable << "\" ";

    // Script path
    cmd << "\"" << script_path << "\" ";

    // State JSON file (positional argument)
    cmd << "\"" << state_json_path << "\" ";

    // Additional arguments
    for (const auto& [key, value] : config.args) {
        if (key == "positional") {
            // Positional argument (e.g., R_c for analyze_igsoa_state.py)
            cmd << value << " ";
        } else {
            // Named argument
            cmd << "--" << key << " ";
            if (!value.empty()) {
                cmd << "\"" << value << "\" ";
            }
        }
    }

    return cmd.str();
}

std::vector<std::string> PythonBridge::findGeneratedFiles(
    const std::string& output_dir,
    const std::vector<std::string>& extensions
) {
    std::vector<std::string> files;

    try {
        if (!fs::exists(output_dir)) {
            return files;
        }

        for (const auto& entry : fs::recursive_directory_iterator(output_dir)) {
            if (entry.is_regular_file()) {
                std::string ext = entry.path().extension().string();
                if (std::find(extensions.begin(), extensions.end(), ext) != extensions.end()) {
                    files.push_back(entry.path().string());
                }
            }
        }

    } catch (...) {
        // Return partial list on error
    }

    return files;
}

} // namespace python
} // namespace dase
