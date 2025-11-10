/**
 * SATP+Higgs Physics Evolution - Velocity Verlet Integration
 *
 * Implements second-order accurate symplectic integration for coupled wave equations:
 * ∂²φ/∂t² = c²∂²φ/∂x² - γ_φ ∂φ/∂t - 2λφh² + S(t,x)
 * ∂²h/∂t² = c²∂²h/∂x² - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
 */

#pragma once

#include "satp_higgs_engine_1d.h"
#include <cmath>

namespace dase {
namespace satp_higgs {

// Velocity Verlet implementation for wave equations
inline void SATPHiggsEngine1D::evolve(size_t num_steps) {
    is_running.store(true);

    const double c_sq = params.c * params.c;
    const double dx_sq = dx * dx;
    const double gamma_phi = params.gamma_phi;
    const double gamma_h = params.gamma_h;
    const double lambda = params.lambda;
    const double mu_sq = params.mu_squared;
    const double lambda_h = params.lambda_h;

    for (size_t step = 0; step < num_steps; ++step) {
        // Velocity Verlet: x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
        //                  v(t+dt) = v(t) + 0.5*[a(t) + a(t+dt)]*dt

        // Step 1: Compute accelerations at t
        std::vector<double> phi_accel(N);
        std::vector<double> h_accel(N);

        for (size_t i = 0; i < N; ++i) {
            size_t i_prev = (i == 0) ? N - 1 : i - 1;
            size_t i_next = (i + 1) % N;

            const auto& node_prev = nodes[i_prev];
            const auto& node = nodes[i];
            const auto& node_next = nodes[i_next];

            // Laplacian using second-order finite differences
            double laplacian_phi = (node_prev.phi - 2.0 * node.phi + node_next.phi) / dx_sq;
            double laplacian_h = (node_prev.h - 2.0 * node.h + node_next.h) / dx_sq;

            // Source term for φ field
            double source_term = 0.0;
            if (has_source) {
                double x_pos = static_cast<double>(i) * dx;
                source_term = source_phi(current_time, x_pos, static_cast<int>(i));
            }

            // φ equation: ∂²φ/∂t² = c²∇²φ - γ_φ ∂φ/∂t - 2λφh² + S(t,x)
            phi_accel[i] = c_sq * laplacian_phi
                         - gamma_phi * node.phi_dot
                         - 2.0 * lambda * node.phi * node.h * node.h
                         + source_term;

            // h equation: ∂²h/∂t² = c²∇²h - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
            h_accel[i] = c_sq * laplacian_h
                       - gamma_h * node.h_dot
                       - 2.0 * mu_sq * node.h
                       - 4.0 * lambda_h * node.h * node.h * node.h
                       - 2.0 * lambda * node.phi * node.phi * node.h;
        }

        // Step 2: Update positions and half-step velocities
        for (size_t i = 0; i < N; ++i) {
            auto& node = nodes_temp[i];
            node = nodes[i];

            // Position update: φ(t+dt) = φ(t) + φ̇(t)*dt + 0.5*a_φ(t)*dt²
            node.phi = node.phi + node.phi_dot * dt + 0.5 * phi_accel[i] * dt * dt;
            node.h = node.h + node.h_dot * dt + 0.5 * h_accel[i] * dt * dt;

            // Half-step velocity update: φ̇(t+½dt) = φ̇(t) + 0.5*a_φ(t)*dt
            node.phi_dot = node.phi_dot + 0.5 * phi_accel[i] * dt;
            node.h_dot = node.h_dot + 0.5 * h_accel[i] * dt;
        }

        // Step 3: Compute accelerations at t+dt
        std::vector<double> phi_accel_new(N);
        std::vector<double> h_accel_new(N);

        for (size_t i = 0; i < N; ++i) {
            size_t i_prev = (i == 0) ? N - 1 : i - 1;
            size_t i_next = (i + 1) % N;

            const auto& node_prev = nodes_temp[i_prev];
            const auto& node = nodes_temp[i];
            const auto& node_next = nodes_temp[i_next];

            // Laplacian at t+dt
            double laplacian_phi = (node_prev.phi - 2.0 * node.phi + node_next.phi) / dx_sq;
            double laplacian_h = (node_prev.h - 2.0 * node.h + node_next.h) / dx_sq;

            // Source term at t+dt
            double source_term = 0.0;
            if (has_source) {
                double x_pos = static_cast<double>(i) * dx;
                double t_new = current_time + dt;
                source_term = source_phi(t_new, x_pos, static_cast<int>(i));
            }

            // Accelerations at t+dt
            phi_accel_new[i] = c_sq * laplacian_phi
                             - gamma_phi * node.phi_dot
                             - 2.0 * lambda * node.phi * node.h * node.h
                             + source_term;

            h_accel_new[i] = c_sq * laplacian_h
                           - gamma_h * node.h_dot
                           - 2.0 * mu_sq * node.h
                           - 4.0 * lambda_h * node.h * node.h * node.h
                           - 2.0 * lambda * node.phi * node.phi * node.h;
        }

        // Step 4: Complete velocity update using average acceleration
        for (size_t i = 0; i < N; ++i) {
            nodes_temp[i].phi_dot = nodes_temp[i].phi_dot + 0.5 * phi_accel_new[i] * dt;
            nodes_temp[i].h_dot = nodes_temp[i].h_dot + 0.5 * h_accel_new[i] * dt;

            // Update derived quantities
            nodes_temp[i].updateDerived();
        }

        // Step 5: Swap buffers
        nodes.swap(nodes_temp);

        // Update simulation state
        current_time += dt;
        step_count++;
        total_updates.fetch_add(N, std::memory_order_relaxed);
    }

    is_running.store(false);
}

// CFL stability check
inline bool checkCFLStability(double c, double dx, double dt) {
    double cfl_number = c * dt / dx;
    // For wave equation, CFL condition is: c*dt/dx ≤ 1
    return cfl_number <= 1.0;
}

inline double computeMaxStableTimestep(double c, double dx) {
    // Maximum stable timestep: dt = dx/c (with safety factor)
    const double safety_factor = 0.95;
    return safety_factor * dx / c;
}

} // namespace satp_higgs
} // namespace dase
