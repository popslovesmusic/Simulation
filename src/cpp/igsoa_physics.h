/**
 * IGSOA Physics Implementation
 *
 * Implements the evolution equations for the IGSOA (Informational Ground State -
 * Ontological Asymmetry) framework with complex-valued quantum states.
 *
 * Core Equations:
 * 1. Schrödinger-like evolution: iℏ ∂|Ψ⟩/∂t = Ĥ_eff|Ψ⟩
 * 2. Causal field evolution: ∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
 * 3. Informational density: F = |Ψ|²
 * 4. Entropy production: Ṡ = R_c(Φ - Re[Ψ])²
 *
 * Theoretical Foundation:
 * - IGS: Maximally symmetric Hilbert space substrate H_I
 * - OA: Non-Hermitian operator Ĥ_eff generating structure
 * - Φ: Realized causal energy (observable)
 * - Ψ: Latent quantum potential (complex)
 * - R_c: Causal resistance mediating dissipation
 */

#pragma once

#include "igsoa_complex_node.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>

namespace dase {
namespace igsoa {

/**
 * IGSOA Physics Engine
 *
 * Implements time evolution of the IGSOA system
 */
class IGSOAPhysics {
public:
    /**
     * Compute non-local coupling kernel
     *
     * K(r, R_c) = exp(-r/R_c) / R_c
     *
     * This provides exponential decay of coupling strength with distance,
     * normalized by the causal radius R_c.
     *
     * @param distance Spatial distance between nodes
     * @param R_c Causal coupling radius
     * @return Coupling strength
     */
    static inline double couplingKernel(double distance, double R_c) {
        if (distance <= 0.0 || R_c <= 0.0) return 0.0;
        return std::exp(-distance / R_c) / R_c;
    }

    /**
     * Compute wrapped lattice distance for periodic boundary conditions.
     */
    static inline double wrappedDistance(size_t index, size_t neighbor, size_t N) {
        if (N == 0) return 0.0;
        double raw_distance = std::abs(static_cast<double>(index) - static_cast<double>(neighbor));
        if (raw_distance > static_cast<double>(N) * 0.5) {
            raw_distance = static_cast<double>(N) - raw_distance;
        }
        return raw_distance;
    }

