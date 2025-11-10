/**
 * IGSOA Physics Implementation - 3D Extension
 *
 * Extends the IGSOA evolution equations to a three-dimensional toroidal lattice.
 * Maintains the original causal coupling kernel while expanding neighbor
 * discovery to a spherical region within the causal radius R_c.
 */

#pragma once

#include "igsoa_complex_node.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <mutex>
#include <vector>

namespace dase {
namespace igsoa {

class IGSOAPhysics3D {
public:
    static inline double couplingKernel(double distance, double R_c) {
        if (distance <= 0.0 || R_c <= 0.0) return 0.0;
        return std::exp(-distance / R_c) / R_c;
    }

    static inline double wrappedDistance1D(int coord1, int coord2, size_t N) {
        int raw_dist = std::abs(coord1 - coord2);
        int wrapped_dist = std::min(raw_dist, static_cast<int>(N) - raw_dist);
        return static_cast<double>(wrapped_dist);
    }

    static inline double wrappedDistance3D(
        int x1, int y1, int z1,
        int x2, int y2, int z2,
        size_t N_x, size_t N_y, size_t N_z
    ) {
        double dx = wrappedDistance1D(x1, x2, N_x);
        double dy = wrappedDistance1D(y1, y2, N_y);
        double dz = wrappedDistance1D(z1, z2, N_z);
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    static uint64_t evolveQuantumState(
        std::vector<IGSOAComplexNode>& nodes,
        double dt,
        size_t N_x,
        size_t N_y,
        size_t N_z,
        double hbar = 1.0
    ) {
        const size_t N_total = N_x * N_y * N_z;
        const size_t plane_size = N_x * N_y;
        const int N_x_int = static_cast<int>(N_x);
        const int N_y_int = static_cast<int>(N_y);
        const int N_z_int = static_cast<int>(N_z);

        uint64_t neighbor_operations = 0;

        for (size_t index = 0; index < N_total; ++index) {
            auto& node = nodes[index];

            const int x_i = static_cast<int>(index % N_x);
            const int y_i = static_cast<int>((index / N_x) % N_y);
            const int z_i = static_cast<int>(index / plane_size);

            std::complex<double> V_eff = node.kappa * node.phi;
            std::complex<double> nonlocal_coupling(0.0, 0.0);

            // DIAGNOSTIC: Print once to verify this code path is active (thread-safe)
            static std::once_flag diagnostic_flag;
            if (index == 0) {
                std::call_once(diagnostic_flag, [&]() {
                    std::cerr << "[IGSOA 3D DIAGNOSTIC] Using 3D non-local coupling (" << N_x
                              << "x" << N_y << "x" << N_z << ", R_c=" << node.R_c << ")" << std::endl;
                });
            }

            if (N_total > 1) {
                const double radius = std::max(node.R_c, 0.0);
                if (radius > 0.0) {
                    const int R_c_int = static_cast<int>(std::ceil(radius));
                    const double radius_sq = radius * radius;

                    for (int dz = -R_c_int; dz <= R_c_int; ++dz) {
                        for (int dy = -R_c_int; dy <= R_c_int; ++dy) {
                            for (int dx = -R_c_int; dx <= R_c_int; ++dx) {
                                if (dx == 0 && dy == 0 && dz == 0) continue;

                                int x_j = (x_i + dx) % N_x_int;
                                if (x_j < 0) x_j += N_x_int;
                                int y_j = (y_i + dy) % N_y_int;
                                if (y_j < 0) y_j += N_y_int;
                                int z_j = (z_i + dz) % N_z_int;
                                if (z_j < 0) z_j += N_z_int;

                                const double dx_wrap = wrappedDistance1D(x_i, x_j, N_x);
                                const double dy_wrap = wrappedDistance1D(y_i, y_j, N_y);
                                const double dz_wrap = wrappedDistance1D(z_i, z_j, N_z);

                                const double dist_sq =
                                    dx_wrap * dx_wrap +
                                    dy_wrap * dy_wrap +
                                    dz_wrap * dz_wrap;

                                if (dist_sq <= radius_sq) {
                                    const double distance = std::sqrt(dist_sq);
                                    const double coupling_strength = couplingKernel(distance, radius);

                                    const size_t neighbor_index =
                                        static_cast<size_t>(z_j) * plane_size +
                                        static_cast<size_t>(y_j) * N_x +
                                        static_cast<size_t>(x_j);

                                    nonlocal_coupling += coupling_strength * (nodes[neighbor_index].psi - node.psi);
                                    neighbor_operations++;
                                }
                            }
                        }
                    }
                }
            }

            std::complex<double> i_gamma(0.0, node.gamma);
            std::complex<double> H_psi = -nonlocal_coupling + V_eff * node.psi + i_gamma * node.psi;
            std::complex<double> i_unit(0.0, 1.0);
            node.psi_dot = (-i_unit / hbar) * H_psi;
            node.psi += node.psi_dot * dt;
        }

        return neighbor_operations + static_cast<uint64_t>(N_total);
    }

    static uint64_t evolveCausalField(
        std::vector<IGSOAComplexNode>& nodes,
        double dt
    ) {
        uint64_t operations = 0;

        for (auto& node : nodes) {
            const double coupling_diff = node.phi - node.psi.real();
            node.phi_dot = -node.kappa * coupling_diff - node.gamma * node.phi;
            node.phi += node.phi_dot * dt;
            operations++;
        }

        return operations;
    }

    static uint64_t updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        uint64_t operations = 0;
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
            node.updateEntropyRate();
            operations++;
        }
        return operations;
    }

