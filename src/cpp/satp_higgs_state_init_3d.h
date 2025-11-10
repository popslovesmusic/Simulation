/**
 * SATP+Higgs State Initialization - 3D Profiles
 *
 * Initialization functions for φ and h fields on 3D toroidal lattice including:
 * - Higgs VEV baseline
 * - Spherical Gaussian pulses
 * - Plane waves
 * - 3D source configurations
 */

#pragma once

#include "satp_higgs_engine_3d.h"
#include <algorithm>
#include <cmath>
#include <random>
#include <string>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace satp_higgs {

inline constexpr double MIN_SIGMA_SATP_3D = 1.0e-9;

struct GaussianProfile3DParams {
    double amplitude;
    double center_x, center_y, center_z;
    double sigma_x, sigma_y, sigma_z;  // Ellipsoidal Gaussian
    bool set_velocity;
    double velocity_amplitude;
    std::string mode;  // "overwrite", "add", "blend"
    double beta;

    GaussianProfile3DParams()
        : amplitude(1.0), center_x(0.0), center_y(0.0), center_z(0.0),
          sigma_x(1.0), sigma_y(1.0), sigma_z(1.0),
          set_velocity(false), velocity_amplitude(0.0),
          mode("overwrite"), beta(1.0) {}
};

class SATPHiggsStateInit3D {
public:
    // Initialize to Higgs vacuum (VEV baseline)
    static void initVacuum(SATPHiggsEngine3D& engine) {
        auto& nodes = engine.getNodesMutable();
        double h_vev = engine.getParams().h_vev;

        for (auto& node : nodes) {
            node.phi = 0.0;
            node.phi_dot = 0.0;
            node.h = h_vev;
            node.h_dot = 0.0;
            node.updateDerived();
        }
    }

    // Initialize φ field with spherical Gaussian
    static void initPhiSphericalGaussian(SATPHiggsEngine3D& engine,
                                          double amplitude,
                                          double center_x, double center_y, double center_z,
                                          double sigma,
                                          const std::string& mode = "overwrite") {
        GaussianProfile3DParams params;
        params.amplitude = amplitude;
        params.center_x = center_x;
        params.center_y = center_y;
        params.center_z = center_z;
        params.sigma_x = sigma;
        params.sigma_y = sigma;
        params.sigma_z = sigma;
        params.mode = mode;
        initPhiGaussian(engine, params);
    }

