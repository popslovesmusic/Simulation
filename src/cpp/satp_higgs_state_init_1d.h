/**
 * SATP+Higgs State Initialization - 1D Profiles
 *
 * Initialization functions for φ and h fields including:
 * - Higgs VEV baseline
 * - Gaussian pulses
 * - Plane waves
 * - Three-zone source configurations
 */

#pragma once

#include "satp_higgs_engine_1d.h"
#include <algorithm>
#include <cmath>
#include <random>
#include <string>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace satp_higgs {

inline constexpr double MIN_SIGMA_SATP = 1.0e-9;

struct GaussianProfileParams {
    double amplitude;
    double center;
    double sigma;
    bool set_velocity;
    double velocity_amplitude;
    std::string mode;  // "overwrite", "add", "blend"
    double beta;       // Blend factor for mode="blend"

    GaussianProfileParams()
        : amplitude(1.0), center(0.0), sigma(1.0),
          set_velocity(false), velocity_amplitude(0.0),
          mode("overwrite"), beta(1.0) {}
};

struct ThreeZoneSourceParams {
    double zone1_start, zone1_end;  // Zone 1 boundaries
    double zone2_start, zone2_end;  // Zone 2 boundaries
    double zone3_start, zone3_end;  // Zone 3 boundaries
    double amplitude1, amplitude2, amplitude3;
    double frequency;  // Temporal oscillation frequency
    double t_start;    // When to start source
    double t_end;      // When to stop source (-1 = never stop)

    ThreeZoneSourceParams()
        : zone1_start(0.0), zone1_end(0.0),
          zone2_start(0.0), zone2_end(0.0),
          zone3_start(0.0), zone3_end(0.0),
          amplitude1(0.0), amplitude2(0.0), amplitude3(0.0),
          frequency(0.0), t_start(0.0), t_end(-1.0) {}
};

