/**
 * IGSOA Status Codes
 *
 * Provides structured error reporting for C API and internal error handling.
 * Replaces silent nullptr returns with explicit error codes and messages.
 */

#pragma once

#include <string>
#include <cstdint>

namespace dase {
namespace igsoa {

/**
 * Status codes for IGSOA operations
 *
 * These codes provide detailed error information for debugging and
 * proper error handling in host languages (Julia, Rust, Python, etc.)
 */
enum class IGSOAStatus : int32_t {
    // Success
    SUCCESS = 0,

    // Configuration errors (1-99)
    ERROR_INVALID_CONFIG = 1,           // General config validation failure
    ERROR_INVALID_NUM_NODES = 2,        // num_nodes <= 0 or too large
    ERROR_INVALID_R_C = 3,              // R_c <= 0 or unreasonable
    ERROR_INVALID_DT = 4,               // dt <= 0 or too large (instability)
    ERROR_INVALID_KAPPA = 5,            // kappa < 0
    ERROR_INVALID_GAMMA = 6,            // gamma < 0

    // Memory errors (100-199)
    ERROR_OUT_OF_MEMORY = 100,          // Allocation failed
    ERROR_BUFFER_TOO_SMALL = 101,       // Output buffer insufficient

    // Runtime errors (200-299)
    ERROR_NULL_HANDLE = 200,            // Engine handle is nullptr
    ERROR_NULL_POINTER = 201,           // Required pointer argument is nullptr
    ERROR_INVALID_DIMENSIONS = 202,     // Lattice dimensions invalid (e.g., N_x = 0)
    ERROR_OUT_OF_BOUNDS = 203,          // Array access out of bounds
    ERROR_NOT_INITIALIZED = 204,        // Engine/cache not properly initialized

    // Physics errors (300-399)
    ERROR_NUMERICAL_INSTABILITY = 300,  // Detected NaN or Inf in computation
    ERROR_CONVERGENCE_FAILED = 301,     // Iterative solver didn't converge
    ERROR_UNPHYSICAL_STATE = 302,       // State violates physical constraints

    // File I/O errors (400-499)
    ERROR_FILE_NOT_FOUND = 400,         // Cannot open file
    ERROR_FILE_WRITE_FAILED = 401,      // Cannot write to file
    ERROR_FILE_READ_FAILED = 402,       // Cannot read from file
    ERROR_INVALID_FILE_FORMAT = 403,    // File format not recognized

    // QIA-specific errors (500-599)
    ERROR_CACHE_NOT_BUILT = 500,        // Neighbor cache not built before use
    ERROR_CACHE_REBUILD_FAILED = 501,   // Failed to rebuild cache
    ERROR_SPATIAL_HASH_FAILED = 502,    // Spatial hash operation failed

    // General errors (900-999)
    ERROR_NOT_IMPLEMENTED = 900,        // Feature not yet implemented
    ERROR_UNKNOWN = 999                 // Unknown error
};

/**
 * Convert status code to human-readable string
 *
 * @param status Status code
 * @return String description of the error
 */
inline const char* statusToString(IGSOAStatus status) {
    switch (status) {
        case IGSOAStatus::SUCCESS:
            return "Success";

        // Configuration errors
        case IGSOAStatus::ERROR_INVALID_CONFIG:
            return "Invalid configuration";
        case IGSOAStatus::ERROR_INVALID_NUM_NODES:
            return "Invalid num_nodes (must be positive and within bounds)";
        case IGSOAStatus::ERROR_INVALID_R_C:
            return "Invalid R_c (causal radius must be positive)";
        case IGSOAStatus::ERROR_INVALID_DT:
            return "Invalid dt (time step must be positive and not too large)";
        case IGSOAStatus::ERROR_INVALID_KAPPA:
            return "Invalid kappa (coupling strength must be non-negative)";
        case IGSOAStatus::ERROR_INVALID_GAMMA:
            return "Invalid gamma (dissipation must be non-negative)";

        // Memory errors
        case IGSOAStatus::ERROR_OUT_OF_MEMORY:
            return "Out of memory (allocation failed)";
        case IGSOAStatus::ERROR_BUFFER_TOO_SMALL:
            return "Output buffer too small";

        // Runtime errors
        case IGSOAStatus::ERROR_NULL_HANDLE:
            return "Engine handle is null";
        case IGSOAStatus::ERROR_NULL_POINTER:
            return "Required pointer argument is null";
        case IGSOAStatus::ERROR_INVALID_DIMENSIONS:
            return "Invalid lattice dimensions";
        case IGSOAStatus::ERROR_OUT_OF_BOUNDS:
            return "Array access out of bounds";
        case IGSOAStatus::ERROR_NOT_INITIALIZED:
            return "Engine or cache not properly initialized";

        // Physics errors
        case IGSOAStatus::ERROR_NUMERICAL_INSTABILITY:
            return "Numerical instability detected (NaN or Inf)";
        case IGSOAStatus::ERROR_CONVERGENCE_FAILED:
            return "Iterative solver failed to converge";
        case IGSOAStatus::ERROR_UNPHYSICAL_STATE:
            return "State violates physical constraints";

        // File I/O errors
        case IGSOAStatus::ERROR_FILE_NOT_FOUND:
            return "File not found";
        case IGSOAStatus::ERROR_FILE_WRITE_FAILED:
            return "Failed to write to file";
        case IGSOAStatus::ERROR_FILE_READ_FAILED:
            return "Failed to read from file";
        case IGSOAStatus::ERROR_INVALID_FILE_FORMAT:
            return "Invalid file format";

        // QIA-specific errors
        case IGSOAStatus::ERROR_CACHE_NOT_BUILT:
            return "Neighbor cache not built (call build() first)";
        case IGSOAStatus::ERROR_CACHE_REBUILD_FAILED:
            return "Failed to rebuild cache";
        case IGSOAStatus::ERROR_SPATIAL_HASH_FAILED:
            return "Spatial hash operation failed";

        // General errors
        case IGSOAStatus::ERROR_NOT_IMPLEMENTED:
            return "Feature not yet implemented";
        case IGSOAStatus::ERROR_UNKNOWN:
        default:
            return "Unknown error";
    }
}

/**
 * Status result with optional error message
 *
 * Provides structured error information with context-specific messages.
 */
struct StatusResult {
    IGSOAStatus code;
    std::string message;

    StatusResult() : code(IGSOAStatus::SUCCESS), message("") {}

    explicit StatusResult(IGSOAStatus status_code)
        : code(status_code)
        , message(statusToString(status_code))
    {}

    StatusResult(IGSOAStatus status_code, const std::string& msg)
        : code(status_code)
        , message(msg)
    {}

    bool isSuccess() const { return code == IGSOAStatus::SUCCESS; }
    bool isError() const { return code != IGSOAStatus::SUCCESS; }

    // Implicit conversion to bool (true if success)
    explicit operator bool() const { return isSuccess(); }
};

/**
 * Create success result
 */
inline StatusResult makeSuccess() {
    return StatusResult(IGSOAStatus::SUCCESS);
}

/**
 * Create error result with custom message
 */
inline StatusResult makeError(IGSOAStatus code, const std::string& message) {
    return StatusResult(code, message);
}

/**
 * Create error result with default message
 */
inline StatusResult makeError(IGSOAStatus code) {
    return StatusResult(code);
}

} // namespace igsoa
} // namespace dase
