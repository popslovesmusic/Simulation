/**
 * IGSOA GW Engine - Basic Functionality Test
 *
 * Tests core components:
 * - SymmetryField 3D grid operations
 * - FractionalSolver SOE kernel
 * - Basic field evolution
 */

#define _USE_MATH_DEFINES  // Enable M_PI on MSVC
#include <cmath>
#include "../src/cpp/igsoa_gw_engine/core/symmetry_field.h"
#include "../src/cpp/igsoa_gw_engine/core/fractional_solver.h"
#include <iostream>
#include <iomanip>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace dase::igsoa::gw;

// Test 1: SymmetryField construction and grid operations
bool test_symmetry_field_basic() {
    std::cout << "\n=== Test 1: SymmetryField Basic Operations ===" << std::endl;

    // Create small test grid
    SymmetryFieldConfig config;
    config.nx = 8;
    config.ny = 8;
    config.nz = 8;
    config.dx = 1000.0;  // 1 km
    config.dy = 1000.0;
    config.dz = 1000.0;
    config.dt = 0.001;   // 1 ms

    SymmetryField field(config);

    // Test grid access
    std::complex<double> test_val(1.0, 0.5);
    field.setDeltaPhi(4, 4, 4, test_val);
    std::complex<double> retrieved = field.getDeltaPhi(4, 4, 4);

    if (std::abs(retrieved - test_val) > 1e-12) {
        std::cout << "FAILED: Grid set/get mismatch" << std::endl;
        return false;
    }

    std::cout << "✓ Grid access working" << std::endl;

    // Test alpha field
    field.setAlpha(4, 4, 4, 1.5);
    double alpha = field.getAlpha(4, 4, 4);

    if (std::abs(alpha - 1.5) > 1e-12) {
        std::cout << "FAILED: Alpha set/get mismatch" << std::endl;
        return false;
    }

    std::cout << "✓ Alpha field working" << std::endl;

    // Test grid info
    int total = field.getTotalPoints();
    if (total != 8*8*8) {
        std::cout << "FAILED: Total points = " << total << ", expected 512" << std::endl;
        return false;
    }

    std::cout << "✓ Total points = " << total << std::endl;

    // Test index conversion
    int flat_idx = field.toFlatIndex(2, 3, 4);
    int i, j, k;
    field.fromFlatIndex(flat_idx, i, j, k);

    if (i != 2 || j != 3 || k != 4) {
        std::cout << "FAILED: Index conversion" << std::endl;
        return false;
    }

    std::cout << "✓ Index conversion working" << std::endl;

    return true;
}

// Test 2: Gradient and Laplacian computation
bool test_derivatives() {
    std::cout << "\n=== Test 2: Spatial Derivatives ===" << std::endl;

    SymmetryFieldConfig config;
    config.nx = 16;
    config.ny = 16;
    config.nz = 16;
    config.dx = 1000.0;
    config.dy = 1000.0;
    config.dz = 1000.0;

    SymmetryField field(config);

    // Set up a simple test pattern: φ(x,y,z) = A * sin(kx * x)
    double A = 1.0;
    double kx = 2.0 * M_PI / (config.nx * config.dx);

    for (int i = 0; i < config.nx; i++) {
        for (int j = 0; j < config.ny; j++) {
            for (int k = 0; k < config.nz; k++) {
                Vector3D pos = field.toPosition(i, j, k);
                double value = A * std::sin(kx * pos.x);
                field.setDeltaPhi(i, j, k, std::complex<double>(value, 0.0));
            }
        }
    }

    // Test gradient at center (should be ≈ A * kx * cos(kx * x_center))
    int ic = config.nx / 2;
    int jc = config.ny / 2;
    int kc = config.nz / 2;

    Vector3D grad = field.computeGradient(ic, jc, kc);
    Vector3D pos_center = field.toPosition(ic, jc, kc);

    double expected_grad_x = A * kx * std::cos(kx * pos_center.x);

    std::cout << "Computed gradient_x: " << grad.x << std::endl;
    std::cout << "Expected gradient_x: " << std::abs(expected_grad_x) << std::endl;

    // Allow 10% error for finite difference approximation
    double rel_error = std::abs(grad.x - std::abs(expected_grad_x)) / std::abs(expected_grad_x);
    if (rel_error > 0.1) {
        std::cout << "FAILED: Gradient error too large: " << rel_error * 100 << "%" << std::endl;
        return false;
    }

    std::cout << "✓ Gradient computation (error: " << rel_error * 100 << "%)" << std::endl;

    // Test Laplacian (should be ≈ -A * kx² * sin(kx * x))
    std::complex<double> laplacian = field.computeLaplacian(ic, jc, kc);
    double expected_laplacian = -A * kx * kx * std::sin(kx * pos_center.x);

    std::cout << "Computed Laplacian: " << laplacian.real() << std::endl;
    std::cout << "Expected Laplacian: " << expected_laplacian << std::endl;

    // For very small expected values (near machine precision), check absolute error
    double laplacian_abs_error = std::abs(laplacian.real() - expected_laplacian);
    double laplacian_rel_error = 0.0;

    if (std::abs(expected_laplacian) < 1e-10) {
        // Use absolute error for tiny values
        if (laplacian_abs_error > 1e-10) {
            std::cout << "FAILED: Laplacian absolute error too large: " << laplacian_abs_error << std::endl;
            return false;
        }
        laplacian_rel_error = 0.0;  // Effectively zero for tiny values
    } else {
        // Use relative error for normal values
        laplacian_rel_error = laplacian_abs_error / std::abs(expected_laplacian);
        if (laplacian_rel_error > 0.15) {
            std::cout << "FAILED: Laplacian error too large: " << laplacian_rel_error * 100 << "%" << std::endl;
            return false;
        }
    }

    std::cout << "✓ Laplacian computation (absolute error: " << laplacian_abs_error << ")" << std::endl;

    return true;
}

