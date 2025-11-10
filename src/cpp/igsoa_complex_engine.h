/**
 * IGSOA Complex Engine
 *
 * Complete engine implementation for IGSOA (Informational Ground State -
 * Ontological Asymmetry) framework with complex-valued quantum states.
 *
 * This engine provides a high-level interface for:
 * - Creating and managing IGSOA networks
 * - Running time evolution simulations
 * - Accessing node states and metrics
 * - Performance measurement
 */

#pragma once

#include "igsoa_complex_node.h"
#include "igsoa_physics.h"
#include <vector>
#include <memory>
#include <chrono>
#include <string>

namespace dase {
namespace igsoa {

/**
 * IGSOA Complex Engine
 *
 * Main engine class for IGSOA simulations
 */
class IGSOAComplexEngine {
public:
    /**
     * Constructor
     *
     * @param config Engine configuration
     */
    explicit IGSOAComplexEngine(const IGSOAComplexConfig& config)
        : config_(config)
        , nodes_(config.num_nodes)
        , current_time_(0.0)
        , total_steps_(0)
        , total_operations_(0)
    {
        // Initialize all nodes with configuration
        for (auto& node : nodes_) {
            node.R_c = config.R_c_default;
            node.kappa = config.kappa;
            node.gamma = config.gamma;
        }
    }

    /**
     * Get number of nodes
     */
    size_t getNumNodes() const {
        return nodes_.size();
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
     * Set quantum state for a specific node
     *
     * @param index Node index
     * @param real Real part of Ψ
     * @param imag Imaginary part of Ψ
     */
    void setNodePsi(size_t index, double real, double imag) {
        if (index < nodes_.size()) {
            nodes_[index].psi = std::complex<double>(real, imag);
            nodes_[index].updateInformationalDensity();
            nodes_[index].updatePhase();
        }
    }

    /**
     * Get quantum state for a specific node
     *
     * @param index Node index
     * @param real_out Output: real part of Ψ
     * @param imag_out Output: imaginary part of Ψ
     */
    void getNodePsi(size_t index, double& real_out, double& imag_out) const {
        if (index < nodes_.size()) {
            real_out = nodes_[index].psi.real();
            imag_out = nodes_[index].psi.imag();
        } else {
            real_out = 0.0;
            imag_out = 0.0;
        }
    }

    /**
     * Set realized field for a specific node
     *
     * @param index Node index
     * @param value Φ value
     */
    void setNodePhi(size_t index, double value) {
        if (index < nodes_.size()) {
            nodes_[index].phi = value;
        }
    }

    /**
     * Get realized field for a specific node
     *
     * @param index Node index
     * @return Φ value
     */
    double getNodePhi(size_t index) const {
        if (index < nodes_.size()) {
            return nodes_[index].phi;
        }
        return 0.0;
    }

    /**
     * Get informational density for a specific node
     *
     * @param index Node index
     * @return F = |Ψ|²
     */
    double getNodeF(size_t index) const {
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
                IGSOAPhysics::applyDriving(
                    nodes_,
                    input_signals[step],
                    control_patterns[step]
                );
                operations_this_run += static_cast<uint64_t>(nodes_.size());
            }

            // Execute one time step
            operations_this_run += IGSOAPhysics::timeStep(nodes_, config_);

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
     *
     * @param out_ns_per_op Nanoseconds per operation
     * @param out_ops_per_sec Operations per second
     * @param out_speedup_factor Speedup vs 15,500ns baseline
     * @param out_total_ops Total operations completed
     */
    void getMetrics(
        double& out_ns_per_op,
        double& out_ops_per_sec,
        double& out_speedup_factor,
        uint64_t& out_total_ops
    ) const {
        out_ns_per_op = ns_per_op_;
        out_ops_per_sec = ops_per_sec_;
        out_speedup_factor = (ns_per_op_ > 0.0) ? (15500.0 / ns_per_op_) : 0.0;  // vs baseline
        out_total_ops = total_operations_;
    }

    /**
     * Compute total system energy
     * E = ∑_i [|Ψ_i|² + Φ_i²]
     */
    double getTotalEnergy() const {
        return IGSOAPhysics::computeTotalEnergy(nodes_);
    }

    /**
     * Compute total entropy production rate
     * Ṡ_total = ∑_i Ṡ_i
     */
    double getTotalEntropyRate() const {
        return IGSOAPhysics::computeTotalEntropyRate(nodes_);
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
     * Get average phase
     * <θ> = (1/N) ∑_i arg(Ψ_i)
     */
    double getAveragePhase() const {
        double sum = 0.0;
        for (const auto& node : nodes_) {
            sum += node.phase;
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
    std::vector<IGSOAComplexNode> nodes_;

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
