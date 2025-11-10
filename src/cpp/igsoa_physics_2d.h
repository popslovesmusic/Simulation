/**
 * IGSOA Physics Implementation - 2D Extension
 *
 * Implements the evolution equations for the IGSOA framework on a 2D toroidal lattice.
 *
 * Core Equations (unchanged from 1D):
 * 1. Schrödinger-like evolution: iℏ ∂|Ψ⟩/∂t = Ĥ_eff|Ψ⟩
 * 2. Causal field evolution: ∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
 * 3. Informational density: F = |Ψ|²
 * 4. Entropy production: Ṡ = R_c(Φ - Re[Ψ])²
 *
 * Key 2D Extensions:
 * - Distance metric: d = sqrt(dx² + dy²) with toroidal wrapping
 * - Coupling region: Circular neighborhood within R_c
 * - Gradient computation: 2D central differences (∇F = (∂F/∂x, ∂F/∂y))
 */

#pragma once

#include "igsoa_complex_node.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
#include <iostream>
#include <mutex>

namespace dase {
namespace igsoa {

/**
 * IGSOA Physics Engine - 2D
 *
 * Implements time evolution of the IGSOA system on a 2D lattice
 */
class IGSOAPhysics2D {
public:
    /**
     * Compute non-local coupling kernel (reused from 1D)
     *
     * K(r, R_c) = exp(-r/R_c) / R_c
     */
    static inline double couplingKernel(double distance, double R_c) {
        if (distance <= 0.0 || R_c <= 0.0) return 0.0;
        return std::exp(-distance / R_c) / R_c;
    }

    /**
     * Compute wrapped distance in 1D with periodic boundaries
     *
     * @param coord1 First coordinate
     * @param coord2 Second coordinate
     * @param N Number of nodes in this dimension
     * @return Minimum distance with wrapping
     */
    static inline double wrappedDistance1D(int coord1, int coord2, size_t N) {
        int raw_dist = std::abs(coord1 - coord2);
        int wrapped_dist = std::min(raw_dist, static_cast<int>(N) - raw_dist);
        return static_cast<double>(wrapped_dist);
    }

    /**
     * Compute 2D Euclidean distance with toroidal wrapping
     *
     * On a torus, we take the minimum distance considering wraparound in both dimensions.
     *
     * @param x1 X-coordinate of first node
     * @param y1 Y-coordinate of first node
     * @param x2 X-coordinate of second node
     * @param y2 Y-coordinate of second node
     * @param N_x Number of nodes in x-direction
     * @param N_y Number of nodes in y-direction
     * @return Euclidean distance with wrapping
     */
    static inline double wrappedDistance2D(
        int x1, int y1,
        int x2, int y2,
        size_t N_x, size_t N_y
    ) {
        double dx = wrappedDistance1D(x1, x2, N_x);
        double dy = wrappedDistance1D(y1, y2, N_y);
        return std::sqrt(dx * dx + dy * dy);
    }

