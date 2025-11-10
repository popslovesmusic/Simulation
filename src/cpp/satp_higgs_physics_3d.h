/**
 * SATP+Higgs Physics Evolution - 3D Velocity Verlet Integration
 *
 * Implements second-order accurate symplectic integration for coupled wave equations on 3D torus:
 * ∂²φ/∂t² = c²∇²φ - γ_φ ∂φ/∂t - 2λφh² + S(t,x,y,z)
 * ∂²h/∂t² = c²∇²h - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
 *
 * 3D Laplacian: ∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z²
 */

#pragma once

#include "satp_higgs_engine_3d.h"
#include <cmath>

namespace dase {
namespace satp_higgs {

// Velocity Verlet implementation for 3D wave equations
inline void SATPHiggsEngine3D::evolve(size_t num_steps) {
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
        std::vector<double> phi_accel(N_x * N_y * N_z);
        std::vector<double> h_accel(N_x * N_y * N_z);

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t idx = getIndex(x, y, z);

                    // Neighbor indices (periodic boundaries)
                    size_t x_prev = (x == 0) ? N_x - 1 : x - 1;
                    size_t x_next = (x + 1) % N_x;
                    size_t y_prev = (y == 0) ? N_y - 1 : y - 1;
                    size_t y_next = (y + 1) % N_y;
                    size_t z_prev = (z == 0) ? N_z - 1 : z - 1;
                    size_t z_next = (z + 1) % N_z;

                    size_t idx_xprev = getIndex(x_prev, y, z);
                    size_t idx_xnext = getIndex(x_next, y, z);
                    size_t idx_yprev = getIndex(x, y_prev, z);
                    size_t idx_ynext = getIndex(x, y_next, z);
                    size_t idx_zprev = getIndex(x, y, z_prev);
                    size_t idx_znext = getIndex(x, y, z_next);

                    const auto& node = nodes[idx];
                    const auto& node_xprev = nodes[idx_xprev];
                    const auto& node_xnext = nodes[idx_xnext];
                    const auto& node_yprev = nodes[idx_yprev];
                    const auto& node_ynext = nodes[idx_ynext];
                    const auto& node_zprev = nodes[idx_zprev];
                    const auto& node_znext = nodes[idx_znext];

                    // 3D Laplacian using 7-point stencil
                    // ∇²f = (f_{i-1,j,k} + f_{i+1,j,k} + f_{i,j-1,k} + f_{i,j+1,k} + f_{i,j,k-1} + f_{i,j,k+1} - 6f_{i,j,k}) / dx²
                    double laplacian_phi = (node_xprev.phi + node_xnext.phi +
                                           node_yprev.phi + node_ynext.phi +
                                           node_zprev.phi + node_znext.phi -
                                           6.0 * node.phi) / dx_sq;

                    double laplacian_h = (node_xprev.h + node_xnext.h +
                                         node_yprev.h + node_ynext.h +
                                         node_zprev.h + node_znext.h -
                                         6.0 * node.h) / dx_sq;

                    // Source term for φ field
                    double source_term = 0.0;
                    if (has_source) {
                        double x_pos = static_cast<double>(x) * dx;
                        double y_pos = static_cast<double>(y) * dx;
                        double z_pos = static_cast<double>(z) * dx;
                        source_term = source_phi(current_time, x_pos, y_pos, z_pos,
                                                static_cast<int>(x), static_cast<int>(y), static_cast<int>(z));
                    }

                    // φ equation: ∂²φ/∂t² = c²∇²φ - γ_φ ∂φ/∂t - 2λφh² + S(t,x,y,z)
                    phi_accel[idx] = c_sq * laplacian_phi
                                   - gamma_phi * node.phi_dot
                                   - 2.0 * lambda * node.phi * node.h * node.h
                                   + source_term;

                    // h equation: ∂²h/∂t² = c²∇²h - γ_h ∂h/∂t - 2μ²h - 4λ_h h³ - 2λφ²h
                    h_accel[idx] = c_sq * laplacian_h
                                 - gamma_h * node.h_dot
                                 - 2.0 * mu_sq * node.h
                                 - 4.0 * lambda_h * node.h * node.h * node.h
                                 - 2.0 * lambda * node.phi * node.phi * node.h;
                }
            }
        }

        // Step 2: Update positions and half-step velocities
        for (size_t i = 0; i < N_x * N_y * N_z; ++i) {
            auto& node = nodes_temp[i];
            node = nodes[i];

            // Position update
            node.phi = node.phi + node.phi_dot * dt + 0.5 * phi_accel[i] * dt * dt;
            node.h = node.h + node.h_dot * dt + 0.5 * h_accel[i] * dt * dt;

            // Half-step velocity update
            node.phi_dot = node.phi_dot + 0.5 * phi_accel[i] * dt;
            node.h_dot = node.h_dot + 0.5 * h_accel[i] * dt;
        }

        // Step 3: Compute accelerations at t+dt
        std::vector<double> phi_accel_new(N_x * N_y * N_z);
        std::vector<double> h_accel_new(N_x * N_y * N_z);

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t idx = getIndex(x, y, z);

                    // Neighbor indices
                    size_t x_prev = (x == 0) ? N_x - 1 : x - 1;
                    size_t x_next = (x + 1) % N_x;
                    size_t y_prev = (y == 0) ? N_y - 1 : y - 1;
                    size_t y_next = (y + 1) % N_y;
                    size_t z_prev = (z == 0) ? N_z - 1 : z - 1;
                    size_t z_next = (z + 1) % N_z;

                    size_t idx_xprev = getIndex(x_prev, y, z);
                    size_t idx_xnext = getIndex(x_next, y, z);
                    size_t idx_yprev = getIndex(x, y_prev, z);
                    size_t idx_ynext = getIndex(x, y_next, z);
                    size_t idx_zprev = getIndex(x, y, z_prev);
                    size_t idx_znext = getIndex(x, y, z_next);

                    const auto& node = nodes_temp[idx];
                    const auto& node_xprev = nodes_temp[idx_xprev];
                    const auto& node_xnext = nodes_temp[idx_xnext];
                    const auto& node_yprev = nodes_temp[idx_yprev];
                    const auto& node_ynext = nodes_temp[idx_ynext];
                    const auto& node_zprev = nodes_temp[idx_zprev];
                    const auto& node_znext = nodes_temp[idx_znext];

                    // 3D Laplacian at t+dt
                    double laplacian_phi = (node_xprev.phi + node_xnext.phi +
                                           node_yprev.phi + node_ynext.phi +
                                           node_zprev.phi + node_znext.phi -
                                           6.0 * node.phi) / dx_sq;

                    double laplacian_h = (node_xprev.h + node_xnext.h +
                                         node_yprev.h + node_ynext.h +
                                         node_zprev.h + node_znext.h -
                                         6.0 * node.h) / dx_sq;

                    // Source term at t+dt
                    double source_term = 0.0;
                    if (has_source) {
                        double x_pos = static_cast<double>(x) * dx;
                        double y_pos = static_cast<double>(y) * dx;
                        double z_pos = static_cast<double>(z) * dx;
                        double t_new = current_time + dt;
                        source_term = source_phi(t_new, x_pos, y_pos, z_pos,
                                                static_cast<int>(x), static_cast<int>(y), static_cast<int>(z));
                    }

                    // Accelerations at t+dt
                    phi_accel_new[idx] = c_sq * laplacian_phi
                                       - gamma_phi * node.phi_dot
                                       - 2.0 * lambda * node.phi * node.h * node.h
                                       + source_term;

                    h_accel_new[idx] = c_sq * laplacian_h
                                     - gamma_h * node.h_dot
                                     - 2.0 * mu_sq * node.h
                                     - 4.0 * lambda_h * node.h * node.h * node.h
                                     - 2.0 * lambda * node.phi * node.phi * node.h;
                }
            }
        }

        // Step 4: Complete velocity update using average acceleration
        for (size_t i = 0; i < N_x * N_y * N_z; ++i) {
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
        total_updates.fetch_add(N_x * N_y * N_z, std::memory_order_relaxed);
    }

    is_running.store(false);
}

// CFL stability check for 3D
inline bool checkCFLStability3D(double c, double dx, double dt) {
    // For 3D wave equation: c*dt/dx ≤ 1/√3 ≈ 0.577
    constexpr double cfl_limit_3d = 1.0 / 1.73205080757;  // 1/√3
    double cfl_number = c * dt / dx;
    return cfl_number <= cfl_limit_3d;
}

inline double computeMaxStableTimestep3D(double c, double dx) {
    // Maximum stable timestep for 3D
    constexpr double safety_factor = 0.95;
    constexpr double sqrt_3 = 1.73205080757;  // √3
    return safety_factor * dx / (c * sqrt_3);
}

} // namespace satp_higgs
} // namespace dase
