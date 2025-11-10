/**
 * IGSOA Gravitational Wave Engine - Fractional Solver Module
 *
 * Implements the Caputo fractional derivative for memory dynamics:
 * ₀D^α_t f(t) = (1/Γ(2-α)) ∫₀ᵗ K_α(t-t') ∂²_t' f(t') dt'
 *
 * Uses Sum-of-Exponentials (SOE) optimization for efficient O(N) computation
 * instead of naive O(N²) convolution.
 *
 * Physical meaning:
 * - α = 2.0: Standard wave equation (no memory, flat spacetime)
 * - α < 2.0: Nonlocal memory (curved spacetime, causal integration)
 * - α → 1.0: Maximum memory depth (near event horizon)
 *
 * Based on: IGSOA-QMM Papers 04, 05
 * Design: docs/implementation/IGSOA_GW_ENGINE_DESIGN.md
 */

#pragma once

#include <vector>
#include <complex>
#include <memory>

namespace dase {
namespace igsoa {
namespace gw {

/**
 * Sum-of-Exponentials kernel approximation
 *
 * Approximates the fractional memory kernel K_α(t) as:
 * K_α(t) ≈ Σᵣ wᵣ exp(-sᵣ t)
 *
 * This enables O(N) computation via recursive update instead of
 * O(N²) convolution.
 */
struct SOEKernel {
    std::vector<double> weights;     // wᵣ coefficients
    std::vector<double> exponents;   // sᵣ decay rates
    int rank;                        // R = number of exponential terms

    SOEKernel();

    /**
     * Initialize SOE approximation for given α
     * @param alpha Fractional order ∈ [1.0, 2.0]
     * @param T_max Maximum time for approximation accuracy
     * @param target_rank Desired number of terms (10-14 typical)
     */
    void initialize(double alpha, double T_max, int target_rank = 12);

    /**
     * Evaluate kernel at time t
     */
    double evaluate(double t) const;

    /**
     * Compute error estimate vs exact kernel
     */
    double estimateError(double alpha, double t) const;
};

/**
 * History state for fractional derivative computation
 *
 * Stores internal states zᵣ(t) for each SOE term, enabling
 * recursive update without storing full history.
 */
struct HistoryState {
    std::vector<std::complex<double>> z_states;  // Internal states zᵣ

    HistoryState();
    explicit HistoryState(int rank);

    /**
     * Update states for next timestep
     * zᵣ(t+dt) = exp(-sᵣ dt) zᵣ(t) + wᵣ ∂²_t f(t) dt
     */
    void update(const SOEKernel& kernel, std::complex<double> second_derivative, double dt);

    /**
     * Compute fractional derivative from current states
     * ₀D^α_t f(t) ≈ Σᵣ zᵣ(t)
     */
    std::complex<double> computeDerivative() const;

    /**
     * Reset to zero
     */
    void reset();
};

/**
 * Configuration for fractional solver
 */
struct FractionalSolverConfig {
    double T_max;           // Maximum simulation time (for SOE accuracy)
    int soe_rank;           // Number of exponential terms (10-14)
    double dt;              // Timestep

    // Fractional order range
    double alpha_min;       // Minimum α (maximum memory)
    double alpha_max;       // Maximum α (minimum memory)

    FractionalSolverConfig();
};

/**
 * Fractional memory solver
 *
 * Computes Caputo fractional derivatives ₀D^α_t for all grid points,
 * using SOE optimization for efficiency.
 */
class FractionalSolver {
public:
    /**
     * Constructor
     * @param config Solver configuration
     * @param num_points Total number of field grid points
     */
    explicit FractionalSolver(const FractionalSolverConfig& config, int num_points);

    /**
     * Destructor
     */
    ~FractionalSolver();

    // Disable copy (large state vectors)
    FractionalSolver(const FractionalSolver&) = delete;
    FractionalSolver& operator=(const FractionalSolver&) = delete;

    // === Kernel Management ===

    /**
     * Get or create SOE kernel for given α
     * (Kernels are cached for efficiency)
     */
    const SOEKernel& getKernel(double alpha);

    /**
     * Precompute kernels for range of α values
     */
    void precomputeKernels(int num_alpha_samples = 20);

    // === Fractional Derivative Computation ===

