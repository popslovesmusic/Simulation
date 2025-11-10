/**
 * Comprehensive Test Suite for 2D IGSOA Engine
 *
 * Tests:
 * 1. Compilation and linking
 * 2. Basic functionality
 * 3. Coordinate transformations
 * 4. Distance calculations
 * 5. State initialization
 * 6. Time evolution
 * 7. Physics validation
 */

#include "../src/cpp/igsoa_complex_engine_2d.h"
#include "../src/cpp/igsoa_state_init_2d.h"
#include <iostream>
#include <cmath>
#include <cassert>
#include <iomanip>

using namespace dase::igsoa;

// Test result tracking
struct TestResults {
    int passed = 0;
    int failed = 0;

    void pass(const std::string& test_name) {
        std::cout << "[PASS] " << test_name << std::endl;
        passed++;
    }

    void fail(const std::string& test_name, const std::string& reason) {
        std::cout << "[FAIL] " << test_name << ": " << reason << std::endl;
        failed++;
    }

    void report() {
        std::cout << "\n======================================" << std::endl;
        std::cout << "TEST RESULTS" << std::endl;
        std::cout << "======================================" << std::endl;
        std::cout << "Passed: " << passed << std::endl;
        std::cout << "Failed: " << failed << std::endl;
        std::cout << "Total:  " << (passed + failed) << std::endl;

        if (failed == 0) {
            std::cout << "\n✓ ALL TESTS PASSED" << std::endl;
        } else {
            std::cout << "\n✗ SOME TESTS FAILED" << std::endl;
        }
    }
};

TestResults results;

// Helper to check floating point equality
bool approxEqual(double a, double b, double epsilon = 1e-6) {
    return std::abs(a - b) < epsilon;
}

//============================================================================
// TEST 1: Engine Creation
//============================================================================
void test_engine_creation() {
    std::cout << "\n[TEST] Engine Creation" << std::endl;

    try {
        IGSOAComplexConfig config;
        config.num_nodes = 64 * 64;
        config.R_c_default = 1.0;
        config.kappa = 1.0;
        config.gamma = 0.1;
        config.dt = 0.01;
        config.normalize_psi = false;

        IGSOAComplexEngine2D engine(config, 64, 64);

        // Verify dimensions
        if (engine.getNx() != 64) {
            results.fail("Engine Creation", "N_x incorrect");
            return;
        }
        if (engine.getNy() != 64) {
            results.fail("Engine Creation", "N_y incorrect");
            return;
        }
        if (engine.getTotalNodes() != 4096) {
            results.fail("Engine Creation", "Total nodes incorrect");
            return;
        }

        results.pass("Engine Creation");
    } catch (const std::exception& e) {
        results.fail("Engine Creation", std::string("Exception: ") + e.what());
    }
}

//============================================================================
// TEST 2: Coordinate Transformations
//============================================================================
void test_coordinate_transformations() {
    std::cout << "\n[TEST] Coordinate Transformations" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 32 * 32;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 32, 32);

    // Test known coordinates
    struct TestCase {
        size_t x, y, expected_index;
    };

    TestCase cases[] = {
        {0, 0, 0},
        {1, 0, 1},
        {0, 1, 32},
        {31, 31, 32*31 + 31},
        {15, 16, 32*16 + 15}
    };

    for (const auto& tc : cases) {
        size_t index = engine.coordToIndex(tc.x, tc.y);
        if (index != tc.expected_index) {
            results.fail("Coordinate Transformations",
                        "coordToIndex failed for (" + std::to_string(tc.x) + "," +
                        std::to_string(tc.y) + "): got " + std::to_string(index) +
                        " expected " + std::to_string(tc.expected_index));
            return;
        }

        // Test inverse
        size_t x_back, y_back;
        engine.indexToCoord(index, x_back, y_back);
        if (x_back != tc.x || y_back != tc.y) {
            results.fail("Coordinate Transformations",
                        "indexToCoord failed for index " + std::to_string(index));
            return;
        }
    }

    results.pass("Coordinate Transformations");
}

