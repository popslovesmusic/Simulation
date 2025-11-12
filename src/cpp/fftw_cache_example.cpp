/**
 * @file fftw_cache_example.cpp
 * @brief Example usage of FFTW Wisdom Cache
 *
 * This demonstrates how to integrate FFTWWisdomCache into your engine.
 *
 * Compile with:
 *   g++ -o fftw_cache_example fftw_cache_example.cpp -lfftw3 -std=c++11
 */

#include "fftw_wisdom_cache.hpp"
#include <iostream>
#include <chrono>

using namespace dase;
using namespace std::chrono;

void benchmark_fft_with_cache(int nx, int ny, int num_iterations) {
    std::cout << "\n==========================================================\n";
    std::cout << "Benchmarking " << nx << "x" << ny << " FFT (" << num_iterations << " iterations)\n";
    std::cout << "==========================================================\n";

    // Initialize cache
    FFTWWisdomCache::initialize("./cache/fftw_wisdom");

    // Allocate data
    fftw_complex* data = fftw_alloc_complex(nx * ny);

    // Fill with test data
    for (int i = 0; i < nx * ny; i++) {
        data[i][0] = 1.0;  // Real part
        data[i][1] = 0.0;  // Imaginary part
    }

    // Create plan (first time - will be cached)
    auto t0 = high_resolution_clock::now();
    fftw_plan plan = FFTWWisdomCache::create_plan_2d(nx, ny, data, data);
    auto t1 = high_resolution_clock::now();

    auto plan_time = duration_cast<microseconds>(t1 - t0).count();
    std::cout << "Plan creation time: " << plan_time / 1000.0 << " ms\n";

    // Execute FFTs
    auto t2 = high_resolution_clock::now();
    for (int i = 0; i < num_iterations; i++) {
        fftw_execute(plan);
    }
    auto t3 = high_resolution_clock::now();

    auto exec_time = duration_cast<microseconds>(t3 - t2).count();
    std::cout << "Total execution time: " << exec_time / 1000.0 << " ms\n";
    std::cout << "Avg per FFT: " << (exec_time / num_iterations) / 1000.0 << " ms\n";

    // Cleanup
    fftw_destroy_plan(plan);
    fftw_free(data);

    FFTWWisdomCache::cleanup();

    std::cout << "\nNow run again to see cached wisdom speedup!\n";
}

void example_basic_usage() {
    std::cout << "\n==========================================================\n";
    std::cout << "Example: Basic Usage\n";
    std::cout << "==========================================================\n";

    // Initialize cache system
    FFTWWisdomCache::initialize();

    // 1D FFT example
    int n = 1024;
    fftw_complex* data_1d = fftw_alloc_complex(n);

    fftw_plan plan_1d = FFTWWisdomCache::create_plan_1d(n, data_1d, data_1d);
    fftw_execute(plan_1d);
    fftw_destroy_plan(plan_1d);
    fftw_free(data_1d);

    std::cout << "1D FFT (n=" << n << ") completed\n";

    // 2D FFT example
    int nx = 512, ny = 512;
    fftw_complex* data_2d = fftw_alloc_complex(nx * ny);

    fftw_plan plan_2d = FFTWWisdomCache::create_plan_2d(nx, ny, data_2d, data_2d);
    fftw_execute(plan_2d);
    fftw_destroy_plan(plan_2d);
    fftw_free(data_2d);

    std::cout << "2D FFT (" << nx << "x" << ny << ") completed\n";

    // 3D FFT example
    int nz = 64;
    fftw_complex* data_3d = fftw_alloc_complex(nx * ny * nz);

    fftw_plan plan_3d = FFTWWisdomCache::create_plan_3d(nx, ny, nz, data_3d, data_3d);
    fftw_execute(plan_3d);
    fftw_destroy_plan(plan_3d);
    fftw_free(data_3d);

    std::cout << "3D FFT (" << nx << "x" << ny << "x" << nz << ") completed\n";

    // Cleanup
    FFTWWisdomCache::cleanup();

    std::cout << "\nAll wisdom saved to cache!\n";
}

void example_engine_integration() {
    std::cout << "\n==========================================================\n";
    std::cout << "Example: Engine Integration Pattern\n";
    std::cout << "==========================================================\n";

    std::cout << R"(
// In your engine initialization:
void Engine::initialize() {
    FFTWWisdomCache::initialize("./cache/fftw_wisdom");
    // ... other initialization
}

// Replace fftw_plan_dft_2d calls with:
void Engine::setup_fft_for_grid(int nx, int ny) {
    // OLD:
    // plan = fftw_plan_dft_2d(nx, ny, data, data, FFTW_FORWARD, FFTW_MEASURE);

    // NEW:
    plan = FFTWWisdomCache::create_plan_2d(nx, ny, data, data);
}

// In your engine cleanup:
void Engine::cleanup() {
    FFTWWisdomCache::cleanup();
    // ... other cleanup
}
)" << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "\n";
    std::cout << "##########################################################\n";
    std::cout << "#  FFTW Wisdom Cache - Examples and Benchmarks          #\n";
    std::cout << "##########################################################\n";

    // Example 1: Basic usage
    example_basic_usage();

    // Example 2: Benchmark
    benchmark_fft_with_cache(512, 512, 100);

    // Example 3: Engine integration pattern
    example_engine_integration();

    std::cout << "\n";
    std::cout << "##########################################################\n";
    std::cout << "#  Integration Complete!                                 #\n";
    std::cout << "##########################################################\n";
    std::cout << "\nNext steps:\n";
    std::cout << "1. Include fftw_wisdom_cache.hpp in your engine\n";
    std::cout << "2. Call FFTWWisdomCache::initialize() at startup\n";
    std::cout << "3. Replace fftw_plan_dft_* with FFTWWisdomCache::create_plan_*\n";
    std::cout << "4. Call FFTWWisdomCache::cleanup() at shutdown\n";
    std::cout << "\n";

    return 0;
}