    /**
     * Update history states for all grid points
     *
     * @param field_values Current field values δΦ(x,t)
     * @param field_second_time_derivatives ∂²_t δΦ(x,t)
     * @param alpha_values Fractional order α(x) at each grid point
     * @param dt Timestep
     */
    void updateHistory(
        const std::vector<std::complex<double>>& field_values,
        const std::vector<std::complex<double>>& field_second_time_derivatives,
        const std::vector<double>& alpha_values,
        double dt
    );

    /**
     * Compute fractional derivatives for all grid points
     *
     * @param alpha_values Fractional order α(x) at each grid point
     * @return Vector of ₀D^α_t δΦ for each point
     */
    std::vector<std::complex<double>> computeDerivatives(
        const std::vector<double>& alpha_values
    ) const;

    /**
     * Compute fractional derivative for single grid point
     */
    std::complex<double> computeDerivativeAt(int point_index, double alpha) const;

    // === Memory Strength ===

    /**
     * Get memory strength parameter η = 1 - α
     * η = 0: No memory (standard wave)
     * η = 1: Maximum memory (horizon physics)
     */
    double getMemoryStrength(double alpha) const {
        return 1.0 - alpha;
    }

    // === Diagnostics ===

    /**
     * Get total number of grid points
     */
    int getNumPoints() const { return num_points_; }

    /**
     * Get number of cached kernels
     */
    int getNumCachedKernels() const;

    /**
     * Reset all history states (for new simulation)
     */
    void resetHistory();

    /**
     * Get memory usage estimate (bytes)
     */
    size_t getMemoryUsage() const;

    // === Analytical Tests ===

    /**
     * Compute exact Caputo derivative for test function (for validation)
     * Test: f(t) = t^β → ₀D^α_t f(t) = Γ(β+1)/Γ(β-α+1) t^(β-α)
     */
    double computeExactCaputo(double alpha, double beta, double t) const;

    /**
     * Validate SOE approximation against exact formula
     */
    struct ValidationResult {
        double max_error;
        double mean_error;
        double rms_error;
        bool passed;  // true if max_error < tolerance
    };
    ValidationResult validateSOEApproximation(double alpha, double tolerance = 1e-6) const;

private:
    FractionalSolverConfig config_;
    int num_points_;

    // SOE kernel cache (map: α → kernel)
    std::vector<double> cached_alphas_;
    std::vector<SOEKernel> cached_kernels_;

    // History states for each grid point
    std::vector<HistoryState> history_states_;

    // Helper: find or create kernel for α
    int findKernelIndex(double alpha, double tolerance = 1e-6) const;

    // Helper: interpolate between two kernels if needed
    SOEKernel interpolateKernels(double alpha) const;
};

/**
 * Mittag-Leffler function E_α,β(z)
 *
 * Special function appearing in fractional calculus solutions:
 * E_α,β(z) = Σ_{k=0}^∞ z^k / Γ(αk + β)
 *
 * Used for analytical test solutions and envelope functions.
 */
class MittagLefflerFunction {
public:
    /**
     * Evaluate E_α,β(z) with specified accuracy
     */
    static std::complex<double> evaluate(
        double alpha,
        double beta,
        std::complex<double> z,
        int max_terms = 100,
        double tolerance = 1e-12
    );

    /**
     * Evaluate E_α(z) = E_α,1(z) (most common case)
     */
    static std::complex<double> evaluate_one_param(
        double alpha,
        std::complex<double> z,
        int max_terms = 100,
        double tolerance = 1e-12
    );

    /**
     * Evaluate for real argument (faster)
     */
    static double evaluate_real(double alpha, double beta, double z);

    /**
     * Asymptotic expansion for large |z|
     */
    static std::complex<double> asymptotic_expansion(
        double alpha,
        double beta,
        std::complex<double> z,
        int num_terms = 10
    );
};

/**
 * Gamma function and related utilities
 */
namespace gamma_functions {
    /**
     * Gamma function Γ(x)
     */
    double gamma(double x);

    /**
     * Log-gamma function ln(Γ(x))
     */
    double lgamma(double x);

    /**
     * Beta function B(a,b) = Γ(a)Γ(b)/Γ(a+b)
     */
    double beta(double a, double b);

} // namespace gamma_functions

} // namespace gw
} // namespace igsoa
} // namespace dase
