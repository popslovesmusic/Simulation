/**
 * Unit Tests for IGSOA Complex Engine
 */

#define _USE_MATH_DEFINES
#include <cmath>
#include "igsoa_complex_engine.h"
#include <iostream>
#include <iomanip>
#include <cassert>
#include <vector>

using namespace dase::igsoa;

void test_engine_creation() {
    std::cout << "Test: Engine Creation... ";

    IGSOAComplexConfig config;
    config.num_nodes = 100;

    IGSOAComplexEngine engine(config);

    assert(engine.getNumNodes() == 100);
    assert(engine.getCurrentTime() == 0.0);
    assert(engine.getTotalSteps() == 0);

    std::cout << "PASS" << std::endl;
}

void test_set_get_psi() {
    std::cout << "Test: Set/Get Quantum State... ";

    IGSOAComplexConfig config;
    config.num_nodes = 10;

    IGSOAComplexEngine engine(config);

    // Set state
    engine.setNodePsi(5, 3.0, 4.0);

    // Get state
    double real, imag;
    engine.getNodePsi(5, real, imag);

    assert(real == 3.0);
    assert(imag == 4.0);

    // Check F was updated
    double F = engine.getNodeF(5);
    assert(std::abs(F - 25.0) < 1e-10);  // |3+4i|² = 25

    std::cout << "PASS" << std::endl;
}

void test_set_get_phi() {
    std::cout << "Test: Set/Get Realized Field... ";

    IGSOAComplexConfig config;
    config.num_nodes = 10;

    IGSOAComplexEngine engine(config);

    engine.setNodePhi(3, 2.5);

    double phi = engine.getNodePhi(3);
    assert(phi == 2.5);

    std::cout << "PASS" << std::endl;
}

void test_simple_mission() {
    std::cout << "Test: Simple Mission Execution... ";

    IGSOAComplexConfig config;
    config.num_nodes = 50;
    config.dt = 0.01;

    IGSOAComplexEngine engine(config);

    // Initialize with some energy
    for (size_t i = 0; i < engine.getNumNodes(); i++) {
        engine.setNodePsi(i, 0.1, 0.1);
    }

    // Run mission
    engine.runMission(100);

    // Check execution happened
    assert(engine.getTotalSteps() == 100);
    assert(engine.getCurrentTime() > 0.0);
    assert(engine.getTotalOperations() == 100 * 50);

    // Check metrics
    double ns_per_op, ops_per_sec, speedup;
    uint64_t total_ops;
    engine.getMetrics(ns_per_op, ops_per_sec, speedup, total_ops);

    assert(total_ops == 5000);
    assert(ns_per_op > 0.0);
    assert(ops_per_sec > 0.0);

    std::cout << "PASS (" << std::fixed << std::setprecision(2)
              << ns_per_op << " ns/op)" << std::endl;
}

void test_mission_with_driving() {
    std::cout << "Test: Mission with Driving Signals... ";

    IGSOAComplexConfig config;
    config.num_nodes = 20;
    config.dt = 0.01;

    IGSOAComplexEngine engine(config);

    // Create driving signals
    const int num_steps = 100;
    std::vector<double> input_signals(num_steps);
    std::vector<double> control_patterns(num_steps);

    for (int i = 0; i < num_steps; i++) {
        input_signals[i] = 0.1 * std::sin(i * 0.1);
        control_patterns[i] = 0.1 * std::cos(i * 0.1);
    }

    // Run with driving
    engine.runMission(num_steps, input_signals.data(), control_patterns.data());

    // System should have absorbed energy
    double total_energy = engine.getTotalEnergy();
    assert(total_energy > 0.0);

    std::cout << "PASS (energy: " << std::scientific << std::setprecision(2)
              << total_energy << ")" << std::endl;
}