//============================================================================
// TEST 3: Wrapped Distance (1D)
//============================================================================
void test_wrapped_distance_1d() {
    std::cout << "\n[TEST] Wrapped Distance 1D" << std::endl;

    size_t N = 100;

    // Test cases: (coord1, coord2, expected_distance)
    struct TestCase {
        int c1, c2;
        double expected;
    };

    TestCase cases[] = {
        {0, 0, 0.0},      // Same point
        {0, 1, 1.0},      // Adjacent
        {0, 10, 10.0},    // Direct
        {0, 99, 1.0},     // Wrap around (99 = -1)
        {10, 90, 20.0},   // Wrap (80 direct, 20 wrapped)
        {25, 75, 50.0}    // Middle (no wrapping)
    };

    for (const auto& tc : cases) {
        double dist = IGSOAPhysics2D::wrappedDistance1D(tc.c1, tc.c2, N);
        if (!approxEqual(dist, tc.expected, 0.01)) {
            results.fail("Wrapped Distance 1D",
                        "wrappedDistance1D(" + std::to_string(tc.c1) + "," +
                        std::to_string(tc.c2) + ") = " + std::to_string(dist) +
                        ", expected " + std::to_string(tc.expected));
            return;
        }
    }

    results.pass("Wrapped Distance 1D");
}

//============================================================================
// TEST 4: Wrapped Distance (2D)
//============================================================================
void test_wrapped_distance_2d() {
    std::cout << "\n[TEST] Wrapped Distance 2D" << std::endl;

    size_t N_x = 100, N_y = 100;

    // Test cases: (x1, y1, x2, y2, expected_distance)
    struct TestCase {
        int x1, y1, x2, y2;
        double expected;
    };

    TestCase cases[] = {
        {0, 0, 0, 0, 0.0},                         // Same point
        {0, 0, 1, 0, 1.0},                         // Adjacent in x
        {0, 0, 0, 1, 1.0},                         // Adjacent in y
        {0, 0, 3, 4, 5.0},                         // Pythagorean triple
        {0, 0, 99, 0, 1.0},                        // Wrap in x
        {0, 0, 0, 99, 1.0},                        // Wrap in y
        {0, 0, 99, 99, std::sqrt(2.0)},           // Wrap in both
        {50, 50, 60, 60, std::sqrt(200.0)}        // No wrap, diagonal
    };

    for (const auto& tc : cases) {
        double dist = IGSOAPhysics2D::wrappedDistance2D(
            tc.x1, tc.y1, tc.x2, tc.y2, N_x, N_y
        );
        if (!approxEqual(dist, tc.expected, 0.01)) {
            results.fail("Wrapped Distance 2D",
                        "wrappedDistance2D(" + std::to_string(tc.x1) + "," +
                        std::to_string(tc.y1) + "," + std::to_string(tc.x2) + "," +
                        std::to_string(tc.y2) + ") = " + std::to_string(dist) +
                        ", expected " + std::to_string(tc.expected));
            return;
        }
    }

    results.pass("Wrapped Distance 2D");
}

//============================================================================
// TEST 5: Node State Access
//============================================================================
void test_node_state_access() {
    std::cout << "\n[TEST] Node State Access" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 16 * 16;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 16, 16);

    // Set and get Ψ
    engine.setNodePsi(5, 7, 3.5, -2.1);
    double real, imag;
    engine.getNodePsi(5, 7, real, imag);

    if (!approxEqual(real, 3.5, 1e-6) || !approxEqual(imag, -2.1, 1e-6)) {
        results.fail("Node State Access", "Psi set/get mismatch");
        return;
    }

    // Set and get Φ
    engine.setNodePhi(10, 12, 7.8);
    double phi = engine.getNodePhi(10, 12);

    if (!approxEqual(phi, 7.8, 1e-6)) {
        results.fail("Node State Access", "Phi set/get mismatch");
        return;
    }

    // Check F updated correctly
    double F = engine.getNodeF(5, 7);
    double expected_F = 3.5*3.5 + 2.1*2.1;

    if (!approxEqual(F, expected_F, 1e-6)) {
        results.fail("Node State Access", "F not updated correctly");
        return;
    }

    results.pass("Node State Access");
}

