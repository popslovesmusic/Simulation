#!/usr/bin/env python3
"""
Apply critical fixes to IGSOA 2D engine files
"""

import re
import sys

def fix_center_of_mass_toroidal():
    """Fix center-of-mass calculation to use circular statistics for toroidal topology"""

    file_path = "src/cpp/igsoa_state_init_2d.h"

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find and replace the center of mass computation
    old_code = '''        const auto& nodes = engine.getNodes();

        double sum_F = 0.0;
        double sum_x_F = 0.0;
        double sum_y_F = 0.0;

        for (size_t y = 0; y < N_y; y++) {
            for (size_t x = 0; x < N_x; x++) {
                size_t index = y * N_x + x;
                double F = nodes[index].F;

                sum_F += F;
                sum_x_F += static_cast<double>(x) * F;
                sum_y_F += static_cast<double>(y) * F;
            }
        }

        if (sum_F > 0.0) {
            x_cm_out = sum_x_F / sum_F;
            y_cm_out = sum_y_F / sum_F;
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
        }'''

    new_code = '''        const auto& nodes = engine.getNodes();

        double sum_F = 0.0;
        // Use circular statistics for toroidal topology
        double sum_cos_x = 0.0;
        double sum_sin_x = 0.0;
        double sum_cos_y = 0.0;
        double sum_sin_y = 0.0;

        for (size_t y = 0; y < N_y; y++) {
            for (size_t x = 0; x < N_x; x++) {
                size_t index = y * N_x + x;
                double F = nodes[index].F;

                // Convert coordinates to angles on unit circle
                double theta_x = 2.0 * M_PI * static_cast<double>(x) / static_cast<double>(N_x);
                double theta_y = 2.0 * M_PI * static_cast<double>(y) / static_cast<double>(N_y);

                sum_F += F;
                sum_cos_x += F * std::cos(theta_x);
                sum_sin_x += F * std::sin(theta_x);
                sum_cos_y += F * std::cos(theta_y);
                sum_sin_y += F * std::sin(theta_y);
            }
        }

        if (sum_F > 0.0) {
            // Compute mean angle using atan2
            double mean_theta_x = std::atan2(sum_sin_x, sum_cos_x);
            double mean_theta_y = std::atan2(sum_sin_y, sum_cos_y);

            // Convert back to coordinates (ensure positive result)
            x_cm_out = static_cast<double>(N_x) * mean_theta_x / (2.0 * M_PI);
            if (x_cm_out < 0.0) x_cm_out += static_cast<double>(N_x);

            y_cm_out = static_cast<double>(N_y) * mean_theta_y / (2.0 * M_PI);
            if (y_cm_out < 0.0) y_cm_out += static_cast<double>(N_y);
        } else {
            x_cm_out = 0.0;
            y_cm_out = 0.0;
        }'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed center-of-mass toroidal wrapping in {file_path}")
        return True
    else:
        print(f"[FAIL] Could not find old code pattern in {file_path}")
        return False

def fix_while_loop_wrapping():
    """Optimize coordinate wrapping from while loops to modulo"""

    file_path = "src/cpp/igsoa_physics_2d.h"

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    old_code = '''                        // Periodic boundary conditions (torus wrapping)
                        int x_j = x_i + dx;
                        int y_j = y_i + dy;

                        // Wrap x-coordinate
                        while (x_j < 0) x_j += static_cast<int>(N_x);
                        while (x_j >= static_cast<int>(N_x)) x_j -= static_cast<int>(N_x);

                        // Wrap y-coordinate
                        while (y_j < 0) y_j += static_cast<int>(N_y);
                        while (y_j >= static_cast<int>(N_y)) y_j -= static_cast<int>(N_y);'''

    new_code = '''                        // Periodic boundary conditions (torus wrapping) - optimized modulo
                        int x_temp = (x_i + dx) % static_cast<int>(N_x);
                        int x_j = (x_temp < 0) ? (x_temp + static_cast<int>(N_x)) : x_temp;

                        int y_temp = (y_i + dy) % static_cast<int>(N_y);
                        int y_j = (y_temp < 0) ? (y_temp + static_cast<int>(N_y)) : y_temp;'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Optimized while-loop wrapping in {file_path}")
        return True
    else:
        print(f"[FAIL] Could not find old code pattern in {file_path}")
        return False

def fix_speedup_baseline():
    """Fix hard-coded speedup baseline"""

    file_path = "src/cpp/igsoa_complex_engine_2d.h"

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    old_line = '        out_speedup_factor = 15500.0 / ns_per_op_;  // vs baseline'
    new_line = '        out_speedup_factor = (ns_per_op_ > 0.0) ? (1.0 / ns_per_op_) : 0.0;  // ops/ns (remove 1D baseline)'

    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed speedup baseline in {file_path}")
        return True
    else:
        print(f"[FAIL] Could not find old code pattern in {file_path}")
        return False

if __name__ == "__main__":
    print("Applying critical fixes to IGSOA 2D engine...")
    print()

    success_count = 0
    total_count = 3

    if fix_center_of_mass_toroidal():
        success_count += 1

    if fix_while_loop_wrapping():
        success_count += 1

    if fix_speedup_baseline():
        success_count += 1

    print()
    print(f"{success_count}/{total_count} fixes applied successfully")

    if success_count == total_count:
        print("[SUCCESS] All critical issues fixed!")
        sys.exit(0)
    else:
        print(f"[WARNING] {total_count - success_count} fixes failed - manual intervention may be needed")
        sys.exit(1)
