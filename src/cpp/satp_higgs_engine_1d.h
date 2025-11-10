/**
 * SATP+Higgs Coupled Field Engine - 1D Implementation
 *
 * Simulates coupled evolution of:
 * - φ: Scale field (SATP)
 * - h: Higgs field with spontaneous symmetry breaking
 *
 * Physics:
 * ∂²φ/∂t² = c²∇²φ - γ_φ ∂φ/∂t - 2λφh² + S(t,x)
 * ∂²h/∂t² = c²∇²h - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
 */

#pragma once

#include <algorithm>
#include <atomic>
#include <cmath>
#include <complex>
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace satp_higgs {

// SATP+Higgs node with velocity storage for wave equations
struct SATPHiggsNode {
    double phi;      // Scale field value
    double phi_dot;  // Scale field velocity ∂φ/∂t
    double h;        // Higgs field value
    double h_dot;    // Higgs field velocity ∂h/∂t

    // Derived quantities
    double energy_density;  // Total energy density
    double conformal_factor; // Ω = exp(φ)

    SATPHiggsNode()
        : phi(0.0), phi_dot(0.0), h(0.0), h_dot(0.0),
          energy_density(0.0), conformal_factor(1.0) {}

    void updateDerived() {
        conformal_factor = std::exp(phi);
        // Energy density: kinetic + gradient + potential terms
        energy_density = 0.5 * (phi_dot * phi_dot + h_dot * h_dot);
    }
};

// Physics parameters for SATP+Higgs system
struct SATPHiggsParams {
    double c;           // Wave speed (default: 1.0)
    double gamma_phi;   // Scale field dissipation (default: 0.0)
    double gamma_h;     // Higgs dissipation (default: 0.0)
    double lambda;      // φ-h coupling strength (default: 0.1)
    double mu_squared;  // Higgs mass² parameter (negative for SSB, default: -1.0)
    double lambda_h;    // Higgs self-coupling (default: 0.5)
    double h_vev;       // Higgs vacuum expectation value (computed from params)

    SATPHiggsParams()
        : c(1.0), gamma_phi(0.0), gamma_h(0.0),
          lambda(0.1), mu_squared(-1.0), lambda_h(0.5), h_vev(0.0) {
        updateVEV();
    }

    void updateVEV() {
        // h_vev = sqrt(-μ²/2λ_h) for Mexican hat potential
        if (mu_squared < 0.0 && lambda_h > 0.0) {
            h_vev = std::sqrt(-mu_squared / (2.0 * lambda_h));
        } else {
            h_vev = 0.0;
        }
    }
};

// Source function callback type
using SourceFunction = std::function<double(double t, double x, int index)>;

class SATPHiggsEngine1D {
private:
    // Lattice configuration
    size_t N;           // Number of lattice points
    double dx;          // Spatial step size
    double dt;          // Time step size

    // Field storage
    std::vector<SATPHiggsNode> nodes;
    std::vector<SATPHiggsNode> nodes_temp;  // Temporary storage for updates

    // Physics parameters
    SATPHiggsParams params;

    // Source term
    SourceFunction source_phi;  // External source for φ field
    bool has_source;

    // Simulation state
    double current_time;
    uint64_t step_count;

    // Thread safety
    mutable std::mutex state_mutex;
    std::atomic<bool> is_running;

    // Diagnostics
    std::atomic<uint64_t> total_updates;

public:
    SATPHiggsEngine1D(size_t num_nodes, double spatial_step, double time_step,
                      const SATPHiggsParams& physics_params)
        : N(num_nodes), dx(spatial_step), dt(time_step),
          nodes(num_nodes), nodes_temp(num_nodes),
          params(physics_params), has_source(false),
          current_time(0.0), step_count(0),
          is_running(false), total_updates(0) {

        params.updateVEV();

        // Initialize to Higgs VEV by default
        for (auto& node : nodes) {
            node.h = params.h_vev;
            node.updateDerived();
        }
    }

    // Getters
    size_t getN() const { return N; }
    double getDx() const { return dx; }
    double getDt() const { return dt; }
    double getTime() const { return current_time; }
    uint64_t getStepCount() const { return step_count; }
    const SATPHiggsParams& getParams() const { return params; }
    const std::vector<SATPHiggsNode>& getNodes() const { return nodes; }
    std::vector<SATPHiggsNode>& getNodesMutable() { return nodes; }

    // Source term management
    void setSource(SourceFunction func) {
        source_phi = func;
        has_source = true;
    }

    void clearSource() {
        has_source = false;
        source_phi = nullptr;
    }

    // State management
    void reset() {
        std::lock_guard<std::mutex> lock(state_mutex);
        current_time = 0.0;
        step_count = 0;
        total_updates.store(0);
        for (auto& node : nodes) {
            node.phi = 0.0;
            node.phi_dot = 0.0;
            node.h = params.h_vev;
            node.h_dot = 0.0;
            node.updateDerived();
        }
    }

    // Physics evolution (implemented in satp_higgs_physics_1d.h)
    void evolve(size_t num_steps);

    // Diagnostics
    double computeTotalEnergy() const {
        double total_E = 0.0;
        for (size_t i = 0; i < N; ++i) {
            const auto& node = nodes[i];

            // Kinetic energy
            double E_kin = 0.5 * (node.phi_dot * node.phi_dot + node.h_dot * node.h_dot);

            // Gradient energy (finite difference)
            size_t i_next = (i + 1) % N;
            double dphi_dx = (nodes[i_next].phi - node.phi) / dx;
            double dh_dx = (nodes[i_next].h - node.h) / dx;
            double E_grad = 0.5 * params.c * params.c * (dphi_dx * dphi_dx + dh_dx * dh_dx);

            // Higgs potential
            double h_val = node.h;
            double V_higgs = params.mu_squared * h_val * h_val
                           + params.lambda_h * h_val * h_val * h_val * h_val;

            // Coupling energy
            double V_coupling = params.lambda * node.phi * node.phi * h_val * h_val;

            total_E += (E_kin + E_grad + V_higgs + V_coupling) * dx;
        }
        return total_E;
    }

    double computePhiRMS() const {
        double sum = 0.0;
        for (const auto& node : nodes) {
            sum += node.phi * node.phi;
        }
        return std::sqrt(sum / static_cast<double>(N));
    }

    double computeHiggsRMS() const {
        double sum = 0.0;
        for (const auto& node : nodes) {
            double h_deviation = node.h - params.h_vev;
            sum += h_deviation * h_deviation;
        }
        return std::sqrt(sum / static_cast<double>(N));
    }

    void getCenterOfMass(double& x_cm_phi, double& x_cm_h) const {
        // Use circular statistics for toroidal topology
        double sum_phi = 0.0, sum_cos_phi = 0.0, sum_sin_phi = 0.0;
        double sum_h = 0.0, sum_cos_h = 0.0, sum_sin_h = 0.0;

        for (size_t i = 0; i < N; ++i) {
            double theta = 2.0 * M_PI * static_cast<double>(i) / static_cast<double>(N);
            double weight_phi = std::abs(nodes[i].phi);
            double weight_h = std::abs(nodes[i].h - params.h_vev);

            sum_phi += weight_phi;
            sum_cos_phi += weight_phi * std::cos(theta);
            sum_sin_phi += weight_phi * std::sin(theta);

            sum_h += weight_h;
            sum_cos_h += weight_h * std::cos(theta);
            sum_sin_h += weight_h * std::sin(theta);
        }

        if (sum_phi > 1e-12) {
            double mean_theta_phi = std::atan2(sum_sin_phi, sum_cos_phi);
            x_cm_phi = static_cast<double>(N) * mean_theta_phi / (2.0 * M_PI);
            if (x_cm_phi < 0.0) x_cm_phi += static_cast<double>(N);
        } else {
            x_cm_phi = 0.0;
        }

        if (sum_h > 1e-12) {
            double mean_theta_h = std::atan2(sum_sin_h, sum_cos_h);
            x_cm_h = static_cast<double>(N) * mean_theta_h / (2.0 * M_PI);
            if (x_cm_h < 0.0) x_cm_h += static_cast<double>(N);
        } else {
            x_cm_h = 0.0;
        }
    }
};

} // namespace satp_higgs
} // namespace dase