    /**
     * Compute 3D spatial gradients of F (informational density)
     *
     * ∇F = (∂F/∂x, ∂F/∂y, ∂F/∂z) approximated as central differences
     */
    static uint64_t computeGradients(
        std::vector<IGSOAComplexNode>& nodes,
        size_t N_x,
        size_t N_y,
        size_t N_z
    ) {
        const size_t N_total = N_x * N_y * N_z;
        const size_t plane_size = N_x * N_y;
        uint64_t operations = 0;

        for (size_t index = 0; index < N_total; ++index) {
            const int x_i = static_cast<int>(index % N_x);
            const int y_i = static_cast<int>((index / N_x) % N_y);
            const int z_i = static_cast<int>(index / plane_size);

            // Neighbor indices with wrapping
            const int x_right = (x_i == static_cast<int>(N_x) - 1) ? 0 : x_i + 1;
            const int x_left = (x_i == 0) ? static_cast<int>(N_x) - 1 : x_i - 1;
            const int y_up = (y_i == static_cast<int>(N_y) - 1) ? 0 : y_i + 1;
            const int y_down = (y_i == 0) ? static_cast<int>(N_y) - 1 : y_i - 1;
            const int z_front = (z_i == static_cast<int>(N_z) - 1) ? 0 : z_i + 1;
            const int z_back = (z_i == 0) ? static_cast<int>(N_z) - 1 : z_i - 1;

            // Convert to 1D indices
            const size_t idx_right = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_right);
            const size_t idx_left = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_left);
            const size_t idx_up = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_up) * N_x + static_cast<size_t>(x_i);
            const size_t idx_down = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_down) * N_x + static_cast<size_t>(x_i);
            const size_t idx_front = static_cast<size_t>(z_front) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_i);
            const size_t idx_back = static_cast<size_t>(z_back) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_i);

            // Central differences: ∂F/∂x ≈ (F[x+1] - F[x-1]) / 2
            const double dF_dx = (nodes[idx_right].F - nodes[idx_left].F) * 0.5;
            const double dF_dy = (nodes[idx_up].F - nodes[idx_down].F) * 0.5;
            const double dF_dz = (nodes[idx_front].F - nodes[idx_back].F) * 0.5;

            // Store gradient magnitude
            nodes[index].F_gradient = std::sqrt(dF_dx * dF_dx + dF_dy * dF_dy + dF_dz * dF_dz);
            operations++;
        }
        return operations;
    }

    static uint64_t timeStep(
        std::vector<IGSOAComplexNode>& nodes,
        const IGSOAComplexConfig& config,
        size_t N_x,
        size_t N_y,
        size_t N_z
    ) {
        uint64_t operations = 0;
        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        operations += updateDerivedQuantities(nodes);  // Fixed: now returns operation count
        operations += computeGradients(nodes, N_x, N_y, N_z);

        // Normalize if requested (matches 1D/2D behavior)
        if (config.normalize_psi) {
            operations += IGSOAPhysics::normalizeStates(nodes);
        }

        return operations;
    }

    static void applyDriving(
        std::vector<IGSOAComplexNode>& nodes,
        double signal_real,
        double signal_imag = 0.0
    ) {
        for (auto& node : nodes) {
            // Drive causal field (Φ)
            node.phi += signal_real;

            // Drive quantum state (Ψ) - matches 1D/2D behavior
            node.psi += std::complex<double>(signal_real, signal_imag);
        }
    }
};

} // namespace igsoa
} // namespace dase

