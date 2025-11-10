#!/usr/bin/env python3
"""
IGSOA-SIM Production Release Preparation Script

Safely cleans the codebase by removing test files, build artifacts, and
temporary files before production release. Supports dry-run mode and creates
backups before any deletions.

Usage:
  python prepare_release.py --dry-run              # Preview what would be removed
  python prepare_release.py --clean                # Remove files (creates backup)
  python prepare_release.py --split-licensing      # Separate GNU vs Commercial code
  python prepare_release.py --manifest             # Generate file manifest only
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Backup directory
BACKUP_DIR = PROJECT_ROOT / "backups" / f"pre_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ============================================================================
# File Patterns to Clean
# ============================================================================

CLEANUP_PATTERNS = {
    "test_missions": {
        "description": "Test mission files (not production examples)",
        "patterns": [
            "missions/test_*.json",
            "missions/mission_rc_*.json",  # Auto-generated test sweeps
            "missions/debug_*.json",
            "missions/tmp_*.json",
        ],
        "exclude": [
            "missions/examples/",  # Keep example missions
        ]
    },

    "test_outputs": {
        "description": "Test simulation outputs",
        "patterns": [
            "missions/*_output.json",
            "missions/rc_sweep/*_output.json",
            "results/test_*.json",
            "results/tmp_*.json",
        ]
    },

    "build_artifacts": {
        "description": "Build system artifacts (can be regenerated)",
        "patterns": [
            "build/**/*.obj",
            "build/**/*.o",
            "build/**/*.pdb",
            "build/**/*.ilk",
            "build/**/*.exp",
            "build/**/*.iobj",
            "build/**/*.ipdb",
            "**/*.pyc",
            "**/__pycache__/",
            "**/.pytest_cache/",
            "**/.mypy_cache/",
            "**/.ruff_cache/",
        ],
        "exclude": [
            "build/scripts/",  # Keep build scripts
            "build/analysis_reports/",  # Keep recent analysis reports
        ]
    },

    "temp_files": {
        "description": "Temporary and backup files",
        "patterns": [
            "**/*.tmp",
            "**/*.bak",
            "**/*~",
            "**/*.swp",
            "**/*.swo",
            "**/Thumbs.db",
            "**/.DS_Store",
        ]
    },

    "test_executables": {
        "description": "Test executables (keep main dase_cli.exe)",
        "patterns": [
            "dase_cli/test_*.exe",
            "dase_cli/debug_*.exe",
            "build/test_*.exe",
        ],
        "exclude": [
            "dase_cli/dase_cli.exe",  # KEEP main CLI
        ]
    },

    "log_files": {
        "description": "Development log files",
        "patterns": [
            "**/*.log",
            "**/logs/*.txt",
        ],
        "exclude": [
            "docs/**/*.log",  # Keep example logs in docs
        ]
    },

    "analysis_reports": {
        "description": "Old static analysis reports (keep last 3)",
        "patterns": [
            "build/analysis_reports/**/*.txt",
            "build/analysis_reports/**/*.xml",
            "build/analysis_reports/**/*.json",
        ],
        "keep_newest": 3  # Keep 3 most recent reports
    },

    "git_artifacts": {
        "description": "Git-related files (not needed in distribution)",
        "patterns": [
            ".git/",
            ".gitignore",
            ".gitattributes",
        ],
        "warning": "Only remove for final distribution package, not in source repo!"
    }
}

# GNU-licensed components (stay in main distribution)
GNU_COMPONENTS = [
    "tools/",
    "analysis/",
    "docs/",
    "build/scripts/",
    "benchmarks/",
    "missions/examples/",
]

# Commercial-licensed components (require commercial license)
COMMERCIAL_COMPONENTS = [
    "dase_cli/dase_cli.exe",
    "src/cpp/",  # Engine source code
    "include/",  # Header files
    "external/fftw/",  # FFTW binaries
]


# ============================================================================
# Helper Functions
# ============================================================================

def find_files(patterns: List[str], exclude: List[str] = None) -> List[Path]:
    """Find files matching glob patterns, excluding certain paths"""
    exclude = exclude or []
    files = set()

    for pattern in patterns:
        pattern_path = PROJECT_ROOT / pattern

        # Handle directory patterns
        if pattern.endswith('/'):
            for match in PROJECT_ROOT.glob(pattern):
                if match.is_dir():
                    files.add(match)
        else:
            # Handle file patterns
            if '**' in pattern:
                # Recursive glob
                parts = pattern.split('**/')
                if len(parts) == 2:
                    base = parts[0] if parts[0] else '.'
                    file_pattern = parts[1]
                    for match in (PROJECT_ROOT / base).rglob(file_pattern):
                        files.add(match)
            else:
                # Non-recursive glob
                for match in PROJECT_ROOT.glob(pattern):
                    files.add(match)

    # Apply exclusions
    filtered = []
    for f in files:
        excluded = False
        for exc in exclude:
            exc_path = PROJECT_ROOT / exc
            try:
                f.relative_to(exc_path)
                excluded = True
                break
            except ValueError:
                pass

        if not excluded:
            filtered.append(f)

    return sorted(filtered)


def keep_newest(files: List[Path], n: int) -> Tuple[List[Path], List[Path]]:
    """Split files into newest N and rest, sorted by modification time"""
    if len(files) <= n:
        return files, []

    sorted_files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
    return sorted_files[:n], sorted_files[n:]


def format_size(size_bytes: int) -> str:
    """Format byte size as human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_size(path: Path) -> int:
    """Get total size of file or directory"""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return 0


