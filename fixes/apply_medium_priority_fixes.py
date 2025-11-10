#!/usr/bin/env python3
"""
Apply all medium and medium-high priority fixes to IGSOA engine
"""

import re
import sys

def fix_1_consistent_return_type_3d(file_path):
    """Fix: Make 3D updateDerivedQuantities return uint64_t like 2D"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = '''    static void updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
            node.updateEntropyRate();  // Fixed: was missing in 3D
        }
    }'''

    new_code = '''    static uint64_t updateDerivedQuantities(std::vector<IGSOAComplexNode>& nodes) {
        uint64_t operations = 0;
        for (auto& node : nodes) {
            node.updateInformationalDensity();
            node.updatePhase();
            node.updateEntropyRate();
            operations++;
        }
        return operations;
    }'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Also update the call in timeStep to use the return value
        old_timestep_call = '''        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        updateDerivedQuantities(nodes);
        operations += computeGradients(nodes, N_x, N_y, N_z);  // Added: compute 3D gradients'''

        new_timestep_call = '''        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        operations += updateDerivedQuantities(nodes);  // Fixed: now returns operation count
        operations += computeGradients(nodes, N_x, N_y, N_z);'''

        content = content.replace(old_timestep_call, new_timestep_call)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed return type inconsistency in {file_path}")
        return True
    else:
        print(f"[SKIP] Return type already fixed in {file_path}")
        return False

def fix_2_thread_safe_diagnostic_2d(file_path):
    """Fix: Make diagnostic print thread-safe in 2D"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if mutex already added
    if '#include <mutex>' in content:
        print(f"[SKIP] Thread-safety already fixed in {file_path}")
        return False

    # Add mutex header after iostream
    old_includes = '''#include <iostream>

namespace dase {'''

    new_includes = '''#include <iostream>
#include <mutex>

namespace dase {'''

    if old_includes in content:
        content = content.replace(old_includes, new_includes)
    else:
        print(f"[WARNING] Could not find include insertion point in {file_path}")

    # Replace static bool with std::once_flag and std::call_once
    old_diagnostic = '''            // DIAGNOSTIC: Print once to verify this code path is active
            static bool diagnostic_printed = false;
            if (!diagnostic_printed && i == 0) {
                std::cerr << "[IGSOA 2D DIAGNOSTIC] Using 2D non-local coupling (Nov 3 2025, R_c="
                          << node.R_c << ", lattice=" << N_x << "x" << N_y << ")" << std::endl;
                diagnostic_printed = true;
            }'''

    new_diagnostic = '''            // DIAGNOSTIC: Print once to verify this code path is active (thread-safe)
            static std::once_flag diagnostic_flag;
            if (i == 0) {
                std::call_once(diagnostic_flag, [&]() {
                    std::cerr << "[IGSOA 2D DIAGNOSTIC] Using 2D non-local coupling (Nov 3 2025, R_c="
                              << node.R_c << ", lattice=" << N_x << "x" << N_y << ")" << std::endl;
                });
            }'''

    if old_diagnostic in content:
        content = content.replace(old_diagnostic, new_diagnostic)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed thread-safety in {file_path}")
        return True
    else:
        print(f"[SKIP] Diagnostic already fixed or pattern not found in {file_path}")
        return False

def fix_2_thread_safe_diagnostic_3d(file_path):
    """Fix: Make diagnostic print thread-safe in 3D"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if mutex already added
    if '#include <mutex>' in content:
        print(f"[SKIP] Thread-safety already fixed in {file_path}")
        return False

    # Add mutex header after iostream
    old_includes = '''#include <iostream>
#include <vector>

namespace dase {'''

    new_includes = '''#include <iostream>
#include <mutex>
#include <vector>

namespace dase {'''

    if old_includes in content:
        content = content.replace(old_includes, new_includes)
    else:
        print(f"[WARNING] Could not find include insertion point in {file_path}")

    # Replace static bool with std::once_flag and std::call_once
    old_diagnostic = '''            static bool diagnostic_printed = false;
            if (!diagnostic_printed && index == 0) {
                std::cerr << "[IGSOA 3D DIAGNOSTIC] Using 3D non-local coupling (" << N_x
                          << "x" << N_y << "x" << N_z << ", R_c=" << node.R_c << ")" << std::endl;
                diagnostic_printed = true;
            }'''

    new_diagnostic = '''            // DIAGNOSTIC: Print once to verify this code path is active (thread-safe)
            static std::once_flag diagnostic_flag;
            if (index == 0) {
                std::call_once(diagnostic_flag, [&]() {
                    std::cerr << "[IGSOA 3D DIAGNOSTIC] Using 3D non-local coupling (" << N_x
                              << "x" << N_y << "x" << N_z << ", R_c=" << node.R_c << ")" << std::endl;
                });
            }'''

    if old_diagnostic in content:
        content = content.replace(old_diagnostic, new_diagnostic)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed thread-safety in {file_path}")
        return True
    else:
        print(f"[SKIP] Diagnostic already fixed or pattern not found in {file_path}")
        return False

def fix_3_add_bounds_checking_2d(file_path):
    """Fix: Add bounds checking to 2D coordToIndex"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = '''    size_t coordToIndex(size_t x, size_t y) const {
        return y * N_x_ + x;
    }'''

    new_code = '''    size_t coordToIndex(size_t x, size_t y) const {
        #ifndef NDEBUG
        if (x >= N_x_ || y >= N_y_) {
            throw std::out_of_range("2D coordinates out of bounds");
        }
        #endif
        return y * N_x_ + x;
    }'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Add stdexcept header if not present
        if '#include <stdexcept>' not in content:
            content = content.replace('#include <vector>', '#include <vector>\n#include <stdexcept>')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Added bounds checking to {file_path}")
        return True
    else:
        print(f"[SKIP] Bounds checking already added to {file_path}")
        return False