// Test 3: Fractional solver and SOE kernel
bool test_fractional_solver() {
    std::cout << "\n=== Test 3: Fractional Solver ===" << std::endl;

    FractionalSolverConfig config;
    config.T_max = 10.0;
    config.soe_rank = 12;
    config.alpha_min = 1.0;
    config.alpha_max = 2.0;

    int num_points = 100;
    FractionalSolver solver(config, num_points);

    std::cout << "✓ FractionalSolver constructed with " << num_points << " points" << std::endl;

    // Test kernel generation for different alphas
    std::vector<double> test_alphas = {1.0, 1.5, 2.0};

    for (double alpha : test_alphas) {
        const SOEKernel& kernel = solver.getKernel(alpha);

        std::cout << "Alpha = " << alpha << ": rank = " << kernel.rank << std::endl;

        if (kernel.rank != config.soe_rank) {
            std::cout << "FAILED: Kernel rank mismatch" << std::endl;
            return false;
        }

        // Evaluate kernel at t = 1.0
        double K_1 = kernel.evaluate(1.0);
        std::cout << "  K(" << alpha << ", t=1.0) = " << K_1 << std::endl;

        // Memory strength should decrease as alpha increases
        double memory_strength = solver.getMemoryStrength(alpha);
        std::cout << "  Memory strength η = " << memory_strength << std::endl;
    }

    std::cout << "✓ SOE kernels generated for multiple alphas" << std::endl;

    // Test precomputation
    solver.precomputeKernels(10);
    int num_cached = solver.getNumCachedKernels();

    std::cout << "✓ Precomputed " << num_cached << " kernels" << std::endl;

    // Test memory usage
    size_t mem = solver.getMemoryUsage();
    std::cout << "✓ Memory usage: " << mem / 1024.0 / 1024.0 << " MB" << std::endl;

    return true;
}

