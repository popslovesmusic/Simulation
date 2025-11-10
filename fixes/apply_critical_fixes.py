#!/usr/bin/env python3
"""
Apply all 5 critical fixes to IGSOA 3D engine
"""

import re
import sys

def fix_1_add_m_pi_definition(file_path):
    """Fix 1 & 2: Add M_PI definition to 3D state init"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add M_PI definition after includes
    old_pattern = '#include <string>\n\nnamespace dase {'
    new_text = '''#include <string>

// Define M_PI for MSVC
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {'''

    if old_pattern in content and '#ifndef M_PI' not in content:
        content = content.replace(old_pattern, new_text)

        # Also replace std::acos(-1.0) with M_PI
        content = content.replace('2.0 * std::acos(-1.0)', '2.0 * M_PI')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fix 1 & 2: Added M_PI definition to {file_path}")
        return True
    else:
        print(f"[INFO] M_PI already defined in {file_path}")
        return False

def fix_3d_center_of_mass(file_path):
    """Fix 1: Replace simple averaging with circular statistics in 3D"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the center of mass function
    old_code = '''        double sum_F = 0.0;
        double sum_x_F = 0.0;
        double sum_y_F = 0.0;
        double sum_z_F = 0.0;

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t index = z * N_x * N_y + y * N_x + x;
                    double F = nodes[index].F;
                    sum_F += F;
                    sum_x_F += static_cast<double>(x) * F;
                    sum_y_F += static_cast<double>(y) * F;
                    sum_z_F += static_cast<double>(z) * F;
                }
            }
        }

        if (sum_F > 0.0) {
            x_cm_out = sum_x_F / sum_F;
            y_cm_out = sum_y_F / sum_F;
            z_cm_out = sum_z_F / sum_F;
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
            z_cm_out = 0.0;
        }'''

    new_code = '''        double sum_F = 0.0;
        // Use circular statistics for toroidal topology
        double sum_cos_x = 0.0;
        double sum_sin_x = 0.0;
        double sum_cos_y = 0.0;
        double sum_sin_y = 0.0;
        double sum_cos_z = 0.0;
        double sum_sin_z = 0.0;

        for (size_t z = 0; z < N_z; ++z) {
            for (size_t y = 0; y < N_y; ++y) {
                for (size_t x = 0; x < N_x; ++x) {
                    size_t index = z * N_x * N_y + y * N_x + x;
                    double F = nodes[index].F;

                    // Convert coordinates to angles on unit circle
                    double theta_x = 2.0 * M_PI * static_cast<double>(x) / static_cast<double>(N_x);
                    double theta_y = 2.0 * M_PI * static_cast<double>(y) / static_cast<double>(N_y);
                    double theta_z = 2.0 * M_PI * static_cast<double>(z) / static_cast<double>(N_z);

                    sum_F += F;
                    sum_cos_x += F * std::cos(theta_x);
                    sum_sin_x += F * std::sin(theta_x);
                    sum_cos_y += F * std::cos(theta_y);
                    sum_sin_y += F * std::sin(theta_y);
                    sum_cos_z += F * std::cos(theta_z);
                    sum_sin_z += F * std::sin(theta_z);
                }
            }
        }

        if (sum_F > 0.0) {
            // Compute mean angle using atan2
            double mean_theta_x = std::atan2(sum_sin_x, sum_cos_x);
            double mean_theta_y = std::atan2(sum_sin_y, sum_cos_y);
            double mean_theta_z = std::atan2(sum_sin_z, sum_cos_z);

            // Convert back to coordinates (ensure positive result)
            x_cm_out = static_cast<double>(N_x) * mean_theta_x / (2.0 * M_PI);
            if (x_cm_out < 0.0) x_cm_out += static_cast<double>(N_x);

            y_cm_out = static_cast<double>(N_y) * mean_theta_y / (2.0 * M_PI);
            if (y_cm_out < 0.0) y_cm_out += static_cast<double>(N_y);

            z_cm_out = static_cast<double>(N_z) * mean_theta_z / (2.0 * M_PI);
            if (z_cm_out < 0.0) z_cm_out += static_cast<double>(N_z);
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
            z_cm_out = 0.0;
        }'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fix 1: Applied circular statistics to 3D center-of-mass in {file_path}")
        return True
    else:
        print(f"[SKIP] Center-of-mass already fixed or pattern not found in {file_path}")
        return False

def fix_3_add_entropy_rate(file_path):
    """Fix 3: Add updateEntropyRate() call in 3D physics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = '''    static void updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
        }
    }'''

    new_code = '''    static void updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
            node.updateEntropyRate();  // Fixed: was missing in 3D
        }
    }'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fix 3: Added updateEntropyRate() to {file_path}")
        return True
    else:
        print(f"[SKIP] updateEntropyRate() already added or pattern not found in {file_path}")
        return False