    // Initialize φ field with ellipsoidal Gaussian
    static void initPhiGaussian(SATPHiggsEngine3D& engine,
                                const GaussianProfile3DParams& params) {
        auto& nodes = engine.getNodesMutable();
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();
        size_t N_z = engine.getNz();
        double dx = engine.getDx();

        const double sigma_x = std::max(params.sigma_x, MIN_SIGMA_SATP_3D);
        const double sigma_y = std::max(params.sigma_y, MIN_SIGMA_SATP_3D);
        const double sigma_z = std::max(params.sigma_z, MIN_SIGMA_SATP_3D);
        const double inv_two_sigma_x_sq = 1.0 / (2.0 * sigma_x * sigma_x);
        const double inv_two_sigma_y_sq = 1.0 / (2.0 * sigma_y * sigma_y);
        const double inv_two_sigma_z_sq = 1.0 / (2.0 * sigma_z * sigma_z);

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t idx = engine.getIndex(x, y, z);

                    double x_pos = static_cast<double>(x) * dx;
                    double y_pos = static_cast<double>(y) * dx;
                    double z_pos = static_cast<double>(z) * dx;
                    double dx_val = x_pos - params.center_x;
                    double dy_val = y_pos - params.center_y;
                    double dz_val = z_pos - params.center_z;

                    // Handle periodic boundaries
                    double L_x = static_cast<double>(N_x) * dx;
                    double L_y = static_cast<double>(N_y) * dx;
                    double L_z = static_cast<double>(N_z) * dx;
                    if (dx_val > L_x / 2.0) dx_val -= L_x;
                    if (dx_val < -L_x / 2.0) dx_val += L_x;
                    if (dy_val > L_y / 2.0) dy_val -= L_y;
                    if (dy_val < -L_y / 2.0) dy_val += L_y;
                    if (dz_val > L_z / 2.0) dz_val -= L_z;
                    if (dz_val < -L_z / 2.0) dz_val += L_z;

                    double exponent = -(dx_val * dx_val) * inv_two_sigma_x_sq
                                     - (dy_val * dy_val) * inv_two_sigma_y_sq
                                     - (dz_val * dz_val) * inv_two_sigma_z_sq;
                    double gaussian = params.amplitude * std::exp(exponent);

                    if (params.mode == "add") {
                        nodes[idx].phi += gaussian;
                        if (params.set_velocity) {
                            nodes[idx].phi_dot += params.velocity_amplitude * std::exp(exponent);
                        }
                    } else if (params.mode == "blend") {
                        nodes[idx].phi = params.beta * gaussian + (1.0 - params.beta) * nodes[idx].phi;
                        if (params.set_velocity) {
                            double vel = params.velocity_amplitude * std::exp(exponent);
                            nodes[idx].phi_dot = params.beta * vel + (1.0 - params.beta) * nodes[idx].phi_dot;
                        }
                    } else {  // overwrite
                        nodes[idx].phi = gaussian;
                        if (params.set_velocity) {
                            nodes[idx].phi_dot = params.velocity_amplitude * std::exp(exponent);
                        } else {
                            nodes[idx].phi_dot = 0.0;
                        }
                    }

                    nodes[idx].updateDerived();
                }
            }
        }
    }

    // Initialize h field with spherical Gaussian perturbation around VEV
    static void initHiggsSphericalGaussian(SATPHiggsEngine3D& engine,
                                           double amplitude,
                                           double center_x, double center_y, double center_z,
                                           double sigma,
                                           const std::string& mode = "overwrite") {
        GaussianProfile3DParams params;
        params.amplitude = amplitude;
        params.center_x = center_x;
        params.center_y = center_y;
        params.center_z = center_z;
        params.sigma_x = sigma;
        params.sigma_y = sigma;
        params.sigma_z = sigma;
        params.mode = mode;
        initHiggsGaussian(engine, params);
    }

    // Initialize h field with Gaussian perturbation around VEV
    static void initHiggsGaussian(SATPHiggsEngine3D& engine,
                                   const GaussianProfile3DParams& params) {
        auto& nodes = engine.getNodesMutable();
        size_t N_x = engine.getNx();
        size_t N_y = engine.getNy();
        size_t N_z = engine.getNz();
        double dx = engine.getDx();
        double h_vev = engine.getParams().h_vev;

        const double sigma_x = std::max(params.sigma_x, MIN_SIGMA_SATP_3D);
        const double sigma_y = std::max(params.sigma_y, MIN_SIGMA_SATP_3D);
        const double sigma_z = std::max(params.sigma_z, MIN_SIGMA_SATP_3D);
        const double inv_two_sigma_x_sq = 1.0 / (2.0 * sigma_x * sigma_x);
        const double inv_two_sigma_y_sq = 1.0 / (2.0 * sigma_y * sigma_y);
        const double inv_two_sigma_z_sq = 1.0 / (2.0 * sigma_z * sigma_z);

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t idx = engine.getIndex(x, y, z);

                    double x_pos = static_cast<double>(x) * dx;
                    double y_pos = static_cast<double>(y) * dx;
                    double z_pos = static_cast<double>(z) * dx;
                    double dx_val = x_pos - params.center_x;
                    double dy_val = y_pos - params.center_y;
                    double dz_val = z_pos - params.center_z;

                    // Handle periodic boundaries
                    double L_x = static_cast<double>(N_x) * dx;
                    double L_y = static_cast<double>(N_y) * dx;
                    double L_z = static_cast<double>(N_z) * dx;
                    if (dx_val > L_x / 2.0) dx_val -= L_x;
                    if (dx_val < -L_x / 2.0) dx_val += L_x;
                    if (dy_val > L_y / 2.0) dy_val -= L_y;
                    if (dy_val < -L_y / 2.0) dy_val += L_y;
                    if (dz_val > L_z / 2.0) dz_val -= L_z;
                    if (dz_val < -L_z / 2.0) dz_val += L_z;

                    double exponent = -(dx_val * dx_val) * inv_two_sigma_x_sq
                                     - (dy_val * dy_val) * inv_two_sigma_y_sq
                                     - (dz_val * dz_val) * inv_two_sigma_z_sq;
                    double gaussian = params.amplitude * std::exp(exponent);

                    if (params.mode == "add") {
                        nodes[idx].h += gaussian;
                        if (params.set_velocity) {
                            nodes[idx].h_dot += params.velocity_amplitude * std::exp(exponent);
                        }
                    } else if (params.mode == "blend") {
                        double h_target = h_vev + gaussian;
                        nodes[idx].h = params.beta * h_target + (1.0 - params.beta) * nodes[idx].h;
                        if (params.set_velocity) {
                            double vel = params.velocity_amplitude * std::exp(exponent);
                            nodes[idx].h_dot = params.beta * vel + (1.0 - params.beta) * nodes[idx].h_dot;
                        }
                    } else {  // overwrite
                        nodes[idx].h = h_vev + gaussian;
                        if (params.set_velocity) {
                            nodes[idx].h_dot = params.velocity_amplitude * std::exp(exponent);
                        } else {
                            nodes[idx].h_dot = 0.0;
                        }
                    }

                    nodes[idx].updateDerived();
                }
            }
        }
    }

    // Initialize uniform state
    static void initUniform(SATPHiggsEngine3D& engine,
                           double phi_val, double phi_dot_val,
                           double h_val, double h_dot_val) {
        auto& nodes = engine.getNodesMutable();
        for (auto& node : nodes) {
            node.phi = phi_val;
            node.phi_dot = phi_dot_val;
            node.h = h_val;
            node.h_dot = h_dot_val;
            node.updateDerived();
        }
    }

    // Add random perturbations
    static void addRandomPerturbation(SATPHiggsEngine3D& engine,
                                      double phi_amplitude,
                                      double h_amplitude,
                                      unsigned int seed = 0) {
        std::mt19937_64 rng(seed == 0 ? std::random_device{}() : seed);
        std::uniform_real_distribution<double> dist(-1.0, 1.0);

        auto& nodes = engine.getNodesMutable();
        for (auto& node : nodes) {
            node.phi += phi_amplitude * dist(rng);
            node.h += h_amplitude * dist(rng);
            node.updateDerived();
        }
    }

    // Reset to vacuum
    static void reset(SATPHiggsEngine3D& engine) {
        engine.reset();
    }
};

} // namespace satp_higgs
} // namespace dase
