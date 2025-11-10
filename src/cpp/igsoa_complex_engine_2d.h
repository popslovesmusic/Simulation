/**
 * IGSOA Complex Engine - 2D Extension
 *
 * Two-dimensional extension of the IGSOA framework with complex-valued quantum states.
 * Implements SATP (Scalar Affine Toroid Physics) on a 2D toroidal lattice.
 *
 * Key Differences from 1D:
 * - Lattice topology: N_x × N_y torus (periodic boundaries in both dimensions)
 * - Distance metric: Euclidean distance with wrapping
 * - Coupling region: Circular R_c neighborhood (not just linear)
 * - Memory layout: Row-major (cache-friendly sequential access)
 *
 * Physics Preserved:
 * - Same IGSOA evolution equations
 * - Same non-local coupling kernel K(r, R_c) = exp(-r/R_c) / R_c
 * - Same two-field dynamics (Ψ complex, Φ real)
 */

#pragma once

#include "igsoa_complex_node.h"
#include "igsoa_physics_2d.h"
#include <vector>
#include <stdexcept>
#include <memory>
#include <chrono>
#include <string>
#include <cmath>

namespace dase {
namespace igsoa {

/**
 * IGSOA Complex Engine - 2D
 *
 * Main engine class for 2D IGSOA simulations
 */
class IGSOAComplexEngine2D {
public:
    /**
     * Constructor
     *
     * @param config Engine configuration (inherited from 1D)
     * @param N_x Number of nodes in x-direction
     * @param N_y Number of nodes in y-direction
     */
    explicit IGSOAComplexEngine2D(const IGSOAComplexConfig& config, size_t N_x, size_t N_y)
        : config_(config)
        , N_x_(N_x)
        , N_y_(N_y)
        , nodes_(N_x * N_y)
        , current_time_(0.0)
        , total_steps_(0)
        , total_operations_(0)
    {
        // Input validation
        if (N_x == 0 || N_y == 0) {
            throw std::invalid_argument("Lattice dimensions must be positive");
        }
        if (N_x > 4096 || N_y > 4096) {
            throw std::invalid_argument("Lattice dimension too large (max 4096 per axis)");
        }
        const size_t total = N_x * N_y;
        if (total > 100'000'000) {
            throw std::invalid_argument("Total nodes exceeds limit (100M max)");
        }

        // Initialize all nodes with configuration
        for (auto& node : nodes_) {
            node.R_c = config.R_c_default;
            node.kappa = config.kappa;
            node.gamma = config.gamma;
        }
    }

    /**
     * Get lattice dimensions
     */
    size_t getNx() const { return N_x_; }
    size_t getNy() const { return N_y_; }
    size_t getTotalNodes() const { return N_x_ * N_y_; }

    /**
     * Convert 2D coordinates to 1D index (row-major)
     *
     * Index = y * N_x + x
     */
    size_t coordToIndex(size_t x, size_t y) const {
        #ifndef NDEBUG
        if (x >= N_x_ || y >= N_y_) {
            throw std::out_of_range("2D coordinates out of bounds");
        }
        #endif
        return y * N_x_ + x;
    }

    /**
     * Convert 1D index to 2D coordinates
     */
    void indexToCoord(size_t index, size_t& x_out, size_t& y_out) const {
        x_out = index % N_x_;
        y_out = index / N_x_;
    }

    /**
     * Get current simulation time
     */
    double getCurrentTime() const {
        return current_time_;
    }

    /**
     * Get total steps executed
     */
    uint64_t getTotalSteps() const {
        return total_steps_;
    }

    /**
     * Get total operations executed
     */
    uint64_t getTotalOperations() const {
        return total_operations_;
    }

    /**
     * Set quantum state for a specific node (2D coordinates)
     *
     * @param x X-coordinate
     * @param y Y-coordinate
     * @param real Real part of Ψ
     * @param imag Imaginary part of Ψ
     */
    void setNodePsi(size_t x, size_t y, double real, double imag) {
        size_t index = coordToIndex(x, y);
        if (index < nodes_.size()) {
            nodes_[index].psi = std::complex<double>(real, imag);
            nodes_[index].updateInformationalDensity();
            nodes_[index].updatePhase();
        }
    }

    /**
     * Get quantum state for a specific node (2D coordinates)
     */
    void getNodePsi(size_t x, size_t y, double& real_out, double& imag_out) const {
        size_t index = coordToIndex(x, y);
        if (index < nodes_.size()) {
            real_out = nodes_[index].psi.real();
            imag_out = nodes_[index].psi.imag();
        } else {
            real_out = 0.0;
            imag_out = 0.0;
        }
    }

    /**
     * Set realized field for a specific node (2D coordinates)
     */
    void setNodePhi(size_t x, size_t y, double value) {
        size_t index = coordToIndex(x, y);
        if (index < nodes_.size()) {
            nodes_[index].phi = value;
        }
    }