    /**
     * Evolve quantum state: iℏ ∂|Ψ⟩/∂t = Ĥ_eff|Ψ⟩
     *
     * CORRECTED: Implements true non-local coupling with R_c-dependent range
     *
     * Effective Hamiltonian:
     * Ĥ_eff = -𝒦[Ψ] + V_eff(Φ) + iΓ
     *
     * Where:
     * - 𝒦[Ψ] = ∑_{j: |j-i| ≤ R_c} K(|j-i|, R_c) Ψ_j  (causal derivative)
     * - K(r, R_c) = exp(-r/R_c) / R_c  (coupling kernel)
     * - V_eff(Φ) = κΦ is coupling to realized field
     * - iΓ is non-Hermitian term (dissipation)
     *
     * Computational complexity: O(N × R_c) per time step
     *
     * @param nodes Network of IGSOA nodes
     * @param dt Time step
     * @param hbar Reduced Planck constant (default: 1.0 in natural units)
     */
    static uint64_t evolveQuantumState(
        std::vector<IGSOAComplexNode>& nodes,
        double dt,
        double hbar = 1.0
    ) {
        const size_t N = nodes.size();
        uint64_t neighbor_operations = 0;

        // Evolve each node with non-local coupling
        for (size_t i = 0; i < N; i++) {
            auto& node = nodes[i];

            // Compute effective potential from realized field
            std::complex<double> V_eff = node.kappa * node.phi;

            // NON-LOCAL SPATIAL COUPLING (Causal Derivative Operator 𝒦)
            // Sum over all neighbors within causal radius R_c
            std::complex<double> nonlocal_coupling(0.0, 0.0);

            // DIAGNOSTIC: Print once to verify this code path is active
            static bool diagnostic_printed = false;
            if (!diagnostic_printed && i == 0) {
                std::cerr << "[IGSOA DIAGNOSTIC] Using CORRECTED non-local coupling (Oct 26 2025, R_c="
                          << node.R_c << ")" << std::endl;
                diagnostic_printed = true;
            }

            if (N > 1) {
                // Determine coupling range based on R_c
                double radius = std::max(node.R_c, 0.0);
                int R_c_int = static_cast<int>(std::ceil(radius));

                // Loop over all neighbors within R_c
                for (int offset = -R_c_int; offset <= R_c_int; offset++) {
                    if (offset == 0) continue;  // Skip self-coupling

                    // Periodic boundary conditions (lattice wrapping)
                    int j = static_cast<int>(i) + offset;
                    while (j < 0) j += static_cast<int>(N);
                    while (j >= static_cast<int>(N)) j -= static_cast<int>(N);

                    // Compute spatial distance
                    double distance = wrappedDistance(i, static_cast<size_t>(j), N);

                    // Only couple if within causal radius
                    if (distance <= radius && radius > 0.0) {
                        // Compute coupling strength using exponential kernel
                        double coupling_strength = couplingKernel(distance, radius);

                        // Accumulate weighted contribution from neighbor
                        nonlocal_coupling += coupling_strength * (nodes[j].psi - node.psi);
                        neighbor_operations++;
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
            // TODO: Upgrade to RK4 for better accuracy
            node.psi += node.psi_dot * dt;
        }

        return neighbor_operations + static_cast<uint64_t>(N);
    }

    /**
     * Evolve realized causal field: ∂Φ/∂t = -κ(Φ - Re[Ψ]) - γΦ
     *
     * This couples the realized field Φ to the quantum state Ψ with:
     * - κ: Coupling strength (how strongly Φ follows Ψ)
     * - γ: Dissipation (how quickly Φ decays)
     *
     * Physical interpretation:
     * - Φ is pulled toward Re[Ψ] (the "classical projection" of quantum state)
     * - γ provides energy dissipation
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
     * Update derived quantities:
     * - F = |Ψ|² (informational density)
     * - T_IGS = F (informational temperature)
     * - phase = arg(Ψ)
     * - Ṡ = R_c(Φ - Re[Ψ])² (entropy production)
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
     * Compute spatial gradients of F (informational density)
     * ∇F approximated as finite difference
     */
    static uint64_t computeGradients(
        std::vector<IGSOAComplexNode>& nodes
    ) {
        const size_t N = nodes.size();
        uint64_t operations = 0;

        for (size_t i = 0; i < N; i++) {
            if (N > 1) {
                size_t right = (i == N - 1) ? 0 : i + 1;
                // Simple forward difference: ∇F ≈ (F[i+1] - F[i])
                nodes[i].F_gradient = nodes[right].F - nodes[i].F;
            } else {
                nodes[i].F_gradient = 0.0;
            }
            operations++;
        }
        return operations;
    }

    /**
     * Normalize all quantum states (unitary evolution)
     * |Ψ⟩ → |Ψ⟩ / ||Ψ||
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
     * Full time step evolution
     *
     * Performs one complete integration step:
     * 1. Evolve quantum state Ψ
     * 2. Evolve causal field Φ
     * 3. Update derived quantities (F, T_IGS, phase, Ṡ)
     * 4. Compute gradients
     * 5. Optionally normalize states
     */
    static uint64_t timeStep(
        std::vector<IGSOAComplexNode>& nodes,
        const IGSOAComplexConfig& config
    ) {
        uint64_t operations = 0;
        // 1. Evolve quantum state
        operations += evolveQuantumState(nodes, config.dt);

        // 2. Evolve causal field
        operations += evolveCausalField(nodes, config.dt);

        // 3. Update derived quantities
        operations += updateDerivedQuantities(nodes);

        // 4. Compute gradients
        operations += computeGradients(nodes);

        // 5. Normalize if requested
        if (config.normalize_psi) {
            operations += normalizeStates(nodes);
        }
        return operations;
    }

    /**
     * Apply external driving signal to nodes
     *
     * This allows injecting energy into the system through:
     * - Direct Φ excitation (classical)
     * - Complex Ψ excitation (quantum)
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
     * Compute total system energy
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
     * Compute total entropy production rate
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