# ============================================================================
# Main Operations
# ============================================================================

def analyze_cleanup(dry_run=True) -> Dict:
    """Analyze what would be cleaned up"""
    results = {
        "categories": {},
        "total_files": 0,
        "total_size": 0,
        "timestamp": datetime.now().isoformat()
    }

    print("\n" + "=" * 70)
    print("  IGSOA-SIM Production Cleanup Analysis")
    print("=" * 70 + "\n")

    for category, config in CLEANUP_PATTERNS.items():
        print(f"\n[{category.upper()}]")
        print(f"Description: {config['description']}")

        if 'warning' in config:
            print(f"WARNING: {config['warning']}")

        patterns = config.get('patterns', [])
        exclude = config.get('exclude', [])
        keep_n = config.get('keep_newest', 0)

        files = find_files(patterns, exclude)

        if keep_n > 0:
            keep, remove = keep_newest(files, keep_n)
            files = remove
            print(f"Keeping {len(keep)} newest files, removing {len(remove)} older files")

        if not files:
            print("  No files found.")
            continue

        total_size = sum(get_file_size(f) for f in files)

        results["categories"][category] = {
            "description": config["description"],
            "files": [str(f.relative_to(PROJECT_ROOT)) for f in files],
            "count": len(files),
            "total_size": total_size
        }

        results["total_files"] += len(files)
        results["total_size"] += total_size

        print(f"  Files to remove: {len(files)}")
        print(f"  Total size: {format_size(total_size)}")

        if len(files) <= 10:
            for f in files:
                rel_path = f.relative_to(PROJECT_ROOT)
                size = get_file_size(f)
                print(f"    - {rel_path} ({format_size(size)})")
        else:
            for f in files[:5]:
                rel_path = f.relative_to(PROJECT_ROOT)
                size = get_file_size(f)
                print(f"    - {rel_path} ({format_size(size)})")
            print(f"    ... and {len(files) - 5} more files")

    print("\n" + "=" * 70)
    print(f"TOTAL: {results['total_files']} files, {format_size(results['total_size'])}")
    print("=" * 70 + "\n")

    return results


def execute_cleanup(backup=True):
    """Execute cleanup with optional backup"""
    print("\n" + "=" * 70)
    print("  EXECUTING CLEANUP")
    print("=" * 70 + "\n")

    if backup:
        print(f"Creating backup at: {BACKUP_DIR}")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    removed_count = 0
    removed_size = 0

    for category, config in CLEANUP_PATTERNS.items():
        if 'warning' in config:
            print(f"\nSkipping {category} (requires manual confirmation)")
            continue

        patterns = config.get('patterns', [])
        exclude = config.get('exclude', [])
        keep_n = config.get('keep_newest', 0)

        files = find_files(patterns, exclude)

        if keep_n > 0:
            _, files = keep_newest(files, keep_n)

        for f in files:
            size = get_file_size(f)

            if backup:
                # Create backup
                rel_path = f.relative_to(PROJECT_ROOT)
                backup_path = BACKUP_DIR / rel_path
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    if f.is_dir():
                        shutil.copytree(f, backup_path)
                    else:
                        shutil.copy2(f, backup_path)
                except Exception as e:
                    print(f"  WARNING: Backup failed for {rel_path}: {e}")

            # Remove file/directory
            try:
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    f.unlink()

                removed_count += 1
                removed_size += size

                rel_path = f.relative_to(PROJECT_ROOT)
                print(f"  Removed: {rel_path} ({format_size(size)})")

            except Exception as e:
                print(f"  ERROR: Failed to remove {f.relative_to(PROJECT_ROOT)}: {e}")

    print("\n" + "=" * 70)
    print(f"CLEANUP COMPLETE")
    print(f"  Removed: {removed_count} files/directories")
    print(f"  Freed: {format_size(removed_size)}")
    if backup:
        print(f"  Backup: {BACKUP_DIR}")
    print("=" * 70 + "\n")

    return removed_count, removed_size


