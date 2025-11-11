/**
 * Metric Emitter - Structured metric output for real-time monitoring
 *
 * Emits metrics in format: METRIC:{"name":"...", "value":..., "units":"..."}
 * which the backend can parse and stream to the frontend via WebSocket.
 */

#pragma once

#include <string>
#include <iostream>
#include "json.hpp"

using json = nlohmann::json;

namespace dase {

/**
 * Emit a metric to stdout for backend parsing
 * @param name Metric name (e.g., "simulation_time", "energy")
 * @param value Numeric value
 * @param units Unit string (e.g., "s", "joules", "dimensionless")
 */
inline void emitMetric(const std::string& name, double value, const std::string& units = "dimensionless") {
    json metric = {
        {"name", name},
        {"value", value},
        {"units", units}
    };
    std::cout << "METRIC:" << metric.dump() << std::endl;
}

/**
 * Emit a metric with integer value
 */
inline void emitMetric(const std::string& name, int value, const std::string& units = "dimensionless") {
    json metric = {
        {"name", name},
        {"value", value},
        {"units", units}
    };
    std::cout << "METRIC:" << metric.dump() << std::endl;
}

/**
 * Emit a metric with string value
 */
inline void emitMetric(const std::string& name, const std::string& value) {
    json metric = {
        {"name", name},
        {"value", value},
        {"units", "string"}
    };
    std::cout << "METRIC:" << metric.dump() << std::endl;
}

/**
 * Emit multiple metrics at once
 * @param metrics Map of name -> value
 * @param units Optional map of name -> units (defaults to "dimensionless")
 */
inline void emitMetrics(const std::map<std::string, double>& metrics,
                       const std::map<std::string, std::string>& units = {}) {
    for (const auto& [name, value] : metrics) {
        std::string unit = "dimensionless";
        auto unit_it = units.find(name);
        if (unit_it != units.end()) {
            unit = unit_it->second;
        }
        emitMetric(name, value, unit);
    }
}

} // namespace dase
