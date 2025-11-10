/**
 * IGSOA Complex Node Structure
 *
 * Implements the Informational Ground State - Ontological Asymmetry (IGSOA) framework
 * with complex-valued quantum states.
 *
 * Theoretical Foundation:
 * - IGS (Informational Ground State): Maximally symmetric Hilbert space substrate
 * - OA (Ontological Asymmetry): Non-Hermitian operator generating structure
 * - Quantum states: |Ψ⟩ ∈ H_I (complex Hilbert space)
 * - Schrödinger-like evolution: iℏ ∂|Ψ⟩/∂t = Ĥ_eff|Ψ⟩
 * - Conjugate domains: Φ(t) (realized) and Ψ(t) (latent potential)
 * - Causal resistance: R_c mediating phase relationships
 */

#pragma once

#include <complex>
#include <cstdint>
#include <string>
#include <stdexcept>

namespace dase {
namespace igsoa {

/**
 * IGSOA Complex Node
 *
 * Represents a single node in the IGSOA Complex engine with quantum state evolution.
 *
 * State Variables:
 * - psi: Complex quantum amplitude |Ψ⟩
 * - phi: Real-valued realized causal energy Φ
 * - F: Informational density F = |Ψ|²
 * - R_c: Causal resistance (mediates dissipation)
 * - T_IGS: IGS temperature T_IGS = F
 * - entropy_rate: Entropy production Ṡ = R_c(∇F)²
 */
struct IGSOAComplexNode {
    // Quantum state (complex Hilbert space)
    std::complex<double> psi;          // |Ψ⟩ - quantum amplitude (latent potential)
    std::complex<double> psi_dot;      // ∂|Ψ⟩/∂t - time derivative

    // Realized causal field (real-valued)
    double phi;                         // Φ - realized causal energy
    double phi_dot;                     // ∂Φ/∂t - causal energy rate

    // Informational density (derived from quantum state)
    double F;                           // F = |Ψ|² - informational density
    double F_gradient;                  // ∇F - spatial gradient (simplified 1D)

    // Causal resistance and dissipation
    double R_c;                         // Causal resistance (mediates Φ-Ψ coupling)
    double entropy_rate;                // Ṡ = R_c(Φ - Re[Ψ])² - entropy production

    // IGS temperature (informational)
    double T_IGS;                       // T_IGS = F - informational temperature

    // Coupling parameters
    double kappa;                       // κ - Φ-Ψ coupling strength
    double gamma;                       // γ - dissipation coefficient

    // Harmonic analysis (for pattern detection)
    uint32_t harmonic_count;            // Number of harmonics detected
    double phase;                       // Phase of Ψ: arg(Ψ)

    // Default constructor - initialize to ground state
    IGSOAComplexNode()
        : psi(0.0, 0.0)
        , psi_dot(0.0, 0.0)
        , phi(0.0)
        , phi_dot(0.0)
        , F(0.0)
        , F_gradient(0.0)
        , R_c(3.0)                // Default causal radius (≈3 lattice units)
        , entropy_rate(0.0)
        , T_IGS(0.0)
        , kappa(1.0)              // Default coupling strength
        , gamma(0.1)              // Default dissipation
        , harmonic_count(0)
        , phase(0.0)
    {}

    /**
     * Update informational density from quantum state
     * F = |Ψ|² = Ψ* · Ψ
     */
    inline void updateInformationalDensity() {
        F = std::norm(psi);  // |Ψ|² = Re(Ψ)² + Im(Ψ)²
        T_IGS = F;           // Temperature equals informational density
    }

    /**
     * Update phase from quantum state
     * phase = arg(Ψ) = atan2(Im[Ψ], Re[Ψ])
     */
    inline void updatePhase() {
        phase = std::arg(psi);
    }

    /**
     * Compute entropy production rate
     * Ṡ = R_c(Φ - Re[Ψ])²
     *
     * Note: This is a simplified coupling model.
     * Full theory may use different Φ-Ψ coupling.
     */
    inline void updateEntropyRate() {
        double coupling_diff = phi - psi.real();
        entropy_rate = R_c * coupling_diff * coupling_diff;
    }