    /**
     * Evolve quantum state: iℏ ∂|Ψ⟩/∂t = Ĥ_eff|Ψ⟩
     *
     * 2D version with circular coupling region within R_c.
     *
     * Effective Hamiltonian:
     * Ĥ_eff = -𝒦[Ψ] + V_eff(Φ) + iΓ
     *
     * Where:
     * - 𝒦[Ψ] = ∑_{j: |r_j - r_i| ≤ R_c} K(|r_j - r_i|, R_c) Ψ_j  (causal derivative)
     * - K(r, R_c) = exp(-r/R_c) / R_c  (coupling kernel)
     * - V_eff(Φ) = κΦ is coupling to realized field
     * - iΓ is non-Hermitian term (dissipation)
     *
     * Computational complexity: O(N × πR_c²) per time step
     *
     * @param nodes Network of IGSOA nodes (row-major layout)
     * @param dt Time step
     * @param N_x Number of nodes in x-direction
     * @param N_y Number of nodes in y-direction
     * @param hbar Reduced Planck constant (default: 1.0 in natural units)
     */
    static uint64_t evolveQuantumState(
        std::vector<IGSOAComplexNode>& nodes,
        double dt,
        size_t N_x,
        size_t N_y,
        double hbar = 1.0
    ) {
        const size_t N_total = N_x * N_y;
        const int N_x_int = static_cast<int>(N_x);
        const int N_y_int = static_cast<int>(N_y);
        uint64_t neighbor_operations = 0;

        // Evolve each node with non-local coupling
        for (size_t i = 0; i < N_total; i++) {
            auto& node = nodes[i];

            // Convert 1D index to 2D coordinates
            const int x_i = static_cast<int>(i % N_x);
            const int y_i = static_cast<int>(i / N_x);

            // Compute effective potential from realized field
            std::complex<double> V_eff = node.kappa * node.phi;

            // NON-LOCAL SPATIAL COUPLING (Causal Derivative Operator 𝒦)
            // Sum over all neighbors within circular region of radius R_c
            std::complex<double> nonlocal_coupling(0.0, 0.0);

            // DIAGNOSTIC: Print once to verify this code path is active (thread-safe)
            static std::once_flag diagnostic_flag;
            if (i == 0) {
                std::call_once(diagnostic_flag, [&]() {
                    std::cerr << "[IGSOA 2D DIAGNOSTIC] Using 2D non-local coupling (Nov 3 2025, R_c="
                              << node.R_c << ", lattice=" << N_x << "x" << N_y << ")" << std::endl;
                });
            }

            if (N_total > 1) {
                // Determine coupling range based on R_c
                const double radius = std::max(node.R_c, 0.0);
                const int R_c_int = static_cast<int>(std::ceil(radius));

                // Loop over square bounding box, then filter by circular distance
                for (int dy = -R_c_int; dy <= R_c_int; dy++) {
                    for (int dx = -R_c_int; dx <= R_c_int; dx++) {
                        if (dx == 0 && dy == 0) continue;  // Skip self-coupling

                        // Periodic boundary conditions (torus wrapping) - optimized modulo
                        int x_temp = (x_i + dx) % N_x_int;
                        int x_j = (x_temp < 0) ? (x_temp + N_x_int) : x_temp;

                        int y_temp = (y_i + dy) % N_y_int;
                        int y_j = (y_temp < 0) ? (y_temp + N_y_int) : y_temp;

                        // Compute 2D spatial distance
                        double distance = wrappedDistance2D(x_i, y_i, x_j, y_j, N_x, N_y);

                        // Only couple if within causal radius (circular cutoff)
                        if (distance <= radius && radius > 0.0) {
                            // Compute coupling strength using exponential kernel
                            double coupling_strength = couplingKernel(distance, radius);

                            // Convert 2D coords to 1D index
                            size_t j = static_cast<size_t>(y_j) * N_x + static_cast<size_t>(x_j);

                            // Accumulate weighted contribution from neighbor
                            nonlocal_coupling += coupling_strength * (nodes[j].psi - node.psi);
                            neighbor_operations++;
                        }
                    }
                }
            }

            // Non-Hermitian dissipation term
            std::complex<double> i_gamma(0.0, node.gamma);

            // Hamiltonian action: Ĥ Ψ = -𝒦[Ψ] + V_eff Ψ + iΓ Ψ
            std::complex<double> H_psi = -nonlocal_coupling + V_eff * node.psi + i_gamma * node.psi;

            // Schrödinger evolution: ∂Ψ/∂t = -i/ℏ Ĥ Ψ
            std::complex<double> i_unit(0.0, 1.0);
            node.psi_dot = (-i_unit / hbar) * H_psi;

            // Update Ψ using Euler integration
            node.psi += node.psi_dot * dt;
        }

        return neighbor_operations + static_cast<uint64_t>(N_total);
    }

    /**
     * Evolve realized causal field: ∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
     *
     * Identical to 1D (no spatial coupling in Φ evolution)
     */
    static uint64_t evolveCausalField(
        std::vector<IGSOAComplexNode>& nodes,
        double dt
    ) {
        uint64_t operations = 0;
        for (auto& node : nodes) {
            // Coupling difference: Φ - Re[Ψ]
            double coupling_diff = node.phi - node.psi.real();

            // ∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
            node.phi_dot = -node.kappa * coupling_diff - node.gamma * node.phi;

            // Update Φ
            node.phi += node.phi_dot * dt;
            operations++;
        }

        return operations;
    }

    /**
     * Update derived quantities (identical to 1D)
     */
    static uint64_t updateDerivedQuantities(
        std::vector<IGSOAComplexNode>& nodes
    ) {
        uint64_t operations = 0;
        for (auto& node : nodes) {
            node.updateInformationalDensity();  // F = |Ψ|²
            node.updatePhase();                  // phase = arg(Ψ)
            node.updateEntropyRate();            // Ṡ = R_c(Φ - Re[Ψ])²
            operations++;
        }
        return operations;
    }

