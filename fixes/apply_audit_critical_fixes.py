#!/usr/bin/env python3
"""
Apply critical fixes identified in audit report verification
Addresses 4 high-priority issues that are simple to fix
"""

import sys

def fix_default_rc(file_path):
    """Fix 1: Change default R_c from 1e-34 to 3.0"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_line = '        , R_c(1e-34)              // Default causal resistance'
    new_line = '        , R_c(3.0)                // Default causal radius (≈3 lattice units)'

    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed default R_c in {file_path}")
        return True
    else:
        print(f"[SKIP] Default R_c already fixed or pattern not found in {file_path}")
        return False

def fix_division_by_zero_1d(file_path):
    """Fix 2: Fix division by zero in 1D engine metrics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_line = '        out_speedup_factor = 15500.0 / ns_per_op_;  // vs baseline'
    new_line = '        out_speedup_factor = (ns_per_op_ > 0.0) ? (15500.0 / ns_per_op_) : 0.0;  // vs baseline'

    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed division by zero in {file_path}")
        return True
    else:
        print(f"[SKIP] Division by zero already fixed or pattern not found in {file_path}")
        return False

def add_3d_normalization(file_path):
    """Fix 3: Add normalization support to 3D timeStep"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already added
    if 'normalize_psi' in content and 'normalizeStates' in content:
        print(f"[SKIP] 3D normalization already added to {file_path}")
        return False

    old_code = '''        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        operations += updateDerivedQuantities(nodes);
        operations += computeGradients(nodes, N_x, N_y, N_z);
        return operations;'''

    new_code = '''        operations += evolveQuantumState(nodes, config.dt, N_x, N_y, N_z);
        operations += evolveCausalField(nodes, config.dt);
        operations += updateDerivedQuantities(nodes);
        operations += computeGradients(nodes, N_x, N_y, N_z);

        // Normalize if requested (matches 1D/2D behavior)
        if (config.normalize_psi) {
            operations += IGSOAPhysics::normalizeStates(nodes);
        }

        return operations;'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Added 3D normalization to {file_path}")
        return True
    else:
        print(f"[WARNING] Could not find insertion point in {file_path}")
        return False

def fix_3d_apply_driving(file_path):
    """Fix 4: Complete 3D applyDriving to match 2D (drive both phi and psi)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_code = '''        for (auto& node : nodes) {
            // Apply real driving signal to causal field
            node.phi += signal_real;
            // Could extend to complex driving if needed (signal_imag reserved for future use)
        }'''

    new_code = '''        for (auto& node : nodes) {
            // Drive causal field (Φ)
            node.phi += signal_real;

            // Drive quantum state (Ψ) - matches 1D/2D behavior
            node.psi += std::complex<double>(signal_real, signal_imag);
        }'''

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[OK] Fixed 3D applyDriving to match 2D in {file_path}")
        return True
    else:
        print(f"[SKIP] 3D applyDriving already fixed or pattern not found in {file_path}")
        return False

def main():
    print("Applying critical fixes from audit report verification...\n")

    success_count = 0
    total_fixes = 4

    # Fix 1: Default R_c
    print("=== Fix 1: Default R_c Value ===")
    if fix_default_rc('src/cpp/igsoa_complex_node.h'):
        success_count += 1

    # Fix 2: Division by zero in 1D
    print("\n=== Fix 2: Division by Zero (1D Engine) ===")
    if fix_division_by_zero_1d('src/cpp/igsoa_complex_engine.h'):
        success_count += 1

    # Fix 3: 3D normalization
    print("\n=== Fix 3: 3D Normalization ===")
    if add_3d_normalization('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    # Fix 4: 3D applyDriving
    print("\n=== Fix 4: 3D applyDriving Completion ===")
    if fix_3d_apply_driving('src/cpp/igsoa_physics_3d.h'):
        success_count += 1

    print(f"\n{success_count}/{total_fixes} critical audit fixes applied")

    if success_count >= 3:
        print("\n[SUCCESS] Critical audit issues addressed!")
        print("\nRemaining issues require more work:")
        print("  - CMake portability (needs FindFFTW3.cmake module)")
        print("  - CFL/stability validation (needs eigenvalue estimation)")
        print("  - CI/testing infrastructure (separate project)")
        print("  - Bridge server security (needs auth/validation)")
        return 0
    else:
        print(f"\n[WARNING] Some fixes may have been skipped or failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