def generate_manifest():
    """Generate manifest of all files in project"""
    manifest = {
        "generated": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "gnu_components": [],
        "commercial_components": [],
        "other_files": [],
        "statistics": {
            "total_files": 0,
            "total_size": 0,
            "gnu_files": 0,
            "commercial_files": 0,
        }
    }

    print("\n" + "=" * 70)
    print("  GENERATING FILE MANIFEST")
    print("=" * 70 + "\n")

    # Collect all files
    all_files = [f for f in PROJECT_ROOT.rglob('*') if f.is_file()]

    for f in all_files:
        rel_path = str(f.relative_to(PROJECT_ROOT))
        size = f.stat().st_size

        file_info = {
            "path": rel_path,
            "size": size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        }

        manifest["statistics"]["total_files"] += 1
        manifest["statistics"]["total_size"] += size

        # Categorize by license
        is_gnu = any(rel_path.startswith(comp) for comp in GNU_COMPONENTS)
        is_commercial = any(rel_path.startswith(comp) for comp in COMMERCIAL_COMPONENTS)

        if is_gnu:
            manifest["gnu_components"].append(file_info)
            manifest["statistics"]["gnu_files"] += 1
        elif is_commercial:
            manifest["commercial_components"].append(file_info)
            manifest["statistics"]["commercial_files"] += 1
        else:
            manifest["other_files"].append(file_info)

    # Save manifest
    manifest_path = PROJECT_ROOT / "MANIFEST.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest saved to: {manifest_path}")
    print(f"\nStatistics:")
    print(f"  Total files: {manifest['statistics']['total_files']}")
    print(f"  Total size: {format_size(manifest['statistics']['total_size'])}")
    print(f"  GNU components: {manifest['statistics']['gnu_files']} files")
    print(f"  Commercial components: {manifest['statistics']['commercial_files']} files")
    print(f"  Other files: {len(manifest['other_files'])} files")
    print("\n" + "=" * 70 + "\n")

    return manifest