    /**
     * Normalize quantum state (unitary evolution)
     * |Ψ⟩ → |Ψ⟩ / ||Ψ||
     */
    inline void normalize() {
        double magnitude = std::abs(psi);
        if (magnitude > 1e-15) {
            psi /= magnitude;
        }
    }
};

/**
 * Engine configuration for IGSOA Complex simulation
 */
struct IGSOAComplexConfig {
    uint32_t num_nodes;           // Number of nodes in the network
    double R_c_default;            // Default causal resistance
    double kappa;                  // Φ-Ψ coupling strength
    double gamma;                  // Dissipation coefficient
    double dt;                     // Time step for integration
    bool normalize_psi;            // Whether to normalize |Ψ⟩ (unitary evolution)

    IGSOAComplexConfig()
        : num_nodes(1024)
        , R_c_default(3.0)         // Default causal radius (≈3 lattice units)
        , kappa(1.0)
        , gamma(0.1)
        , dt(0.01)
        , normalize_psi(true)
    {}

    /**
     * Validate configuration parameters
     *
     * @param error_msg Output parameter for error message (if validation fails)
     * @return true if valid, false otherwise
     */
    bool validate(std::string* error_msg = nullptr) const {
        // Check num_nodes > 0
        if (num_nodes == 0) {
            if (error_msg) *error_msg = "num_nodes must be positive (got 0)";
            return false;
        }

        // Check reasonable bounds on num_nodes (prevent excessive memory allocation)
        constexpr uint32_t MAX_NODES = 100'000'000;  // 100M nodes = ~10-20 GB RAM
        if (num_nodes > MAX_NODES) {
            if (error_msg) {
                *error_msg = "num_nodes exceeds maximum (" + std::to_string(num_nodes) +
                            " > " + std::to_string(MAX_NODES) + ")";
            }
            return false;
        }

        // Check R_c > 0 (causal radius must be positive)
        if (R_c_default <= 0.0) {
            if (error_msg) {
                *error_msg = "R_c_default must be positive (got " + std::to_string(R_c_default) + ")";
            }
            return false;
        }

        // Check reasonable bounds on R_c
        constexpr double MAX_R_C = 1000.0;  // Prevent unreasonably large neighbor lists
        if (R_c_default > MAX_R_C) {
            if (error_msg) {
                *error_msg = "R_c_default too large (" + std::to_string(R_c_default) +
                            " > " + std::to_string(MAX_R_C) + "), may cause performance issues";
            }
            return false;
        }

        // Check dt > 0 (time step must be positive)
        if (dt <= 0.0) {
            if (error_msg) {
                *error_msg = "dt (time step) must be positive (got " + std::to_string(dt) + ")";
            }
            return false;
        }

        // Check dt not too large (stability condition)
        constexpr double MAX_DT = 1.0;
        if (dt > MAX_DT) {
            if (error_msg) {
                *error_msg = "dt too large (" + std::to_string(dt) +
                            " > " + std::to_string(MAX_DT) + "), may cause numerical instability";
            }
            return false;
        }

        // Check kappa >= 0 (coupling strength must be non-negative)
        if (kappa < 0.0) {
            if (error_msg) {
                *error_msg = "kappa (coupling strength) must be non-negative (got " + std::to_string(kappa) + ")";
            }
            return false;
        }

        // Check gamma >= 0 (dissipation must be non-negative)
        if (gamma < 0.0) {
            if (error_msg) {
                *error_msg = "gamma (dissipation) must be non-negative (got " + std::to_string(gamma) + ")";
            }
            return false;
        }

        // All checks passed
        return true;
    }

    /**
     * Validate and throw exception if invalid
     *
     * @throws std::invalid_argument if configuration is invalid
     */
    void validateOrThrow() const {
        std::string error_msg;
        if (!validate(&error_msg)) {
            throw std::invalid_argument("Invalid IGSOAComplexConfig: " + error_msg);
        }
    }
};

} // namespace igsoa
} // namespace dase