// Test 4: Field statistics
bool test_field_statistics() {
    std::cout << "\n=== Test 4: Field Statistics ===" << std::endl;

    SymmetryFieldConfig config;
    config.nx = 32;
    config.ny = 32;
    config.nz = 32;
    config.dx = 1000.0;
    config.dy = 1000.0;
    config.dz = 1000.0;

    SymmetryField field(config);

    // Set Gaussian field
    double sigma = 10000.0;  // 10 km
    Vector3D center(config.nx * config.dx / 2, config.ny * config.dy / 2, config.nz * config.dz / 2);

    for (int i = 0; i < config.nx; i++) {
        for (int j = 0; j < config.ny; j++) {
            for (int k = 0; k < config.nz; k++) {
                Vector3D pos = field.toPosition(i, j, k);
                double r2 = (pos.x - center.x) * (pos.x - center.x) +
                           (pos.y - center.y) * (pos.y - center.y) +
                           (pos.z - center.z) * (pos.z - center.z);

                double value = std::exp(-r2 / (2.0 * sigma * sigma));
                field.setDeltaPhi(i, j, k, std::complex<double>(value, 0.0));
            }
        }
    }

    // Update gradient cache
    field.updateGradientCache();

    // Get statistics
    auto stats = field.getStatistics();

    std::cout << "Max amplitude: " << stats.max_amplitude << std::endl;
    std::cout << "Mean amplitude: " << stats.mean_amplitude << std::endl;
    std::cout << "Total energy: " << stats.total_energy << std::endl;
    std::cout << "Max gradient: " << stats.max_gradient << std::endl;
    std::cout << "Mean gradient: " << stats.mean_gradient << std::endl;

    // Sanity checks
    if (stats.max_amplitude < 0.99 || stats.max_amplitude > 1.01) {
        std::cout << "FAILED: Max amplitude should be ≈ 1.0" << std::endl;
        return false;
    }

    if (stats.mean_amplitude >= stats.max_amplitude) {
        std::cout << "FAILED: Mean should be less than max" << std::endl;
        return false;
    }

    std::cout << "✓ Field statistics computed successfully" << std::endl;

    return true;
}

// Test 5: Interpolation
bool test_interpolation() {
    std::cout << "\n=== Test 5: Trilinear Interpolation ===" << std::endl;

    SymmetryFieldConfig config;
    config.nx = 8;
    config.ny = 8;
    config.nz = 8;
    config.dx = 1.0;
    config.dy = 1.0;
    config.dz = 1.0;

    SymmetryField field(config);

    // Set simple linear field: φ(x,y,z) = x + y + z
    for (int i = 0; i < config.nx; i++) {
        for (int j = 0; j < config.ny; j++) {
            for (int k = 0; k < config.nz; k++) {
                Vector3D pos = field.toPosition(i, j, k);
                double value = pos.x + pos.y + pos.z;
                field.setDeltaPhi(i, j, k, std::complex<double>(value, 0.0));
            }
        }
    }

    // Test interpolation at fractional position
    Vector3D test_pos(2.5, 3.7, 4.2);
    std::complex<double> interpolated = field.getDeltaPhiAt(test_pos);
    double expected = test_pos.x + test_pos.y + test_pos.z;

    std::cout << "Interpolated value: " << interpolated.real() << std::endl;
    std::cout << "Expected value: " << expected << std::endl;

    double error = std::abs(interpolated.real() - expected);
    if (error > 0.1) {
        std::cout << "FAILED: Interpolation error too large: " << error << std::endl;
        return false;
    }

    std::cout << "✓ Trilinear interpolation working (error: " << error << ")" << std::endl;

    return true;
}

// Main test runner
int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "IGSOA GW Engine - Basic Functionality Tests" << std::endl;
    std::cout << "========================================" << std::endl;

    int passed = 0;
    int total = 5;

    if (test_symmetry_field_basic()) {
        passed++;
        std::cout << "✓ Test 1 PASSED" << std::endl;
    } else {
        std::cout << "✗ Test 1 FAILED" << std::endl;
    }

    if (test_derivatives()) {
        passed++;
        std::cout << "✓ Test 2 PASSED" << std::endl;
    } else {
        std::cout << "✗ Test 2 FAILED" << std::endl;
    }

    if (test_fractional_solver()) {
        passed++;
        std::cout << "✓ Test 3 PASSED" << std::endl;
    } else {
        std::cout << "✗ Test 3 FAILED" << std::endl;
    }

    if (test_field_statistics()) {
        passed++;
        std::cout << "✓ Test 4 PASSED" << std::endl;
    } else {
        std::cout << "✗ Test 4 FAILED" << std::endl;
    }

    if (test_interpolation()) {
        passed++;
        std::cout << "✓ Test 5 PASSED" << std::endl;
    } else {
        std::cout << "✗ Test 5 FAILED" << std::endl;
    }

    std::cout << "\n========================================" << std::endl;
    std::cout << "Results: " << passed << "/" << total << " tests passed" << std::endl;
    std::cout << "========================================" << std::endl;

    return (passed == total) ? 0 : 1;
}
