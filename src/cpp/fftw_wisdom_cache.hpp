/**
 * @file fftw_wisdom_cache.hpp
 * @brief FFTW Wisdom Cache Integration for DASE/IGSOA Engine
 *
 * This module provides automatic caching of FFTW wisdom to dramatically
 * speed up FFT planning operations.
 *
 * Benefits:
 * - 100-1000x faster FFT initialization
 * - Persistent wisdom across runs
 * - Automatic fallback to planning if cache miss
 *
 * Usage:
 *   FFTWWisdomCache::initialize("./cache/fftw_wisdom");
 *
 *   fftw_complex* data = fftw_alloc_complex(nx * ny);
 *   fftw_plan plan = FFTWWisdomCache::create_plan_2d(nx, ny, data, data);
 *   fftw_execute(plan);
 *   fftw_destroy_plan(plan);
 *   fftw_free(data);
 *
 *   FFTWWisdomCache::cleanup();
 */

#ifndef FFTW_WISDOM_CACHE_HPP
#define FFTW_WISDOM_CACHE_HPP

#include <fftw3.h>
#include <string>
#include <fstream>
#include <sstream>
#include <iostream>
#include <sys/stat.h>

namespace dase {

class FFTWWisdomCache {
public:
    /**
     * Initialize the wisdom cache system.
     *
     * @param cache_dir Directory for wisdom cache files
     */
    static void initialize(const std::string& cache_dir = "./cache/fftw_wisdom") {
        cache_directory_ = cache_dir;
        create_cache_directory();
        load_global_wisdom();
    }

    /**
     * Clean up FFTW resources.
     */
    static void cleanup() {
        save_global_wisdom();
        fftw_cleanup();
    }

    /**
     * Create 1D FFT plan with caching.
     *
     * @param n Transform size
     * @param in Input array
     * @param out Output array
     * @param sign FFTW_FORWARD or FFTW_BACKWARD
     * @param flags Planning flags (default: FFTW_MEASURE)
     * @return FFTW plan
     */
    static fftw_plan create_plan_1d(
        int n,
        fftw_complex* in,
        fftw_complex* out,
        int sign = FFTW_FORWARD,
        unsigned flags = FFTW_MEASURE
    ) {
        std::string key = wisdom_key_1d(n);
        return create_plan_with_cache(key, [&]() {
            return fftw_plan_dft_1d(n, in, out, sign, flags);
        });
    }

    /**
     * Create 2D FFT plan with caching.
     *
     * @param nx X dimension
     * @param ny Y dimension
     * @param in Input array
     * @param out Output array
     * @param sign FFTW_FORWARD or FFTW_BACKWARD
     * @param flags Planning flags
     * @return FFTW plan
     */
    static fftw_plan create_plan_2d(
        int nx, int ny,
        fftw_complex* in,
        fftw_complex* out,
        int sign = FFTW_FORWARD,
        unsigned flags = FFTW_MEASURE
    ) {
        std::string key = wisdom_key_2d(nx, ny);
        return create_plan_with_cache(key, [&]() {
            return fftw_plan_dft_2d(nx, ny, in, out, sign, flags);
        });
    }

    /**
     * Create 3D FFT plan with caching.
     *
     * @param nx X dimension
     * @param ny Y dimension
     * @param nz Z dimension
     * @param in Input array
     * @param out Output array
     * @param sign FFTW_FORWARD or FFTW_BACKWARD
     * @param flags Planning flags
     * @return FFTW plan
     */
    static fftw_plan create_plan_3d(
        int nx, int ny, int nz,
        fftw_complex* in,
        fftw_complex* out,
        int sign = FFTW_FORWARD,
        unsigned flags = FFTW_MEASURE
    ) {
        std::string key = wisdom_key_3d(nx, ny, nz);
        return create_plan_with_cache(key, [&]() {
            return fftw_plan_dft_3d(nx, ny, nz, in, out, sign, flags);
        });
    }

