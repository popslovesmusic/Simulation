/**
 * IGSOA Complex Engine - 3D Extension
 *
 * Three-dimensional extension of the IGSOA lattice simulator.  The engine
 * mirrors the 2D implementation while expanding the topology to a toroidal
 * volume of size N_x × N_y × N_z.
 */

#pragma once

#include "igsoa_complex_node.h"
#include "igsoa_physics_3d.h"
#include <chrono>
#include <memory>
#include <string>
#include <vector>
#include <stdexcept>

namespace dase {
namespace igsoa {

class IGSOAComplexEngine3D {
public:
    explicit IGSOAComplexEngine3D(const IGSOAComplexConfig& config,
                                  size_t N_x,
                                  size_t N_y,
                                  size_t N_z)
        : config_(config)
        , N_x_(N_x)
        , N_y_(N_y)
        , N_z_(N_z)
        , nodes_(N_x * N_y * N_z)
        , current_time_(0.0)
        , total_steps_(0)
        , total_operations_(0)
    {
        // Input validation
        if (N_x == 0 || N_y == 0 || N_z == 0) {
            throw std::invalid_argument("Lattice dimensions must be positive");
        }
        if (N_x > 512 || N_y > 512 || N_z > 512) {
            throw std::invalid_argument("Lattice dimension too large (max 512 per axis)");
        }
        const size_t total = N_x * N_y * N_z;
        if (total > 100'000'000) {
            throw std::invalid_argument("Total nodes exceeds limit (100M max)");
        }

        for (auto& node : nodes_) {
            node.R_c = config.R_c_default;
            node.kappa = config.kappa;
            node.gamma = config.gamma;
        }
    }

    size_t getNx() const { return N_x_; }
    size_t getNy() const { return N_y_; }
    size_t getNz() const { return N_z_; }
    size_t getTotalNodes() const { return nodes_.size(); }

    size_t coordToIndex(size_t x, size_t y, size_t z) const {
        #ifndef NDEBUG
        if (x >= N_x_ || y >= N_y_ || z >= N_z_) {
            throw std::out_of_range("3D coordinates out of bounds");
        }
        #endif
        return z * N_x_ * N_y_ + y * N_x_ + x;
    }

    void indexToCoord(size_t index, size_t& x_out, size_t& y_out, size_t& z_out) const {
        x_out = index % N_x_;
        y_out = (index / N_x_) % N_y_;
        z_out = index / (N_x_ * N_y_);
    }

    double getCurrentTime() const { return current_time_; }
    uint64_t getTotalSteps() const { return total_steps_; }
    uint64_t getTotalOperations() const { return total_operations_; }

    void setNodePsi(size_t x, size_t y, size_t z, double real, double imag) {
        size_t index = coordToIndex(x, y, z);
        if (index < nodes_.size()) {
            nodes_[index].psi = std::complex<double>(real, imag);
            nodes_[index].updateInformationalDensity();
            nodes_[index].updatePhase();
        }
    }

    void getNodePsi(size_t x, size_t y, size_t z, double& real_out, double& imag_out) const {
        size_t index = coordToIndex(x, y, z);
        if (index < nodes_.size()) {
            real_out = nodes_[index].psi.real();
            imag_out = nodes_[index].psi.imag();
        } else {
            real_out = 0.0;
            imag_out = 0.0;
        }
    }

    void setNodePhi(size_t x, size_t y, size_t z, double value) {
        size_t index = coordToIndex(x, y, z);
        if (index < nodes_.size()) {
            nodes_[index].phi = value;
        }
    }

    double getNodePhi(size_t x, size_t y, size_t z) const {
        size_t index = coordToIndex(x, y, z);
        if (index < nodes_.size()) {
            return nodes_[index].phi;
        }
        return 0.0;
    }

    double getNodeF(size_t x, size_t y, size_t z) const {
        size_t index = coordToIndex(x, y, z);
        if (index < nodes_.size()) {
            return nodes_[index].F;
        }
        return 0.0;
    }

    void runMission(uint64_t num_steps,
                    const double* input_signals = nullptr,
                    const double* control_patterns = nullptr) {
        auto start_time = std::chrono::high_resolution_clock::now();
        uint64_t operations_this_run = 0;

        for (uint64_t step = 0; step < num_steps; ++step) {
            if (input_signals && control_patterns) {
                IGSOAPhysics3D::applyDriving(nodes_, input_signals[step], control_patterns[step]);
                operations_this_run += static_cast<uint64_t>(nodes_.size());
            }

            operations_this_run += IGSOAPhysics3D::timeStep(nodes_, config_, N_x_, N_y_, N_z_);
            current_time_ += config_.dt;
            total_steps_++;
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time);

        total_operations_ += operations_this_run;
        last_execution_time_ns_ = duration.count();
        if (operations_this_run > 0) {
            ns_per_op_ = static_cast<double>(duration.count()) / operations_this_run;
            ops_per_sec_ = 1.0e9 / ns_per_op_;
        }
    }

    const std::vector<IGSOAComplexNode>& getNodes() const { return nodes_; }
    std::vector<IGSOAComplexNode>& getNodesMutable() { return nodes_; }

    void reset() {
        for (auto& node : nodes_) {
            node.psi = std::complex<double>(0.0, 0.0);
            node.phi = 0.0;
            node.F = 0.0;
            node.phase = 0.0;
            node.psi_dot = std::complex<double>(0.0, 0.0);
        }
        current_time_ = 0.0;
        total_steps_ = 0;
        total_operations_ = 0;
        last_execution_time_ns_ = 0;
        ns_per_op_ = 0.0;
        ops_per_sec_ = 0.0;
    }

    void getMetrics(double& ns_per_op_out,
                    double& ops_per_sec_out,
                    double& speedup_factor_out,
                    uint64_t& total_operations_out) const {
        ns_per_op_out = ns_per_op_;
        ops_per_sec_out = ops_per_sec_;
        speedup_factor_out = speedup_factor_;
        total_operations_out = total_operations_;
    }

    void setSpeedupFactor(double factor) { speedup_factor_ = factor; }

private:
    IGSOAComplexConfig config_;
    size_t N_x_;
    size_t N_y_;
    size_t N_z_;
    std::vector<IGSOAComplexNode> nodes_;

    double current_time_;
    uint64_t total_steps_;
    uint64_t total_operations_;

    double ns_per_op_ = 0.0;
    double ops_per_sec_ = 0.0;
    double speedup_factor_ = 1.0;
    uint64_t last_execution_time_ns_ = 0;
};

} // namespace igsoa
} // namespace dase