void test_energy_entropy() {
    std::cout << "Test: Energy and Entropy Computation... ";

    IGSOAComplexConfig config;
    config.num_nodes = 30;

    IGSOAComplexEngine engine(config);

    // Set some states
    for (size_t i = 0; i < engine.getNumNodes(); i++) {
        engine.setNodePsi(i, 0.5, 0.5);
        engine.setNodePhi(i, 0.3);
    }

    // Run one step to update derived quantities
    engine.runMission(1);

    double energy = engine.getTotalEnergy();
    double entropy_rate = engine.getTotalEntropyRate();

    // Energy should be positive
    assert(energy > 0.0);

    // Entropy rate should be finite (may be zero or positive)
    assert(std::isfinite(entropy_rate));

    std::cout << "PASS (E=" << std::fixed << std::setprecision(2)
              << energy << ", Ṡ=" << std::scientific << std::setprecision(2)
              << entropy_rate << ")" << std::endl;
}

void test_average_quantities() {
    std::cout << "Test: Average Quantities... ";

    IGSOAComplexConfig config;
    config.num_nodes = 10;

    IGSOAComplexEngine engine(config);

    // Set uniform state
    for (size_t i = 0; i < engine.getNumNodes(); i++) {
        engine.setNodePsi(i, 1.0, 0.0);  // All on real axis
    }

    double avg_F = engine.getAverageInformationalDensity();
    double avg_phase = engine.getAveragePhase();

    // F should be 1.0 for all nodes
    assert(std::abs(avg_F - 1.0) < 1e-10);

    // Phase should be 0 (all on real axis)
    assert(std::abs(avg_phase) < 1e-10);

    std::cout << "PASS" << std::endl;
}

void test_reset() {
    std::cout << "Test: Engine Reset... ";

    IGSOAComplexConfig config;
    config.num_nodes = 20;

    IGSOAComplexEngine engine(config);

    // Run some evolution
    for (size_t i = 0; i < engine.getNumNodes(); i++) {
        engine.setNodePsi(i, 1.0, 1.0);
    }
    engine.runMission(50);

    // Reset
    engine.reset();

    // Check everything is zeroed
    assert(engine.getCurrentTime() == 0.0);
    assert(engine.getTotalSteps() == 0);
    assert(engine.getTotalOperations() == 0);
    assert(engine.getTotalEnergy() == 0.0);

    double real, imag;
    engine.getNodePsi(0, real, imag);
    assert(real == 0.0);
    assert(imag == 0.0);

    std::cout << "PASS" << std::endl;
}

void test_performance_benchmark() {
    std::cout << "Test: Performance Benchmark... ";

    IGSOAComplexConfig config;
    config.num_nodes = 1024;
    config.dt = 0.01;

    IGSOAComplexEngine engine(config);

    // Initialize
    for (size_t i = 0; i < engine.getNumNodes(); i++) {
        engine.setNodePsi(i, 0.01, 0.01);
    }

    // Run benchmark
    const int num_steps = 10000;
    engine.runMission(num_steps);

    // Get metrics
    double ns_per_op, ops_per_sec, speedup;
    uint64_t total_ops;
    engine.getMetrics(ns_per_op, ops_per_sec, speedup, total_ops);

    // Should have completed
    assert(total_ops == num_steps * 1024);

    std::cout << "PASS" << std::endl;
    std::cout << "       Performance: " << std::fixed << std::setprecision(2)
              << ns_per_op << " ns/op, "
              << std::setprecision(0) << ops_per_sec / 1e6 << " M ops/sec"
              << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "IGSOA Complex Engine Tests" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    try {
        test_engine_creation();
        test_set_get_psi();
        test_set_get_phi();
        test_simple_mission();
        test_mission_with_driving();
        test_energy_entropy();
        test_average_quantities();
        test_reset();
        test_performance_benchmark();

        std::cout << std::endl;
        std::cout << "========================================" << std::endl;
        std::cout << "All tests PASSED! ✓" << std::endl;
        std::cout << "========================================" << std::endl;

        return 0;

    } catch (const std::exception& e) {
        std::cerr << std::endl;
        std::cerr << "FATAL ERROR: " << e.what() << std::endl;
        return 1;
    }
}