    /**
     * Export wisdom to specific file.
     *
     * @param filename Output filename
     * @return True if successful
     */
    static bool export_wisdom(const std::string& filename) {
        char* wisdom_str = fftw_export_wisdom_to_string();
        if (!wisdom_str) return false;

        std::ofstream file(filename, std::ios::binary);
        if (!file) {
            fftw_free(wisdom_str);
            return false;
        }

        file << wisdom_str;
        fftw_free(wisdom_str);
        return true;
    }

    /**
     * Import wisdom from specific file.
     *
     * @param filename Input filename
     * @return True if successful
     */
    static bool import_wisdom(const std::string& filename) {
        std::ifstream file(filename, std::ios::binary);
        if (!file) return false;

        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string wisdom_data = buffer.str();

        int success = fftw_import_wisdom_from_string(wisdom_data.c_str());
        return success != 0;
    }

private:
    static std::string cache_directory_;

    /**
     * Create cache directory if it doesn't exist.
     */
    static void create_cache_directory() {
#ifdef _WIN32
        _mkdir(cache_directory_.c_str());
#else
        mkdir(cache_directory_.c_str(), 0755);
#endif
    }

    /**
     * Load global wisdom file.
     */
    static void load_global_wisdom() {
        std::string global_wisdom = cache_directory_ + "/global_wisdom.dat";
        if (import_wisdom(global_wisdom)) {
            std::cout << "[FFTW Cache] Loaded global wisdom from: " << global_wisdom << std::endl;
        }
    }

    /**
     * Save global wisdom file.
     */
    static void save_global_wisdom() {
        std::string global_wisdom = cache_directory_ + "/global_wisdom.dat";
        if (export_wisdom(global_wisdom)) {
            std::cout << "[FFTW Cache] Saved global wisdom to: " << global_wisdom << std::endl;
        }
    }

    /**
     * Generate wisdom cache key for 1D transform.
     */
    static std::string wisdom_key_1d(int n) {
        return "fft_1d_" + std::to_string(n);
    }

    /**
     * Generate wisdom cache key for 2D transform.
     */
    static std::string wisdom_key_2d(int nx, int ny) {
        return "fft_2d_" + std::to_string(nx) + "x" + std::to_string(ny);
    }

    /**
     * Generate wisdom cache key for 3D transform.
     */
    static std::string wisdom_key_3d(int nx, int ny, int nz) {
        return "fft_3d_" + std::to_string(nx) + "x" + std::to_string(ny) + "x" + std::to_string(nz);
    }

    /**
     * Create plan with caching logic.
     *
     * @param key Wisdom cache key
     * @param plan_func Function to create plan if cache miss
     * @return FFTW plan
     */
    template<typename PlanFunc>
    static fftw_plan create_plan_with_cache(const std::string& key, PlanFunc plan_func) {
        // Try to load wisdom for this specific transform
        std::string wisdom_file = cache_directory_ + "/" + key + ".dat";
        bool wisdom_loaded = import_wisdom(wisdom_file);

        fftw_plan plan = nullptr;

        if (wisdom_loaded) {
            // Try to create plan using wisdom only (no planning)
            // This requires temporarily setting FFTW_WISDOM_ONLY flag
            // Note: For simplicity, we just proceed with normal planning
            // which will use the loaded wisdom if available
        }

        // Create plan (will use wisdom if available, or plan from scratch)
        plan = plan_func();

        if (plan && !wisdom_loaded) {
            // Save wisdom for future use
            export_wisdom(wisdom_file);
            std::cout << "[FFTW Cache] Saved wisdom: " << key << std::endl;
        } else if (plan && wisdom_loaded) {
            std::cout << "[FFTW Cache] Used cached wisdom: " << key << std::endl;
        }

        return plan;
    }
};

// Static member initialization
std::string FFTWWisdomCache::cache_directory_ = "./cache/fftw_wisdom";

} // namespace dase

#endif // FFTW_WISDOM_CACHE_HPP
