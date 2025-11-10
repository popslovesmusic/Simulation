/**
 * IGSOA State Initialization - 3D Profiles
 */

#pragma once

#include "igsoa_complex_engine_3d.h"
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <ctime>
#include <random>
#include <string>

// Define M_PI for MSVC
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace igsoa {

// Named constants (avoid magic numbers)
inline constexpr double MIN_SIGMA_3D = 1.0e-9;          // Minimum allowed sigma
inline constexpr double NORMALIZE_THRESHOLD_3D = 1.0e-15;  // Normalization threshold
inline constexpr double DEFAULT_RC_3D = 1.0e-34;        // Default causal radius (effectively 0)

struct Gaussian3DParams {
    double amplitude;
    double center_x;
    double center_y;
    double center_z;
    double sigma_x;
    double sigma_y;
    double sigma_z;
    double baseline_phi;
    std::string mode;
    double beta;
};

struct PlaneWave3DParams {
    double amplitude;
    double k_x;
    double k_y;
    double k_z;
    double phase_offset;
};

class IGSOAStateInit3D {
public:
    static void initGaussian3D(
        IGSOAComplexEngine3D& engine,
        const Gaussian3DParams& params
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();
        size_t N_z = engine.getNz();

        auto& nodes = engine.getNodesMutable();

        const double sigma_x = std::max(params.sigma_x, MIN_SIGMA_3D);
        const double sigma_y = std::max(params.sigma_y, MIN_SIGMA_3D);
        const double sigma_z = std::max(params.sigma_z, MIN_SIGMA_3D);
        const double inv_two_sigma_x_sq = 1.0 / (2.0 * sigma_x * sigma_x);
        const double inv_two_sigma_y_sq = 1.0 / (2.0 * sigma_y * sigma_y);
        const double inv_two_sigma_z_sq = 1.0 / (2.0 * sigma_z * sigma_z);
        const double baseline_phi = params.baseline_phi;
        const std::string& mode = params.mode;
        const double beta_clamped = std::clamp(params.beta, 0.0, 1.0);

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t index = z * N_x * N_y + y * N_x + x;

                    const double dx = static_cast<double>(x) - params.center_x;
                    const double dy = static_cast<double>(y) - params.center_y;
                    const double dz = static_cast<double>(z) - params.center_z;

                    const double exponent = -(
                        (dx * dx) * inv_two_sigma_x_sq +
                        (dy * dy) * inv_two_sigma_y_sq +
                        (dz * dz) * inv_two_sigma_z_sq
                    );

                    const double gaussian_value = params.amplitude * std::exp(exponent);
                    const std::complex<double> psi_new(gaussian_value, 0.0);

                    if (mode == "add") {
                        nodes[index].psi += psi_new;
                    } else if (mode == "blend") {
                        nodes[index].psi = beta_clamped * psi_new + (1.0 - beta_clamped) * nodes[index].psi;
                        nodes[index].phi = beta_clamped * baseline_phi + (1.0 - beta_clamped) * nodes[index].phi;
                    } else {
                        nodes[index].psi = psi_new;
                        nodes[index].phi = baseline_phi;
                    }

                    nodes[index].updateInformationalDensity();
                    nodes[index].updatePhase();
                }
            }
        }
    }

    static void initSphericalGaussian(
        IGSOAComplexEngine3D& engine,
        double amplitude,
        double center_x,
        double center_y,
        double center_z,
        double sigma,
        double baseline_phi = 0.0,
        const std::string& mode = "overwrite",
        double beta = 1.0
    ) {
        Gaussian3DParams params;
        params.amplitude = amplitude;
        params.center_x = center_x;
        params.center_y = center_y;
        params.center_z = center_z;
        params.sigma_x = sigma;
        params.sigma_y = sigma;
        params.sigma_z = sigma;
        params.baseline_phi = baseline_phi;
        params.mode = mode;
        params.beta = beta;
        initGaussian3D(engine, params);
    }

    static void initPlaneWave3D(
        IGSOAComplexEngine3D& engine,
        const PlaneWave3DParams& params
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();
        size_t N_z = engine.getNz();

        auto& nodes = engine.getNodesMutable();

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t index = z * N_x * N_y + y * N_x + x;
                    double phase = params.k_x * static_cast<double>(x)
                                   + params.k_y * static_cast<double>(y)
                                   + params.k_z * static_cast<double>(z)
                                   + params.phase_offset;
                    nodes[index].psi = params.amplitude * std::exp(std::complex<double>(0.0, phase));
                    nodes[index].updateInformationalDensity();
                    nodes[index].updatePhase();
                }
            }
        }
    }

    static void initUniform(
        IGSOAComplexEngine3D& engine,
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

    static void initRandom(
        IGSOAComplexEngine3D& engine,
        double amplitude_max,
        unsigned int seed = 0
    ) {
        const double max_amplitude = std::max(amplitude_max, 0.0);
        const double two_pi = 2.0 * M_PI;

        std::mt19937_64 rng(seed == 0 ? static_cast<uint64_t>(std::time(nullptr)) : static_cast<uint64_t>(seed));
        std::uniform_real_distribution<double> magnitude_dist(0.0, max_amplitude);
        std::uniform_real_distribution<double> phase_dist(0.0, two_pi);

        auto& nodes = engine.getNodesMutable();
        for (auto& node : nodes) {
            const double magnitude = magnitude_dist(rng);
            const double phase = phase_dist(rng);
            node.psi = magnitude * std::exp(std::complex<double>(0.0, phase));
            node.updateInformationalDensity();
            node.updatePhase();
        }
    }

    static void reset(IGSOAComplexEngine3D& engine) {
        engine.reset();
    }

    static void computeCenterOfMass(
        const IGSOAComplexEngine3D& engine,
        double& x_cm_out,
        double& y_cm_out,
        double& z_cm_out
    ) {
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();
        size_t N_z = engine.getNz();

        const auto& nodes = engine.getNodes();

        double sum_F = 0.0;
        // Use circular statistics for toroidal topology
        double sum_cos_x = 0.0;
        double sum_sin_x = 0.0;
        double sum_cos_y = 0.0;
        double sum_sin_y = 0.0;
        double sum_cos_z = 0.0;
        double sum_sin_z = 0.0;

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t index = z * N_x * N_y + y * N_x + x;
                    double F = nodes[index].F;

                    // Convert coordinates to angles on unit circle
                    double theta_x = 2.0 * M_PI * static_cast<double>(x) / static_cast<double>(N_x);
                    double theta_y = 2.0 * M_PI * static_cast<double>(y) / static_cast<double>(N_y);
                    double theta_z = 2.0 * M_PI * static_cast<double>(z) / static_cast<double>(N_z);

                    sum_F += F;
                    sum_cos_x += F * std::cos(theta_x);
                    sum_sin_x += F * std::sin(theta_x);
                    sum_cos_y += F * std::cos(theta_y);
                    sum_sin_y += F * std::sin(theta_y);
                    sum_cos_z += F * std::cos(theta_z);
                    sum_sin_z += F * std::sin(theta_z);
                }
            }
        }

        if (sum_F > 0.0) {
            // Compute mean angle using atan2
            double mean_theta_x = std::atan2(sum_sin_x, sum_cos_x);
            double mean_theta_y = std::atan2(sum_sin_y, sum_cos_y);
            double mean_theta_z = std::atan2(sum_sin_z, sum_cos_z);

            // Convert back to coordinates (ensure positive result)
            x_cm_out = static_cast<double>(N_x) * mean_theta_x / (2.0 * M_PI);
            if (x_cm_out < 0.0) x_cm_out += static_cast<double>(N_x);

            y_cm_out = static_cast<double>(N_y) * mean_theta_y / (2.0 * M_PI);
            if (y_cm_out < 0.0) y_cm_out += static_cast<double>(N_y);

            z_cm_out = static_cast<double>(N_z) * mean_theta_z / (2.0 * M_PI);
            if (z_cm_out < 0.0) z_cm_out += static_cast<double>(N_z);
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
            z_cm_out = 0.0;
        }
    }
};

} // namespace igsoa
} // namespace dase