    /**
     * Compute 2D spatial gradients of F (informational density)
     *
     * ∇F = (∂F/∂x, ∂F/∂y) approximated as central differences
     *
     * For now, we store only the gradient magnitude in F_gradient.
     * Future: Store full 2D gradient vector.
     */
    static uint64_t computeGradients(
        std::vector<IGSOAComplexNode>& nodes,
        size_t N_x,
        size_t N_y
    ) {
        const size_t N_total = N_x * N_y;
        const int N_x_int = static_cast<int>(N_x);
        const int N_y_int = static_cast<int>(N_y);
        uint64_t operations = 0;

        for (size_t i = 0; i < N_total; i++) {
            const int x_i = static_cast<int>(i % N_x);
            const int y_i = static_cast<int>(i / N_x);

            // Neighbor indices with wrapping
            const int x_right = (x_i == N_x_int - 1) ? 0 : x_i + 1;
            const int x_left = (x_i == 0) ? N_x_int - 1 : x_i - 1;
            const int y_up = (y_i == N_y_int - 1) ? 0 : y_i + 1;
            const int y_down = (y_i == 0) ? N_y_int - 1 : y_i - 1;

            // Convert to 1D indices
            size_t idx_right = static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_right);
            size_t idx_left = static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_left);
            size_t idx_up = static_cast<size_t>(y_up) * N_x + static_cast<size_t>(x_i);
            size_t idx_down = static_cast<size_t>(y_down) * N_x + static_cast<size_t>(x_i);

            // Central difference: ∂F/∂x ≈ (F[x+1] - F[x-1]) / 2
            double dF_dx = (nodes[idx_right].F - nodes[idx_left].F) * 0.5;
            double dF_dy = (nodes[idx_up].F - nodes[idx_down].F) * 0.5;

            // Store gradient magnitude (for now)
            nodes[i].F_gradient = std::sqrt(dF_dx * dF_dx + dF_dy * dF_dy);
            operations++;
        }
        return operations;
    }

    /**
     * Normalize all quantum states (identical to 1D)
     */
    static uint64_t normalizeStates(
        std::vector<IGSOAComplexNode>& nodes
    ) {
        uint64_t operations = 0;
        for (auto& node : nodes) {
            node.normalize();
            operations++;
        }
        return operations;
    }

    /**
     * Full time step evolution for 2D
     *
     * Performs one complete integration step:
     * 1. Evolve quantum state Ψ (2D coupling)
     * 2. Evolve causal field Φ
     * 3. Update derived quantities (F, T_IGS, phase, Ṡ)
     * 4. Compute 2D gradients
     * 5. Optionally normalize states
     */
    static uint64_t timeStep(
        std::vector<IGSOAComplexNode>& nodes,
        const IGSOAComplexConfig& config,
        size_t N_x,
        size_t N_y
    ) {
        uint64_t operations = 0;

        // 1. Evolve quantum state (2D coupling)
        operations += evolveQuantumState(nodes, config.dt, N_x, N_y);

        // 2. Evolve causal field
        operations += evolveCausalField(nodes, config.dt);

        // 3. Update derived quantities
        operations += updateDerivedQuantities(nodes);

        // 4. Compute 2D gradients
        operations += computeGradients(nodes, N_x, N_y);

        // 5. Normalize if requested
        if (config.normalize_psi) {
            operations += normalizeStates(nodes);
        }

        return operations;
    }

    /**
     * Apply external driving signal to nodes (identical to 1D)
     */
    static void applyDriving(
        std::vector<IGSOAComplexNode>& nodes,
        double signal_real,
        double signal_imag = 0.0
    ) {
        for (auto& node : nodes) {
            // Drive realized field
            node.phi += signal_real;

            // Drive quantum state
            node.psi += std::complex<double>(signal_real, signal_imag);
        }
    }

    /**
     * Compute total system energy (identical to 1D)
     * E = ∑_i [|Ψ_i|² + Φ_i²]
     */
    static double computeTotalEnergy(
        const std::vector<IGSOAComplexNode>& nodes
    ) {
        double energy = 0.0;
        for (const auto& node : nodes) {
            energy += node.F;           // Quantum energy: |Ψ|²
            energy += node.phi * node.phi;  // Classical energy: Φ²
        }
        return energy;
    }

    /**
     * Compute total entropy production rate (identical to 1D)
     * Ṡ_total = ∑_i Ṡ_i
     */
    static double computeTotalEntropyRate(
        const std::vector<IGSOAComplexNode>& nodes
    ) {
        double total_entropy = 0.0;
        for (const auto& node : nodes) {
            total_entropy += node.entropy_rate;
        }
        return total_entropy;
    }
};

} // namespace igsoa
} // namespace dase