def split_licensing():
    """Create separate distributions for GNU and Commercial components"""
    print("\n" + "=" * 70)
    print("  SPLITTING GNU AND COMMERCIAL COMPONENTS")
    print("=" * 70 + "\n")

    dist_dir = PROJECT_ROOT / "distributions"
    gnu_dir = dist_dir / "igsoa-sim-community"
    commercial_dir = dist_dir / "igsoa-sim-commercial"

    print(f"Creating distributions in: {dist_dir}")
    print(f"  GNU: {gnu_dir}")
    print(f"  Commercial: {commercial_dir}")

    # Create distribution directories
    gnu_dir.mkdir(parents=True, exist_ok=True)
    commercial_dir.mkdir(parents=True, exist_ok=True)

    # Copy GNU components
    print("\nCopying GNU components...")
    for component in GNU_COMPONENTS:
        src = PROJECT_ROOT / component
        if not src.exists():
            continue

        dst = gnu_dir / component

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  Copied: {component}/ ({len(list(src.rglob('*')))} files)")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  Copied: {component}")

    # Copy commercial components
    print("\nCopying commercial components...")
    for component in COMMERCIAL_COMPONENTS:
        src = PROJECT_ROOT / component
        if not src.exists():
            continue

        # Commercial gets both GNU tools AND engine
        dst_commercial = commercial_dir / component

        if src.is_dir():
            shutil.copytree(src, dst_commercial, dirs_exist_ok=True)
            print(f"  Copied: {component}/ ({len(list(src.rglob('*')))} files)")
        else:
            dst_commercial.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst_commercial)
            print(f"  Copied: {component}")

    # Copy GNU tools to commercial distribution too (dual-license)
    print("\nCopying GNU tools to commercial distribution...")
    for component in GNU_COMPONENTS:
        src = PROJECT_ROOT / component
        if not src.exists():
            continue

        dst = commercial_dir / component

        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Create README files
    gnu_readme = gnu_dir / "README.md"
    with open(gnu_readme, 'w') as f:
        f.write("""# IGSOA-SIM Community Edition (GNU License)

This is the free, open-source distribution of IGSOA-SIM.

## What's Included
- Mission generator tools
- Analysis scripts (Python/Julia)
- CLI interface
- Documentation
- Benchmarks

## What's NOT Included
- Commercial physics engines (requires commercial license)
- FFTW integration
- Advanced optimizations

## License
GNU General Public License v3.0

See LICENSE file for details.

## Commercial License
For commercial engine access, visit: [Your website]
""")

    commercial_readme = commercial_dir / "README.md"
    with open(commercial_readme, 'w') as f:
        f.write("""# IGSOA-SIM Commercial Edition

This is the full commercial distribution of IGSOA-SIM.

## What's Included
- All GNU-licensed tools (mission generator, analysis, docs)
- Commercial physics engines (C++ DLLs)
- FFTW integration
- Full optimization suite

## License
- Tools/Analysis: GNU GPL v3.0
- Engines: Commercial license (see LICENSE_COMMERCIAL)

## Support
Commercial license includes:
- Email support
- Bug fixes
- Updates

Contact: [Your email]
""")

    print("\n" + "=" * 70)
    print("LICENSING SPLIT COMPLETE")
    print(f"  GNU distribution: {gnu_dir}")
    print(f"  Commercial distribution: {commercial_dir}")
    print("=" * 70 + "\n")


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="IGSOA-SIM Production Release Preparation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - see what would be removed
  python prepare_release.py --dry-run

  # Clean up (creates backup automatically)
  python prepare_release.py --clean

  # Clean without backup (dangerous!)
  python prepare_release.py --clean --no-backup

  # Generate file manifest
  python prepare_release.py --manifest

  # Split into GNU and Commercial distributions
  python prepare_release.py --split-licensing

  # Full release prep (all steps)
  python prepare_release.py --full-release-prep
        """
    )

    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without actually removing")

    parser.add_argument("--clean", action="store_true",
                       help="Execute cleanup (removes files)")

    parser.add_argument("--no-backup", action="store_true",
                       help="Don't create backup before cleanup (dangerous!)")

    parser.add_argument("--manifest", action="store_true",
                       help="Generate file manifest (MANIFEST.json)")

    parser.add_argument("--split-licensing", action="store_true",
                       help="Create separate GNU and Commercial distributions")

    parser.add_argument("--full-release-prep", action="store_true",
                       help="Execute all release preparation steps")

    parser.add_argument("--output-json", type=str,
                       help="Save analysis results to JSON file")

    args = parser.parse_args()

    # Default to dry-run if no action specified
    if not any([args.dry_run, args.clean, args.manifest, args.split_licensing, args.full_release_prep]):
        args.dry_run = True

    try:
        # Dry run analysis
        if args.dry_run or args.full_release_prep:
            results = analyze_cleanup(dry_run=True)

            if args.output_json:
                output_path = Path(args.output_json)
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Analysis results saved to: {output_path}")

        # Execute cleanup
        if args.clean or args.full_release_prep:
            if not args.dry_run and not args.full_release_prep:
                # Confirmation prompt
                response = input("\nProceed with cleanup? This will remove files! (yes/no): ")
                if response.lower() != 'yes':
                    print("Cleanup cancelled.")
                    return 0

            backup = not args.no_backup
            execute_cleanup(backup=backup)

        # Generate manifest
        if args.manifest or args.full_release_prep:
            generate_manifest()

        # Split licensing
        if args.split_licensing or args.full_release_prep:
            split_licensing()

        if args.full_release_prep:
            print("\n" + "=" * 70)
            print("  FULL RELEASE PREPARATION COMPLETE!")
            print("=" * 70)
            print("\nNext steps:")
            print("  1. Review distributions/ folder")
            print("  2. Add LICENSE files to each distribution")
            print("  3. Test both GNU and Commercial packages")
            print("  4. Create installation packages (ZIP/installer)")
            print("  5. Update documentation with version numbers")
            print("=" * 70 + "\n")

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