//============================================================================
// TEST 6: Circular Gaussian Initialization
//============================================================================
void test_circular_gaussian() {
    std::cout << "\n[TEST] Circular Gaussian Initialization" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 32 * 32;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 32, 32);

    // Initialize circular Gaussian
    IGSOAStateInit2D::initCircularGaussian(
        engine,
        100.0,  // amplitude
        16.0,   // center_x
        16.0,   // center_y
        5.0,    // sigma
        0.0,    // baseline_phi
        "overwrite",
        1.0
    );

    // Check center has maximum amplitude
    double center_F = engine.getNodeF(16, 16);
    double expected_center = 100.0 * 100.0;  // |A|²

    if (!approxEqual(center_F, expected_center, 1.0)) {
        results.fail("Circular Gaussian Initialization",
                    "Center F = " + std::to_string(center_F) +
                    ", expected ~" + std::to_string(expected_center));
        return;
    }

    // Check decay away from center
    double edge_F = engine.getNodeF(26, 16);  // 10 sites away (2σ)
    double expected_edge = 100.0 * 100.0 * std::exp(-2.0*2.0);  // exp(-r²/σ²)

    if (!approxEqual(edge_F, expected_edge, 100.0)) {
        results.fail("Circular Gaussian Initialization",
                    "Edge F doesn't match Gaussian profile");
        return;
    }

    results.pass("Circular Gaussian Initialization");
}

//============================================================================
// TEST 7: Center of Mass Computation
//============================================================================
void test_center_of_mass() {
    std::cout << "\n[TEST] Center of Mass Computation" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 32 * 32;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 32, 32);

    // Initialize Gaussian at known position
    double init_x = 16.0;
    double init_y = 16.0;

    IGSOAStateInit2D::initCircularGaussian(
        engine, 10.0, init_x, init_y, 3.0, 0.0, "overwrite", 1.0
    );

    // Compute center of mass
    double x_cm, y_cm;
    IGSOAStateInit2D::computeCenterOfMass(engine, x_cm, y_cm);

    // Should be very close to initialized center
    if (!approxEqual(x_cm, init_x, 0.5) || !approxEqual(y_cm, init_y, 0.5)) {
        results.fail("Center of Mass Computation",
                    "CM = (" + std::to_string(x_cm) + "," + std::to_string(y_cm) +
                    "), expected (" + std::to_string(init_x) + "," + std::to_string(init_y) + ")");
        return;
    }

    results.pass("Center of Mass Computation");
}

//============================================================================
// TEST 8: Time Evolution (Basic)
//============================================================================
void test_time_evolution() {
    std::cout << "\n[TEST] Time Evolution (Basic)" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 16 * 16;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 16, 16);

    // Initialize state
    IGSOAStateInit2D::initCircularGaussian(
        engine, 5.0, 8.0, 8.0, 2.0, 0.0, "overwrite", 1.0
    );

    // Record initial state
    double initial_energy = engine.getTotalEnergy();

    // Run evolution
    engine.runMission(5);

    // Check that time advanced
    if (engine.getTotalSteps() != 5) {
        results.fail("Time Evolution", "Step count incorrect");
        return;
    }

    double expected_time = 5 * config.dt;
    if (!approxEqual(engine.getCurrentTime(), expected_time, 1e-9)) {
        results.fail("Time Evolution", "Simulation time incorrect");
        return;
    }

    // Energy should have changed (not conserved due to dissipation)
    double final_energy = engine.getTotalEnergy();
    if (approxEqual(initial_energy, final_energy, 1e-3)) {
        results.fail("Time Evolution", "Energy didn't change (physics not running?)");
        return;
    }

    results.pass("Time Evolution (Basic)");
}

