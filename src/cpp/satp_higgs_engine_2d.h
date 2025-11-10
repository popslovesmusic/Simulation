/**
 * SATP+Higgs Coupled Field Engine - 2D Implementation
 *
 * Simulates coupled evolution of φ and h fields on 2D toroidal lattice:
 * - φ: Scale field (SATP)
 * - h: Higgs field with spontaneous symmetry breaking
 *
 * Physics:
 * ∂²φ/∂t² = c²∇²φ - γ_φ ∂φ/∂t - 2λφh² + S(t,x,y)
 * ∂²h/∂t² = c²∇²h - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
 */

#pragma once

#include <algorithm>
#include <atomic>
#include <cmath>
#include <complex>
#include <cstdint>
#include <functional>
#include <mutex>
#include <string>
#include <vector>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace satp_higgs {

// Forward declarations
struct SATPHiggsParams;

// 2D source function: S(t, x, y, ix, iy)
using SourceFunction2D = std::function<double(double t, double x, double y, int ix, int iy)>;

class SATPHiggsEngine2D {
private:
    // Lattice configuration
    size_t N_x, N_y;    // Lattice dimensions
    double dx;          // Spatial step size
    double dt;          // Time step size

    // Field storage (flattened 2D array: index = y * N_x + x)
    std::vector<SATPHiggsNode> nodes;
    std::vector<SATPHiggsNode> nodes_temp;

    // Physics parameters
    SATPHiggsParams params;

    // Source term
    SourceFunction2D source_phi;
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
    SATPHiggsEngine2D(size_t nx, size_t ny, double spatial_step, double time_step,
                      const SATPHiggsParams& physics_params)
        : N_x(nx), N_y(ny), dx(spatial_step), dt(time_step),
          nodes(nx * ny), nodes_temp(nx * ny),
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
    size_t getNx() const { return N_x; }
    size_t getNy() const { return N_y; }
    size_t getN() const { return N_x * N_y; }
    double getDx() const { return dx; }
    double getDt() const { return dt; }
    double getTime() const { return current_time; }
    uint64_t getStepCount() const { return step_count; }
    const SATPHiggsParams& getParams() const { return params; }
    const std::vector<SATPHiggsNode>& getNodes() const { return nodes; }
    std::vector<SATPHiggsNode>& getNodesMutable() { return nodes; }

    // Index conversion
    size_t getIndex(size_t x, size_t y) const {
        return y * N_x + x;
    }

    void getCoords(size_t index, size_t& x, size_t& y) const {
        x = index % N_x;
        y = index / N_x;
    }

    // Source term management
    void setSource(SourceFunction2D func) {
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

    // Physics evolution (implemented in satp_higgs_physics_2d.h)
    void evolve(size_t num_steps);

    // Diagnostics
    double computeTotalEnergy() const {
        double total_E = 0.0;
        const double dx_sq = dx * dx;  // Area element

        for (size_t y = 0; y < N_y; ++y) {
            for (size_t x = 0; x < N_x; ++x) {
                size_t idx = getIndex(x, y);
                const auto& node = nodes[idx];

                // Kinetic energy
                double E_kin = 0.5 * (node.phi_dot * node.phi_dot + node.h_dot * node.h_dot);

                // Gradient energy (2D finite difference)
                size_t x_next = (x + 1) % N_x;
                size_t y_next = (y + 1) % N_y;
                size_t idx_xnext = getIndex(x_next, y);
                size_t idx_ynext = getIndex(x, y_next);

                double dphi_dx = (nodes[idx_xnext].phi - node.phi) / dx;
                double dphi_dy = (nodes[idx_ynext].phi - node.phi) / dx;
                double dh_dx = (nodes[idx_xnext].h - node.h) / dx;
                double dh_dy = (nodes[idx_ynext].h - node.h) / dx;

                double E_grad = 0.5 * params.c * params.c * (
                    dphi_dx * dphi_dx + dphi_dy * dphi_dy +
                    dh_dx * dh_dx + dh_dy * dh_dy
                );

                // Higgs potential
                double h_val = node.h;
                double V_higgs = params.mu_squared * h_val * h_val
                               + params.lambda_h * h_val * h_val * h_val * h_val;

                // Coupling energy
                double V_coupling = params.lambda * node.phi * node.phi * h_val * h_val;

                total_E += (E_kin + E_grad + V_higgs + V_coupling) * dx_sq;
            }
        }
        return total_E;
    }

    double computePhiRMS() const {
        double sum = 0.0;
        for (const auto& node : nodes) {
            sum += node.phi * node.phi;
        }
        return std::sqrt(sum / static_cast<double>(nodes.size()));
    }

    double computeHiggsRMS() const {
        double sum = 0.0;
        for (const auto& node : nodes) {
            double h_deviation = node.h - params.h_vev;
            sum += h_deviation * h_deviation;
        }
        return std::sqrt(sum / static_cast<double>(nodes.size()));
    }

    void getCenterOfMass(double& x_cm, double& y_cm) const {
        // Use circular statistics for toroidal topology
        double sum_phi = 0.0;
        double sum_cos_x = 0.0, sum_sin_x = 0.0;
        double sum_cos_y = 0.0, sum_sin_y = 0.0;

        for (size_t y = 0; y < N_y; ++y) {
            for (size_t x = 0; x < N_x; ++x) {
                size_t idx = getIndex(x, y);
                double weight = std::abs(nodes[idx].phi);

                double theta_x = 2.0 * M_PI * static_cast<double>(x) / static_cast<double>(N_x);
                double theta_y = 2.0 * M_PI * static_cast<double>(y) / static_cast<double>(N_y);

                sum_phi += weight;
                sum_cos_x += weight * std::cos(theta_x);
                sum_sin_x += weight * std::sin(theta_x);
                sum_cos_y += weight * std::cos(theta_y);
                sum_sin_y += weight * std::sin(theta_y);
            }
        }

        if (sum_phi > 1e-12) {
            double mean_theta_x = std::atan2(sum_sin_x, sum_cos_x);
            double mean_theta_y = std::atan2(sum_sin_y, sum_cos_y);

            x_cm = static_cast<double>(N_x) * mean_theta_x / (2.0 * M_PI);
            y_cm = static_cast<double>(N_y) * mean_theta_y / (2.0 * M_PI);

            if (x_cm < 0.0) x_cm += static_cast<double>(N_x);
            if (y_cm < 0.0) y_cm += static_cast<double>(N_y);
        } else {
            x_cm = 0.0;
            y_cm = 0.0;
        }
    }
};

} // namespace satp_higgs
} // namespace dase
