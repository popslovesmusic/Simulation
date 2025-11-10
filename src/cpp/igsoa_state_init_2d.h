/**
 * IGSOA State Initialization - 2D Profiles
 *
 * Provides state initialization functions for 2D IGSOA simulations.
 * Supports Gaussian packets, plane waves, and custom profiles.
 */

#pragma once

#include "igsoa_complex_node.h"
#include "igsoa_complex_engine_2d.h"
#include <vector>
#include <cmath>
#include <complex>

// Define M_PI for MSVC
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace igsoa {

// Named constants (avoid magic numbers)
inline constexpr double MIN_SIGMA_2D = 1.0e-9;          // Minimum allowed sigma
inline constexpr double NORMALIZE_THRESHOLD_2D = 1.0e-15;  // Normalization threshold
inline constexpr double DEFAULT_RC_2D = 1.0e-34;        // Default causal radius (effectively 0)

/**
 * 2D Gaussian Profile Parameters
 */
struct Gaussian2DParams {
    double amplitude;      // Peak amplitude
    double center_x;       // X-coordinate of center (lattice units)
    double center_y;       // Y-coordinate of center (lattice units)
    double sigma_x;        // Width in x-direction
    double sigma_y;        // Width in y-direction
    double baseline_phi;   // Background Φ value
    std::string mode;      // "overwrite", "add", or "blend"
    double beta;           // Blend factor (0-1) for "blend" mode
};

/**
 * 2D Plane Wave Parameters
 */
struct PlaneWave2DParams {
    double amplitude;      // Wave amplitude
    double k_x;            // Wavenumber in x-direction
    double k_y;            // Wavenumber in y-direction
    double phase_offset;   // Phase offset (radians)
};

/**
 * IGSOA State Initialization - 2D
 */
class IGSOAStateInit2D {
public:
    /**
     * Initialize 2D Gaussian profile
     *
     * Ψ(x,y) = A * exp(-((x-x₀)²/(2σ_x²) + (y-y₀)²/(2σ_y²)))
     *
     * Supports three modes:
     * - overwrite: Replace existing state with Gaussian
     * - add: Add Gaussian to existing state (perturbation)
     * - blend: Interpolate between existing state and Gaussian
     *
     * @param engine 2D IGSOA engine
     * @param params Gaussian parameters
     */
    static void initGaussian2D(
        IGSOAComplexEngine2D& engine,
        const Gaussian2DParams& params
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();

        auto& nodes = engine.getNodesMutable();

        for (size_t y = 0; y < N_y; y++) {
            for (size_t x = 0; x < N_x; x++) {
                size_t index = y * N_x + x;

                // Compute distance from center
                double dx = static_cast<double>(x) - params.center_x;
                double dy = static_cast<double>(y) - params.center_y;

                // Gaussian envelope
                double exponent = -(dx * dx) / (2.0 * params.sigma_x * params.sigma_x)
                                  -(dy * dy) / (2.0 * params.sigma_y * params.sigma_y);
                double gaussian_value = params.amplitude * std::exp(exponent);

                // New quantum state (real-valued Gaussian for now)
                std::complex<double> psi_new(gaussian_value, 0.0);

                // Apply mode
                if (params.mode == "overwrite") {
                    // Replace existing state
                    nodes[index].psi = psi_new;
                    nodes[index].phi = params.baseline_phi;
                }
                else if (params.mode == "add") {
                    // Add to existing state (perturbation)
                    nodes[index].psi += psi_new;
                    // Φ unchanged
                }
                else if (params.mode == "blend") {
                    // Interpolate: Ψ_final = β*Ψ_new + (1-β)*Ψ_old
                    double beta = params.beta;
                    nodes[index].psi = beta * psi_new + (1.0 - beta) * nodes[index].psi;
                    nodes[index].phi = beta * params.baseline_phi + (1.0 - beta) * nodes[index].phi;
                }

                // Update derived quantities
                nodes[index].updateInformationalDensity();
                nodes[index].updatePhase();
            }
        }
    }

    /**
     * Initialize 2D plane wave
     *
     * Ψ(x,y) = A * exp(i(k_x*x + k_y*y + φ₀))
     *
     * @param engine 2D IGSOA engine
     * @param params Plane wave parameters
     */
    static void initPlaneWave2D(
        IGSOAComplexEngine2D& engine,
        const PlaneWave2DParams& params
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();

        auto& nodes = engine.getNodesMutable();

        for (size_t y = 0; y < N_y; y++) {
            for (size_t x = 0; x < N_x; x++) {
                size_t index = y * N_x + x;

                // Compute phase: φ = k_x*x + k_y*y + φ₀
                double phase = params.k_x * static_cast<double>(x)
                             + params.k_y * static_cast<double>(y)
                             + params.phase_offset;

                // Ψ = A * exp(iφ)
                nodes[index].psi = params.amplitude * std::exp(std::complex<double>(0.0, phase));

                // Update derived quantities
                nodes[index].updateInformationalDensity();
                nodes[index].updatePhase();
            }
        }
    }

    /**
     * Initialize uniform state
     *
     * Sets all nodes to the same Ψ and Φ values.
     *
     * @param engine 2D IGSOA engine
     * @param psi_real Real part of Ψ
     * @param psi_imag Imaginary part of Ψ
     * @param phi Value of Φ
     */
    static void initUniform(
        IGSOAComplexEngine2D& engine,
        double psi_real,
        double psi_imag,
        double phi
    ) {
        auto& nodes = engine.getNodesMutable();

        for (auto& node : nodes) {
            node.psi = std::complex<double>(psi_real, psi_imag);
            node.phi = phi;
            node.updateInformationalDensity();
            node.updatePhase();
        }
    }

    /**
     * Initialize random state
     *
     * Sets random Ψ values with uniform distribution.
     *
     * @param engine 2D IGSOA engine
     * @param amplitude_max Maximum amplitude of random values
     * @param seed Random seed (0 = use time)
     */
    static void initRandom(
        IGSOAComplexEngine2D& engine,
        double amplitude_max,
        unsigned int seed = 0
    ) {
        if (seed == 0) {
            seed = static_cast<unsigned int>(std::time(nullptr));
        }

        std::srand(seed);

        auto& nodes = engine.getNodesMutable();

        for (auto& node : nodes) {
            // Random complex number with magnitude <= amplitude_max
            double magnitude = amplitude_max * (static_cast<double>(std::rand()) / RAND_MAX);
            double phase = 2.0 * M_PI * (static_cast<double>(std::rand()) / RAND_MAX);

            node.psi = magnitude * std::exp(std::complex<double>(0.0, phase));
            node.phi = 0.0;  // Start with Φ = 0
            node.updateInformationalDensity();
            node.updatePhase();
        }
    }

    /**
     * Initialize circular Gaussian (isotropic)
     *
     * Special case where σ_x = σ_y = σ
     *
     * @param engine 2D IGSOA engine
     * @param amplitude Peak amplitude
     * @param center_x X-coordinate of center
     * @param center_y Y-coordinate of center
     * @param sigma Gaussian width (same in both directions)
     * @param baseline_phi Background Φ value
     * @param mode "overwrite", "add", or "blend"
     * @param beta Blend factor (for "blend" mode)
     */
    static void initCircularGaussian(
        IGSOAComplexEngine2D& engine,
        double amplitude,
        double center_x,
        double center_y,
        double sigma,
        double baseline_phi = 0.0,
        const std::string& mode = "overwrite",
        double beta = 1.0
    ) {
        Gaussian2DParams params;
        params.amplitude = amplitude;
        params.center_x = center_x;
        params.center_y = center_y;
        params.sigma_x = sigma;
        params.sigma_y = sigma;
        params.baseline_phi = baseline_phi;
        params.mode = mode;
        params.beta = beta;

        initGaussian2D(engine, params);
    }

    /**
     * Compute center of mass of |Ψ|² distribution
     *
     * Returns (x_cm, y_cm) weighted by informational density F = |Ψ|²
     *
     * @param engine 2D IGSOA engine
     * @param x_cm_out Output: X-coordinate of center of mass
     * @param y_cm_out Output: Y-coordinate of center of mass
     */
    static void computeCenterOfMass(
        const IGSOAComplexEngine2D& engine,
        double& x_cm_out,
        double& y_cm_out
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();

        const auto& nodes = engine.getNodes();

        double sum_F = 0.0;
        // Use circular statistics for toroidal topology
        double sum_cos_x = 0.0;
        double sum_sin_x = 0.0;
        double sum_cos_y = 0.0;
        double sum_sin_y = 0.0;

        for (size_t y = 0; y < N_y; y++) {
            for (size_t x = 0; x < N_x; x++) {
                size_t index = y * N_x + x;
                double F = nodes[index].F;

                // Convert coordinates to angles on unit circle
                double theta_x = 2.0 * M_PI * static_cast<double>(x) / static_cast<double>(N_x);
                double theta_y = 2.0 * M_PI * static_cast<double>(y) / static_cast<double>(N_y);

                sum_F += F;
                sum_cos_x += F * std::cos(theta_x);
                sum_sin_x += F * std::sin(theta_x);
                sum_cos_y += F * std::cos(theta_y);
                sum_sin_y += F * std::sin(theta_y);
            }
        }

        if (sum_F > 0.0) {
            // Compute mean angle using atan2
            double mean_theta_x = std::atan2(sum_sin_x, sum_cos_x);
            double mean_theta_y = std::atan2(sum_sin_y, sum_cos_y);

            // Convert back to coordinates (ensure positive result)
            x_cm_out = static_cast<double>(N_x) * mean_theta_x / (2.0 * M_PI);
            if (x_cm_out < 0.0) x_cm_out += static_cast<double>(N_x);

            y_cm_out = static_cast<double>(N_y) * mean_theta_y / (2.0 * M_PI);
            if (y_cm_out < 0.0) y_cm_out += static_cast<double>(N_y);
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
        }
    }
};

} // namespace igsoa
} // namespace dase