class SATPHiggsStateInit1D {
public:
    // Initialize to Higgs vacuum (VEV baseline)
    static void initVacuum(SATPHiggsEngine1D& engine) {
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

    // Initialize φ field with Gaussian profile
    static void initPhiGaussian(SATPHiggsEngine1D& engine,
                                 const GaussianProfileParams& params) {
        auto& nodes = engine.getNodesMutable();
        size_t N = engine.getN();
        double dx = engine.getDx();

        const double sigma = std::max(params.sigma, MIN_SIGMA_SATP);
        const double inv_two_sigma_sq = 1.0 / (2.0 * sigma * sigma);

        for (size_t i = 0; i < N; ++i) {
            double x = static_cast<double>(i) * dx;
            double dx_val = x - params.center;

            // Handle periodic boundary for distance calculation
            double L = static_cast<double>(N) * dx;
            if (dx_val > L / 2.0) dx_val -= L;
            if (dx_val < -L / 2.0) dx_val += L;

            double exponent = -(dx_val * dx_val) * inv_two_sigma_sq;
            double gaussian = params.amplitude * std::exp(exponent);

            if (params.mode == "add") {
                nodes[i].phi += gaussian;
                if (params.set_velocity) {
                    nodes[i].phi_dot += params.velocity_amplitude * std::exp(exponent);
                }
            } else if (params.mode == "blend") {
                nodes[i].phi = params.beta * gaussian + (1.0 - params.beta) * nodes[i].phi;
                if (params.set_velocity) {
                    double vel = params.velocity_amplitude * std::exp(exponent);
                    nodes[i].phi_dot = params.beta * vel + (1.0 - params.beta) * nodes[i].phi_dot;
                }
            } else {  // overwrite
                nodes[i].phi = gaussian;
                if (params.set_velocity) {
                    nodes[i].phi_dot = params.velocity_amplitude * std::exp(exponent);
                } else {
                    nodes[i].phi_dot = 0.0;
                }
            }

            nodes[i].updateDerived();
        }
    }

    // Initialize h field with Gaussian perturbation around VEV
    static void initHiggsGaussian(SATPHiggsEngine1D& engine,
                                   const GaussianProfileParams& params) {
        auto& nodes = engine.getNodesMutable();
        size_t N = engine.getN();
        double dx = engine.getDx();
        double h_vev = engine.getParams().h_vev;

        const double sigma = std::max(params.sigma, MIN_SIGMA_SATP);
        const double inv_two_sigma_sq = 1.0 / (2.0 * sigma * sigma);

        for (size_t i = 0; i < N; ++i) {
            double x = static_cast<double>(i) * dx;
            double dx_val = x - params.center;

            // Handle periodic boundary
            double L = static_cast<double>(N) * dx;
            if (dx_val > L / 2.0) dx_val -= L;
            if (dx_val < -L / 2.0) dx_val += L;

            double exponent = -(dx_val * dx_val) * inv_two_sigma_sq;
            double gaussian = params.amplitude * std::exp(exponent);

            if (params.mode == "add") {
                nodes[i].h += gaussian;
                if (params.set_velocity) {
                    nodes[i].h_dot += params.velocity_amplitude * std::exp(exponent);
                }
            } else if (params.mode == "blend") {
                double h_target = h_vev + gaussian;
                nodes[i].h = params.beta * h_target + (1.0 - params.beta) * nodes[i].h;
                if (params.set_velocity) {
                    double vel = params.velocity_amplitude * std::exp(exponent);
                    nodes[i].h_dot = params.beta * vel + (1.0 - params.beta) * nodes[i].h_dot;
                }
            } else {  // overwrite
                nodes[i].h = h_vev + gaussian;
                if (params.set_velocity) {
                    nodes[i].h_dot = params.velocity_amplitude * std::exp(exponent);
                } else {
                    nodes[i].h_dot = 0.0;
                }
            }

            nodes[i].updateDerived();
        }
    }

    // Create three-zone source function
    static SourceFunction createThreeZoneSource(const ThreeZoneSourceParams& params,
                                                 double dx) {
        // Capture parameters by value
        return [params, dx](double t, double x, int index) -> double {
            // Check if source is active
            if (t < params.t_start) return 0.0;
            if (params.t_end > 0.0 && t > params.t_end) return 0.0;

            // Determine which zone we're in
            double amplitude = 0.0;
            if (x >= params.zone1_start && x <= params.zone1_end) {
                amplitude = params.amplitude1;
            } else if (x >= params.zone2_start && x <= params.zone2_end) {
                amplitude = params.amplitude2;
            } else if (x >= params.zone3_start && x <= params.zone3_end) {
                amplitude = params.amplitude3;
            }

            // Apply temporal oscillation
            if (params.frequency > 0.0) {
                amplitude *= std::sin(2.0 * M_PI * params.frequency * t);
            }

            return amplitude;
        };
    }

    // Initialize uniform state
    static void initUniform(SATPHiggsEngine1D& engine,
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
    static void addRandomPerturbation(SATPHiggsEngine1D& engine,
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

    // Initialize plane wave
    static void initPlaneWave(SATPHiggsEngine1D& engine,
                             double amplitude, double wavelength,
                             double phase_offset,
                             bool for_phi_field = true) {
        auto& nodes = engine.getNodesMutable();
        size_t N = engine.getN();
        double dx = engine.getDx();
        double k = 2.0 * M_PI / wavelength;

        for (size_t i = 0; i < N; ++i) {
            double x = static_cast<double>(i) * dx;
            double value = amplitude * std::sin(k * x + phase_offset);

            if (for_phi_field) {
                nodes[i].phi = value;
            } else {
                double h_vev = engine.getParams().h_vev;
                nodes[i].h = h_vev + value;
            }
            nodes[i].updateDerived();
        }
    }

    // Reset to vacuum
    static void reset(SATPHiggsEngine1D& engine) {
        engine.reset();
    }
};

} // namespace satp_higgs
} // namespace dase
