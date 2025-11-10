#!/usr/bin/env python3
"""
Resolve merge conflicts in 3D engine files by accepting 'theirs' version
"""

import re
import sys

def resolve_conflicts_accept_theirs(file_path):
    """
    Resolve all merge conflicts in a file by accepting the 'theirs' version
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    # Check if there are any conflicts
    if '<<<<<<< ours' not in content:
        print(f"[INFO] No conflicts found in {file_path}")
        return True

    # Count conflicts before
    conflicts_before = content.count('<<<<<<< ours')

    # Pattern to match merge conflict blocks
    # <<<<<<< ours
    # ... (ours content)
    # =======
    # ... (theirs content)
    # >>>>>>> theirs

    # Use regex to remove "ours" sections and keep "theirs"
    pattern = r'<<<<<<< ours\n(.*?)=======\n(.*?)>>>>>>> theirs\n'

    # Replace with just the theirs content
    resolved = re.sub(pattern, r'\2', content, flags=re.DOTALL)

    # Count conflicts after
    conflicts_after = resolved.count('<<<<<<< ours')

    if conflicts_after > 0:
        print(f"[WARNING] {conflicts_after} conflicts remain in {file_path}")
        return False

    # Write resolved content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(resolved)
        print(f"[OK] Resolved {conflicts_before} conflicts in {file_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write {file_path}: {e}")
        return False

def main():
    print("Resolving 3D engine merge conflicts (accepting 'theirs' version)...\n")

    files = [
        'src/cpp/igsoa_physics_3d.h',
        'src/cpp/igsoa_state_init_3d.h',
        'tests/test_igsoa_3d.cpp'
    ]

    success_count = 0
    for file_path in files:
        if resolve_conflicts_accept_theirs(file_path):
            success_count += 1

    print(f"\n{success_count}/{len(files)} files resolved successfully")

    if success_count == len(files):
        print("\n[SUCCESS] All merge conflicts resolved!")
        return 0
    else:
        print(f"\n[WARNING] {len(files) - success_count} files failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