    /**
     * Get realized field for a specific node (2D coordinates)
     */
    double getNodePhi(size_t x, size_t y) const {
        size_t index = coordToIndex(x, y);
        if (index < nodes_.size()) {
            return nodes_[index].phi;
        }
        return 0.0;
    }

    /**
     * Get informational density for a specific node (2D coordinates)
     */
    double getNodeF(size_t x, size_t y) const {
        size_t index = coordToIndex(x, y);
        if (index < nodes_.size()) {
            return nodes_[index].F;
        }
        return 0.0;
    }

    /**
     * Run mission - execute time evolution
     *
     * @param num_steps Number of time steps to execute
     * @param input_signals Optional driving signals (length: num_steps)
     * @param control_patterns Optional control patterns (length: num_steps)
     */
    void runMission(
        uint64_t num_steps,
        const double* input_signals = nullptr,
        const double* control_patterns = nullptr
    ) {
        auto start_time = std::chrono::high_resolution_clock::now();
        uint64_t operations_this_run = 0;

        for (uint64_t step = 0; step < num_steps; step++) {
            // Apply driving signals if provided
            if (input_signals && control_patterns) {
                IGSOAPhysics2D::applyDriving(
                    nodes_,
                    input_signals[step],
                    control_patterns[step]
                );
                operations_this_run += static_cast<uint64_t>(nodes_.size());
            }

            // Execute one time step (2D version)
            operations_this_run += IGSOAPhysics2D::timeStep(nodes_, config_, N_x_, N_y_);

            // Update counters
            current_time_ += config_.dt;
            total_steps_++;
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time);

        // Update performance metrics
        total_operations_ += operations_this_run;
        last_execution_time_ns_ = duration.count();

        if (operations_this_run > 0) {
            ns_per_op_ = static_cast<double>(duration.count()) / operations_this_run;
            ops_per_sec_ = 1.0e9 / ns_per_op_;
        }
    }

    /**
     * Get performance metrics
     */
    void getMetrics(
        double& out_ns_per_op,
        double& out_ops_per_sec,
        double& out_speedup_factor,
        uint64_t& out_total_ops
    ) const {
        out_ns_per_op = ns_per_op_;
        out_ops_per_sec = ops_per_sec_;
        out_speedup_factor = (ns_per_op_ > 0.0) ? (1.0 / ns_per_op_) : 0.0;  // ops/ns (remove 1D baseline)
        out_total_ops = total_operations_;
    }

    /**
     * Compute total system energy
     * E = ∑_i [|Ψ_i|² + Φ_i²]
     */
    double getTotalEnergy() const {
        return IGSOAPhysics2D::computeTotalEnergy(nodes_);
    }

    /**
     * Compute total entropy production rate
     * Ṡ_total = ∑_i Ṡ_i
     */
    double getTotalEntropyRate() const {
        return IGSOAPhysics2D::computeTotalEntropyRate(nodes_);
    }

    /**
     * Get average informational density
     * <F> = (1/N) ∑_i |Ψ_i|²
     */
    double getAverageInformationalDensity() const {
        double sum = 0.0;
        for (const auto& node : nodes_) {
            sum += node.F;
        }
        return sum / nodes_.size();
    }

    /**
     * Reset engine to initial state
     */
    void reset() {
        for (auto& node : nodes_) {
            node.psi = std::complex<double>(0.0, 0.0);
            node.psi_dot = std::complex<double>(0.0, 0.0);
            node.phi = 0.0;
            node.phi_dot = 0.0;
            node.F = 0.0;
            node.F_gradient = 0.0;
            node.entropy_rate = 0.0;
            node.T_IGS = 0.0;
            node.phase = 0.0;
            node.harmonic_count = 0;
        }

        current_time_ = 0.0;
        total_steps_ = 0;
        total_operations_ = 0;
        ns_per_op_ = 0.0;
        ops_per_sec_ = 0.0;
        last_execution_time_ns_ = 0;
    }

    /**
     * Get direct access to nodes (for advanced use)
     */
    const std::vector<IGSOAComplexNode>& getNodes() const {
        return nodes_;
    }

    /**
     * Get mutable access to nodes (for advanced use)
     */
    std::vector<IGSOAComplexNode>& getNodesMutable() {
        return nodes_;
    }

private:
    IGSOAComplexConfig config_;
    size_t N_x_;  // Lattice width
    size_t N_y_;  // Lattice height
    std::vector<IGSOAComplexNode> nodes_;  // Row-major layout

    // Simulation state
    double current_time_;
    uint64_t total_steps_;
    uint64_t total_operations_;

    // Performance metrics
    double ns_per_op_ = 0.0;
    double ops_per_sec_ = 0.0;
    int64_t last_execution_time_ns_ = 0;
};

} // namespace igsoa
} // namespace dase