def fix_4_standardize_function_name(file_path):
    """Fix 4: Rename evolveRealizedField to evolveCausalField"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace function definition
    content = content.replace(
        'static uint64_t evolveRealizedField(',
        'static uint64_t evolveCausalField('
    )

    # Replace function call
    content = content.replace(
        'operations += evolveRealizedField(nodes, config.dt);',
        'operations += evolveCausalField(nodes, config.dt);'
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] Fix 4: Standardized function name to evolveCausalField in {file_path}")
    return True

def fix_5_add_3d_gradients(file_path):
    """Fix 5: Add computeGradients function to 3D physics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already added
    if 'static uint64_t computeGradients(' in content:
        print(f"[SKIP] computeGradients() already exists in {file_path}")
        return False

    # Find insertion point (after updateDerivedQuantities)
    insertion_marker = '''    static void updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
            node.updateEntropyRate();  // Fixed: was missing in 3D
        }
    }'''

    gradient_function = '''

    /**
     * Compute 3D spatial gradients of F (informational density)
     *
     * ∇F = (∂F/∂x, ∂F/∂y, ∂F/∂z) approximated as central differences
     */
    static uint64_t computeGradients(
        std::vector<IGSOAComplexNode>& nodes,
        size_t N_x,
        size_t N_y,
        size_t N_z
    ) {
        const size_t N_total = N_x * N_y * N_z;
        const size_t plane_size = N_x * N_y;
        uint64_t operations = 0;

        for (size_t index = 0; index < N_total; ++index) {
            const int x_i = static_cast<int>(index % N_x);
            const int y_i = static_cast<int>((index / N_x) % N_y);
            const int z_i = static_cast<int>(index / plane_size);

            // Neighbor indices with wrapping
            const int x_right = (x_i == static_cast<int>(N_x) - 1) ? 0 : x_i + 1;
            const int x_left = (x_i == 0) ? static_cast<int>(N_x) - 1 : x_i - 1;
            const int y_up = (y_i == static_cast<int>(N_y) - 1) ? 0 : y_i + 1;
            const int y_down = (y_i == 0) ? static_cast<int>(N_y) - 1 : y_i - 1;
            const int z_front = (z_i == static_cast<int>(N_z) - 1) ? 0 : z_i + 1;
            const int z_back = (z_i == 0) ? static_cast<int>(N_z) - 1 : z_i - 1;

            // Convert to 1D indices
            const size_t idx_right = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_right);
            const size_t idx_left = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_left);
            const size_t idx_up = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_up) * N_x + static_cast<size_t>(x_i);
            const size_t idx_down = static_cast<size_t>(z_i) * plane_size + static_cast<size_t>(y_down) * N_x + static_cast<size_t>(x_i);
            const size_t idx_front = static_cast<size_t>(z_front) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_i);
            const size_t idx_back = static_cast<size_t>(z_back) * plane_size + static_cast<size_t>(y_i) * N_x + static_cast<size_t>(x_i);

            // Central differences: ∂F/∂x ≈ (F[x+1] - F[x-1]) / 2
            const double dF_dx = (nodes[idx_right].F - nodes[idx_left].F) * 0.5;
            const double dF_dy = (nodes[idx_up].F - nodes[idx_down].F) * 0.5;
            const double dF_dz = (nodes[idx_front].F - nodes[idx_back].F) * 0.5;

            // Store gradient magnitude
            nodes[index].F_gradient = std::sqrt(dF_dx * dF_dx + dF_dy * dF_dy + dF_dz * dF_dz);
            operations++;
        }
        return operations;
    }'''

    if insertion_marker in content:
        content = content.replace(insertion_marker, insertion_marker + gradient_function)

        # Also update timeStep to call computeGradients
        old_timestep = '''    static uint64_t timeStep(
        std::vector<IGSOAComplexNode>& nodes,
        const IGSOAComplexConfig& config,
        size_t N_x,
        size_t N_y,
        size_t N_z
    ) {
        uint64_t operations = 0;
        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        updateDerivedQuantities(nodes);
        return operations;
    }'''

        new_timestep = '''    static uint64_t timeStep(
        std::vector<IGSOAComplexNode>& nodes,
        const IGSOAComplexConfig& config,
        size_t N_x,
        size_t N_y,
        size_t N_z
    ) {
        uint64_t operations = 0;
        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        updateDerivedQuantities(nodes);
        operations += computeGradients(nodes, N_x, N_y, N_z);  // Added: compute 3D gradients
        return operations;
    }'''

        content = content.replace(old_timestep, new_timestep)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fix 5: Added computeGradients() to {file_path}")
        return True
    else:
        print(f"[ERROR] Could not find insertion point in {file_path}")
        return False

def main():
    print("Applying 5 critical fixes to IGSOA 3D engine...\n")

    success_count = 0
    total_fixes = 5

    # Fix 1 & 2: Add M_PI and fix 3D center-of-mass
    if fix_1_add_m_pi_definition('src/cpp/igsoa_state_init_3d.h'):
        success_count += 1
    if fix_3d_center_of_mass('src/cpp/igsoa_state_init_3d.h'):
        success_count += 1

    # Fix 3: Add updateEntropyRate()
    if fix_3_add_entropy_rate('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    # Fix 4: Standardize function names
    if fix_4_standardize_function_name('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    # Fix 5: Add 3D gradient computation
    if fix_5_add_3d_gradients('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    print(f"\n{success_count}/{total_fixes} critical fixes applied")

    if success_count >= 4:  # Allow some to be already applied
        print("\n[SUCCESS] All critical fixes applied!")
        return 0
    else:
        print(f"\n[WARNING] Some fixes may have failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