//============================================================================
// TEST 9: Zero Drift Validation
//============================================================================
void test_zero_drift() {
    std::cout << "\n[TEST] Zero Drift Validation" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 64 * 64;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 64, 64);

    // Initialize Gaussian at center
    double init_x = 32.0;
    double init_y = 32.0;

    IGSOAStateInit2D::initCircularGaussian(
        engine, 100.0, init_x, init_y, 10.0, 0.0, "blend", 1.0
    );

    // Measure initial center of mass
    double x_cm_initial, y_cm_initial;
    IGSOAStateInit2D::computeCenterOfMass(engine, x_cm_initial, y_cm_initial);

    // Evolve
    engine.runMission(10);

    // Measure final center of mass
    double x_cm_final, y_cm_final;
    IGSOAStateInit2D::computeCenterOfMass(engine, x_cm_final, y_cm_final);

    // Compute 2D drift
    double drift_x = x_cm_final - x_cm_initial;
    double drift_y = y_cm_final - y_cm_initial;
    double total_drift = std::sqrt(drift_x*drift_x + drift_y*drift_y);

    std::cout << "  Initial CM: (" << x_cm_initial << ", " << y_cm_initial << ")" << std::endl;
    std::cout << "  Final CM:   (" << x_cm_final << ", " << y_cm_final << ")" << std::endl;
    std::cout << "  Drift:      " << total_drift << " nodes" << std::endl;

    // Drift threshold: 1% of lattice diagonal
    double lattice_diagonal = std::sqrt(64.0*64.0 + 64.0*64.0);
    double threshold = 0.01 * lattice_diagonal;  // ~0.9 nodes

    if (total_drift > threshold) {
        results.fail("Zero Drift Validation",
                    "Drift = " + std::to_string(total_drift) +
                    " exceeds threshold " + std::to_string(threshold));
        return;
    }

    results.pass("Zero Drift Validation");
}

//============================================================================
// TEST 10: Engine Reset
//============================================================================
void test_engine_reset() {
    std::cout << "\n[TEST] Engine Reset" << std::endl;

    IGSOAComplexConfig config;
    config.num_nodes = 16 * 16;
    config.R_c_default = 1.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;

    IGSOAComplexEngine2D engine(config, 16, 16);

    // Initialize and evolve
    IGSOAStateInit2D::initCircularGaussian(
        engine, 10.0, 8.0, 8.0, 2.0, 0.0, "overwrite", 1.0
    );
    engine.runMission(5);

    // Reset
    engine.reset();

    // Check all counters reset
    if (engine.getTotalSteps() != 0 ||
        engine.getCurrentTime() != 0.0 ||
        engine.getTotalOperations() != 0) {
        results.fail("Engine Reset", "Counters not reset");
        return;
    }

    // Check nodes reset
    double F_sum = 0.0;
    for (size_t y = 0; y < 16; y++) {
        for (size_t x = 0; x < 16; x++) {
            F_sum += engine.getNodeF(x, y);
        }
    }

    if (!approxEqual(F_sum, 0.0, 1e-9)) {
        results.fail("Engine Reset", "Nodes not reset to zero");
        return;
    }

    results.pass("Engine Reset");
}

//============================================================================
// MAIN
//============================================================================
int main() {
    std::cout << "======================================" << std::endl;
    std::cout << "2D IGSOA ENGINE COMPREHENSIVE TEST" << std::endl;
    std::cout << "======================================" << std::endl;

    test_engine_creation();
    test_coordinate_transformations();
    test_wrapped_distance_1d();
    test_wrapped_distance_2d();
    test_node_state_access();
    test_circular_gaussian();
    test_center_of_mass();
    test_time_evolution();
    test_zero_drift();
    test_engine_reset();

    results.report();

    return (results.failed == 0) ? 0 : 1;
}
