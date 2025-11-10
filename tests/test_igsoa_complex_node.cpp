/**
 * Unit Tests for IGSOAComplexNode
 *
 * Validates the basic functionality of the IGSOA Complex node structure
 */

#define _USE_MATH_DEFINES
#include <cmath>
#include "igsoa_complex_node.h"
#include <iostream>
#include <iomanip>
#include <cassert>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace dase::igsoa;

// Test helper: Check if two doubles are approximately equal
bool approx_equal(double a, double b, double epsilon = 1e-10) {
    return std::abs(a - b) < epsilon;
}

// Test helper: Check if two complex numbers are approximately equal
bool approx_equal_complex(const std::complex<double>& a, const std::complex<double>& b, double epsilon = 1e-10) {
    return approx_equal(a.real(), b.real(), epsilon) && approx_equal(a.imag(), b.imag(), epsilon);
}

void test_default_construction() {
    std::cout << "Test: Default Construction... ";

    IGSOAComplexNode node;

    // Check initial state
    assert(node.psi == std::complex<double>(0.0, 0.0));
    assert(node.phi == 0.0);
    assert(node.F == 0.0);
    assert(node.R_c == 1e-34);
    assert(node.T_IGS == 0.0);
    assert(node.kappa == 1.0);
    assert(node.gamma == 0.1);

    std::cout << "PASS" << std::endl;
}

void test_informational_density() {
    std::cout << "Test: Informational Density Calculation... ";

    IGSOAComplexNode node;

    // Test 1: Pure real state
    node.psi = std::complex<double>(3.0, 0.0);
    node.updateInformationalDensity();
    assert(approx_equal(node.F, 9.0));  // |3+0i|² = 9
    assert(approx_equal(node.T_IGS, 9.0));

    // Test 2: Pure imaginary state
    node.psi = std::complex<double>(0.0, 4.0);
    node.updateInformationalDensity();
    assert(approx_equal(node.F, 16.0));  // |0+4i|² = 16

    // Test 3: Complex state (3-4-5 triangle)
    node.psi = std::complex<double>(3.0, 4.0);
    node.updateInformationalDensity();
    assert(approx_equal(node.F, 25.0));  // |3+4i|² = 9+16 = 25

    std::cout << "PASS" << std::endl;
}

void test_phase_calculation() {
    std::cout << "Test: Phase Calculation... ";

    IGSOAComplexNode node;

    // Test 1: Positive real axis (phase = 0)
    node.psi = std::complex<double>(1.0, 0.0);
    node.updatePhase();
    assert(approx_equal(node.phase, 0.0));

    // Test 2: Positive imaginary axis (phase = π/2)
    node.psi = std::complex<double>(0.0, 1.0);
    node.updatePhase();
    assert(approx_equal(node.phase, M_PI / 2.0));

    // Test 3: Negative real axis (phase = π)
    node.psi = std::complex<double>(-1.0, 0.0);
    node.updatePhase();
    assert(approx_equal(node.phase, M_PI));

    // Test 4: 45-degree angle (phase = π/4)
    node.psi = std::complex<double>(1.0, 1.0);
    node.updatePhase();
    assert(approx_equal(node.phase, M_PI / 4.0));

    std::cout << "PASS" << std::endl;
}

void test_normalization() {
    std::cout << "Test: Quantum State Normalization... ";

    IGSOAComplexNode node;

    // Test 1: Normalize state with magnitude 5
    node.psi = std::complex<double>(3.0, 4.0);  // |Ψ| = 5
    node.normalize();
    assert(approx_equal(std::abs(node.psi), 1.0));
    assert(approx_equal(node.psi.real(), 0.6));   // 3/5
    assert(approx_equal(node.psi.imag(), 0.8));   // 4/5

    // Test 2: Already normalized state
    node.psi = std::complex<double>(1.0, 0.0);
    node.normalize();
    assert(approx_equal(std::abs(node.psi), 1.0));

    // Test 3: Zero state (should not divide by zero)
    node.psi = std::complex<double>(0.0, 0.0);
    node.normalize();
    assert(node.psi == std::complex<double>(0.0, 0.0));

    std::cout << "PASS" << std::endl;
}

void test_entropy_rate() {
    std::cout << "Test: Entropy Production Rate... ";

    IGSOAComplexNode node;
    node.R_c = 1.0;  // Set to 1 for easier calculation

    // Test 1: Φ = Re[Ψ] (no coupling difference, zero entropy)
    node.phi = 2.0;
    node.psi = std::complex<double>(2.0, 1.0);
    node.updateEntropyRate();
    assert(approx_equal(node.entropy_rate, 0.0));

    // Test 2: Φ - Re[Ψ] = 3 (entropy = R_c * 9)
    node.phi = 5.0;
    node.psi = std::complex<double>(2.0, 1.0);
    node.updateEntropyRate();
    assert(approx_equal(node.entropy_rate, 9.0));  // 1.0 * (5-2)²

    // Test 3: Different R_c
    node.R_c = 2.0;
    node.updateEntropyRate();
    assert(approx_equal(node.entropy_rate, 18.0));  // 2.0 * (5-2)²

    std::cout << "PASS" << std::endl;
}

void test_config_defaults() {
    std::cout << "Test: Configuration Defaults... ";

    IGSOAComplexConfig config;

    assert(config.num_nodes == 1024);
    assert(config.R_c_default == 1e-34);
    assert(config.kappa == 1.0);
    assert(config.gamma == 0.1);
    assert(config.dt == 0.01);
    assert(config.normalize_psi == true);

    std::cout << "PASS" << std::endl;
}

void test_complex_arithmetic() {
    std::cout << "Test: Complex Number Operations... ";

    IGSOAComplexNode node;

    // Test complex addition
    node.psi = std::complex<double>(1.0, 2.0);
    node.psi_dot = std::complex<double>(0.5, 0.3);
    std::complex<double> result = node.psi + node.psi_dot;
    assert(approx_equal(result.real(), 1.5));
    assert(approx_equal(result.imag(), 2.3));

    // Test complex multiplication
    std::complex<double> a(2.0, 3.0);
    std::complex<double> b(4.0, -1.0);
    std::complex<double> product = a * b;
    assert(approx_equal(product.real(), 11.0));   // (2*4 - 3*(-1)) = 8+3 = 11
    assert(approx_equal(product.imag(), 10.0));   // (2*(-1) + 3*4) = -2+12 = 10

    std::cout << "PASS" << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "IGSOA Complex Node Unit Tests" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    try {
        test_default_construction();
        test_informational_density();
        test_phase_calculation();
        test_normalization();
        test_entropy_rate();
        test_config_defaults();
        test_complex_arithmetic();

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
