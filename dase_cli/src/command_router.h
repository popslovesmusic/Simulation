/**
 * Command Router - Dispatches JSON commands to appropriate handlers
 */

#pragma once

#include <string>
#include <map>
#include <functional>
#include <memory>
#include "json.hpp"

// Forward declarations
class EngineManager;

using json = nlohmann::json;

class CommandRouter {
public:
    CommandRouter();
    ~CommandRouter();

    // Execute a JSON command and return JSON response
    json execute(const json& command);

private:
    // Command handlers
    json handleGetCapabilities(const json& params);
    json handleListEngines(const json& params);
    json handleCreateEngine(const json& params);
    json handleDestroyEngine(const json& params);
    json handleSetNodeState(const json& params);
    json handleGetNodeState(const json& params);
    json handleSetIgsoaState(const json& params);
    json handleSetSatpState(const json& params);
    json handleRunMission(const json& params);
    json handleRunMissionWithSnapshots(const json& params);
    json handleRunBenchmark(const json& params);
    json handleGetMetrics(const json& params);
    json handleGetState(const json& params);
    json handleGetSatpState(const json& params);
    json handleGetCenterOfMass(const json& params);

    // Analysis command handlers
    json handleCheckAnalysisTools(const json& params);
    json handlePythonAnalyze(const json& params);
    json handleEngineFFT(const json& params);
    json handleAnalyzeFields(const json& params);

    // Helper to create success response
    json createSuccessResponse(const std::string& command,
                                     const json& result,
                                     double execution_time_ms);

    // Helper to create error response
    json createErrorResponse(const std::string& command,
                                   const std::string& error,
                                   const std::string& error_code);

    // Engine manager (manages engine lifecycle)
    std::unique_ptr<EngineManager> engine_manager;

    // Command registry
    std::map<std::string, std::function<json(const json&)>> command_handlers;
};
