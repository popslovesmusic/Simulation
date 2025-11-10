/**
 * D-ASE Engine C API Implementation
 *
 * This file implements the C-compatible interface for the DASE Engine,
 * wrapping the C++ AnalogCellularEngineAVX2 class for use with Julia/Rust FFI.
 */

#include "dase_capi.h"
#include "analog_universal_node_engine_avx2.h"
#include <memory>

// =============================================================================
// HELPER: Cast between opaque handle and C++ pointer
// =============================================================================

static inline AnalogCellularEngineAVX2* to_cpp_engine(DaseEngineHandle handle) {
    return reinterpret_cast<AnalogCellularEngineAVX2*>(handle);
}

static inline DaseEngineHandle to_c_handle(AnalogCellularEngineAVX2* engine) {
    return reinterpret_cast<DaseEngineHandle>(engine);
}

// =============================================================================
// EXTERN "C" IMPLEMENTATIONS
// =============================================================================

extern "C" {

// -----------------------------------------------------------------------------
// Status Codes
// -----------------------------------------------------------------------------

const char* dase_status_string(DaseStatus status) {
    switch (status) {
        case DASE_SUCCESS:
            return "Success";
        case DASE_ERROR_OUT_OF_MEMORY:
            return "Out of memory (allocation failed)";
        case DASE_ERROR_NULL_HANDLE:
            return "Engine handle is null";
        case DASE_ERROR_NULL_POINTER:
            return "Required pointer argument is null";
        case DASE_ERROR_INVALID_PARAM:
            return "Invalid parameter";
        case DASE_ERROR_UNKNOWN:
        default:
            return "Unknown error";
    }
}

// Helper: Copy error message to buffer (safe, always null-terminates)
static void copy_error_message(char* buffer, uint32_t buffer_size, const char* message) {
    if (!buffer || buffer_size == 0) return;

    // Copy up to buffer_size - 1 characters
    uint32_t i = 0;
    while (i < buffer_size - 1 && message[i] != '\0') {
        buffer[i] = message[i];
        ++i;
    }
    buffer[i] = '\0';  // Always null-terminate
}

// -----------------------------------------------------------------------------
// Engine Lifecycle
// -----------------------------------------------------------------------------

DaseEngineHandle dase_create_engine(uint32_t num_nodes) {
    try {
        auto* engine = new AnalogCellularEngineAVX2(static_cast<std::size_t>(num_nodes));
        return to_c_handle(engine);
    } catch (...) {
        // Return null on allocation failure
        return nullptr;
    }
}

DaseStatus dase_create_engine_ex(
    uint32_t num_nodes,
    DaseEngineHandle* out_handle,
    char* error_msg_buffer,
    uint32_t error_msg_size
) {
    // Validate output handle pointer
    if (!out_handle) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size,
                             "out_handle parameter cannot be null");
        }
        return DASE_ERROR_NULL_POINTER;
    }

    // Validate num_nodes
    if (num_nodes == 0) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size,
                             "num_nodes must be positive (got 0)");
        }
        *out_handle = nullptr;
        return DASE_ERROR_INVALID_PARAM;
    }

    // Check reasonable bounds (prevent excessive allocation)
    constexpr uint32_t MAX_NODES = 100'000'000;  // 100M nodes
    if (num_nodes > MAX_NODES) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size,
                             "num_nodes exceeds maximum (100M nodes)");
        }
        *out_handle = nullptr;
        return DASE_ERROR_INVALID_PARAM;
    }

    // Try to create engine
    try {
        auto* engine = new AnalogCellularEngineAVX2(static_cast<std::size_t>(num_nodes));
        *out_handle = to_c_handle(engine);
        return DASE_SUCCESS;
    } catch (const std::bad_alloc&) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size,
                             "Memory allocation failed");
        }
        *out_handle = nullptr;
        return DASE_ERROR_OUT_OF_MEMORY;
    } catch (const std::exception& e) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size, e.what());
        }
        *out_handle = nullptr;
        return DASE_ERROR_UNKNOWN;
    } catch (...) {
        if (error_msg_buffer && error_msg_size > 0) {
            copy_error_message(error_msg_buffer, error_msg_size,
                             "Unknown exception during engine creation");
        }
        *out_handle = nullptr;
        return DASE_ERROR_UNKNOWN;
    }
}

void dase_destroy_engine(DaseEngineHandle handle) {
    if (handle) {
        auto* engine = to_cpp_engine(handle);
        delete engine;
    }
}

// -----------------------------------------------------------------------------
// High-Performance Mission Execution
// -----------------------------------------------------------------------------

void dase_run_mission_optimized(
    DaseEngineHandle handle,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
) {
    if (!handle || !input_signals || !control_patterns || num_steps == 0) {
        return; // Invalid parameters
    }

    auto* engine = to_cpp_engine(handle);
    engine->runMissionOptimized(input_signals, control_patterns,
                                num_steps, iterations_per_node);
}

void dase_run_mission_optimized_phase4b(
    DaseEngineHandle handle,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
) {
    if (!handle || !input_signals || !control_patterns || num_steps == 0) {
        return; // Invalid parameters
    }

    auto* engine = to_cpp_engine(handle);
    engine->runMissionOptimized_Phase4B(input_signals, control_patterns,
                                        num_steps, iterations_per_node);
}

void dase_run_mission_optimized_phase4c(
    DaseEngineHandle handle,
    const double* input_signals,
    const double* control_patterns,
    uint64_t num_steps,
    uint32_t iterations_per_node
) {
    if (!handle || !input_signals || !control_patterns || num_steps == 0) {
        return; // Invalid parameters
    }

    auto* engine = to_cpp_engine(handle);
    engine->runMissionOptimized_Phase4C(input_signals, control_patterns,
                                        num_steps, iterations_per_node);
}

// -----------------------------------------------------------------------------
// Metrics Retrieval
// -----------------------------------------------------------------------------

void dase_get_metrics(
    DaseEngineHandle handle,
    double* out_ns_per_op,
    double* out_ops_per_sec,
    double* out_speedup_factor,
    uint64_t* out_total_ops
) {
    if (!handle) {
        return; // Invalid handle
    }

    auto* engine = to_cpp_engine(handle);
    EngineMetrics metrics = engine->getMetrics();

    if (out_ns_per_op) {
        *out_ns_per_op = metrics.current_ns_per_op;
    }
    if (out_ops_per_sec) {
        *out_ops_per_sec = metrics.current_ops_per_second;
    }
    if (out_speedup_factor) {
        *out_speedup_factor = metrics.speedup_factor;
    }
    if (out_total_ops) {
        *out_total_ops = static_cast<uint64_t>(metrics.total_operations);
    }
}

// -----------------------------------------------------------------------------
// CPU Features
// -----------------------------------------------------------------------------

int dase_has_avx2(void) {
    return CPUFeatures::hasAVX2() ? 1 : 0;
}

int dase_has_fma(void) {
    return CPUFeatures::hasFMA() ? 1 : 0;
}

} // extern "C"