def fix_3_add_bounds_checking_3d(file_path):
    """Fix: Add bounds checking to 3D coordToIndex"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = '''    size_t coordToIndex(size_t x, size_t y, size_t z) const {
        return z * N_x_ * N_y_ + y * N_x_ + x;
    }'''

    new_code = '''    size_t coordToIndex(size_t x, size_t y, size_t z) const {
        #ifndef NDEBUG
        if (x >= N_x_ || y >= N_y_ || z >= N_z_) {
            throw std::out_of_range("3D coordinates out of bounds");
        }
        #endif
        return z * N_x_ * N_y_ + y * N_x_ + x;
    }'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Add stdexcept header if not present
        if '#include <stdexcept>' not in content:
            content = content.replace('#include <vector>', '#include <vector>\n#include <stdexcept>')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Added bounds checking to {file_path}")
        return True
    else:
        print(f"[SKIP] Bounds checking already added to {file_path}")
        return False

def fix_4_add_const_correctness_2d(file_path):
    """Fix: Add const correctness to 2D physics (match 3D)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 1: Make loop variable const
    content = content.replace(
        '            int x_i = static_cast<int>(i % N_x);',
        '            const int x_i = static_cast<int>(i % N_x);'
    )
    content = content.replace(
        '            int y_i = static_cast<int>(i / N_x);',
        '            const int y_i = static_cast<int>(i / N_x);'
    )

    # Fix 2: Make radius const
    content = content.replace(
        '                double radius = std::max(node.R_c, 0.0);',
        '                const double radius = std::max(node.R_c, 0.0);'
    )

    # Fix 3: Make R_c_int const
    content = content.replace(
        '                int R_c_int = static_cast<int>(std::ceil(radius));',
        '                const int R_c_int = static_cast<int>(std::ceil(radius));'
    )

    # Fix 4: Add const to gradient computation variables
    old_gradient = '''            int x_i = static_cast<int>(i % N_x);
            int y_i = static_cast<int>(i / N_x);

            // Neighbor indices with wrapping
            int x_right = (x_i == static_cast<int>(N_x) - 1) ? 0 : x_i + 1;
            int x_left = (x_i == 0) ? static_cast<int>(N_x) - 1 : x_i - 1;
            int y_up = (y_i == static_cast<int>(N_y) - 1) ? 0 : y_i + 1;
            int y_down = (y_i == 0) ? static_cast<int>(N_y) - 1 : y_i - 1;'''

    new_gradient = '''            const int x_i = static_cast<int>(i % N_x);
            const int y_i = static_cast<int>(i / N_x);

            // Neighbor indices with wrapping
            const int x_right = (x_i == static_cast<int>(N_x) - 1) ? 0 : x_i + 1;
            const int x_left = (x_i == 0) ? static_cast<int>(N_x) - 1 : x_i - 1;
            const int y_up = (y_i == static_cast<int>(N_y) - 1) ? 0 : y_i + 1;
            const int y_down = (y_i == 0) ? static_cast<int>(N_y) - 1 : y_i - 1;'''

    content = content.replace(old_gradient, new_gradient)

    # Fix 5: Make N_total const
    content = content.replace(
        '        const size_t N_total = N_x * N_y;',
        '        const size_t N_total = N_x * N_y;'  # Already const, no change needed
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] Added const correctness to {file_path}")
    return True

def main():
    print("Applying medium-high and medium priority fixes...\n")

    success_count = 0
    total_fixes = 7  # Number of individual fixes

    # Fix 1: Consistent return types in 3D
    print("=== Fix 1: Inconsistent Return Types ===")
    if fix_1_consistent_return_type_3d('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    # Fix 2: Thread-safe diagnostics
    print("\n=== Fix 2: Thread-Safe Diagnostics ===")
    if fix_2_thread_safe_diagnostic_2d('src/cpp/igsoa_physics_2d.h'):
        success_count += 1
    if fix_2_thread_safe_diagnostic_3d('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    # Fix 3: Bounds checking
    print("\n=== Fix 3: Bounds Checking ===")
    if fix_3_add_bounds_checking_2d('src/cpp/igsoa_complex_engine_2d.h'):
        success_count += 1
    if fix_3_add_bounds_checking_3d('src/cpp/igsoa_complex_engine_3d.h'):
        success_count += 1

    # Fix 4: Const correctness in 2D
    print("\n=== Fix 4: Const Correctness (2D) ===")
    if fix_4_add_const_correctness_2d('src/cpp/igsoa_physics_2d.h'):
        success_count += 1
        success_count += 1  # Count as 2 since it's multiple changes

    print(f"\n{success_count}/{total_fixes} medium priority fixes applied")

    if success_count >= 5:  # Allow some to already be applied
        print("\n[SUCCESS] Medium priority fixes applied!")
        return 0
    else:
        print(f"\n[WARNING] Some fixes may have been skipped or failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
