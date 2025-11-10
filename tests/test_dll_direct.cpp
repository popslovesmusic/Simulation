/**
 * Direct DLL Test
 * Tests the DASE DLL functions directly
 */

#include <iostream>
#include <windows.h>
#include <vector>
#include <cmath>

// Function pointer types
typedef void* (*CreateEngineFunc)(uint32_t);
typedef void (*DestroyEngineFunc)(void*);
typedef void (*RunMissionFunc)(void*, const double*, const double*, uint64_t, uint32_t);
typedef void (*GetMetricsFunc)(void*, double*, double*, double*, uint64_t*);

int main() {
    std::cout << "Loading DLL...\n";

    // Load DLL
    HMODULE dll = LoadLibraryA("dase_engine_phase4b.dll");
    if (!dll) {
        std::cerr << "Failed to load DLL. Error: " << GetLastError() << "\n";
        return 1;
    }
    std::cout << "DLL loaded successfully!\n";

    // Get function pointers
    auto create_engine = reinterpret_cast<CreateEngineFunc>(
        GetProcAddress(dll, "dase_create_engine"));
    auto destroy_engine = reinterpret_cast<DestroyEngineFunc>(
        GetProcAddress(dll, "dase_destroy_engine"));
    auto run_mission = reinterpret_cast<RunMissionFunc>(
        GetProcAddress(dll, "dase_run_mission_optimized_phase4b"));
    auto get_metrics = reinterpret_cast<GetMetricsFunc>(
        GetProcAddress(dll, "dase_get_metrics"));

    if (!create_engine) {
        std::cerr << "Failed to find dase_create_engine\n";
        return 1;
    }
    if (!destroy_engine) {
        std::cerr << "Failed to find dase_destroy_engine\n";
        return 1;
    }
    if (!run_mission) {
        std::cerr << "Failed to find dase_run_mission_optimized_phase4b\n";
        return 1;
    }
    if (!get_metrics) {
        std::cerr << "Failed to find dase_get_metrics\n";
        return 1;
    }

    std::cout << "All functions found!\n";

    // Create engine
    std::cout << "Creating engine with 1024 nodes...\n";
    void* engine = create_engine(1024);
    if (!engine) {
        std::cerr << "Failed to create engine\n";
        return 1;
    }
    std::cout << "Engine created: " << engine << "\n";

    // Prepare inputs
    const int num_steps = 50;
    std::vector<double> input_signals(num_steps);
    std::vector<double> control_patterns(num_steps);

    for (int i = 0; i < num_steps; i++) {
        input_signals[i] = std::sin(i * 0.01);
        control_patterns[i] = std::cos(i * 0.01);
    }

    // Run mission
    std::cout << "Running mission with " << num_steps << " steps...\n";
    run_mission(engine, input_signals.data(), control_patterns.data(), num_steps, 10);
    std::cout << "Mission completed!\n";

    // Get metrics
    double ns_per_op = 0, ops_per_sec = 0, speedup = 0;
    uint64_t total_ops = 0;
    get_metrics(engine, &ns_per_op, &ops_per_sec, &speedup, &total_ops);

    std::cout << "\nMetrics:\n";
    std::cout << "  ns/op: " << ns_per_op << "\n";
    std::cout << "  ops/sec: " << ops_per_sec << "\n";
    std::cout << "  speedup: " << speedup << "x\n";
    std::cout << "  total ops: " << total_ops << "\n";

    // Cleanup
    destroy_engine(engine);
    FreeLibrary(dll);

    std::cout << "\nTest completed successfully!\n";
    return 0;
}
