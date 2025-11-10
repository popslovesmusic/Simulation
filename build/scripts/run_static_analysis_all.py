#!/usr/bin/env python3
"""
Unified Static Code Analysis for IGSOA-SIM
Runs static analysis for all languages: C++, Python, and Julia
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = Path(__file__).parent


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def safe_print(text):
    """Print text safely, handling encoding errors"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)


def print_header(text):
    """Print formatted header"""
    safe_print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    safe_print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    safe_print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    safe_print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message"""
    safe_print(f"{Colors.WARNING}[WARN] {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    safe_print(f"{Colors.FAIL}[ERROR] {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    safe_print(f"{Colors.OKCYAN}[INFO] {text}{Colors.ENDC}")


def run_cpp_analysis(mode, extra_args):
    """Run C++ static analysis"""
    print_header("C++ Static Analysis (cppcheck)")

    script = SCRIPTS_DIR / "run_static_analysis.py"
    if not script.exists():
        print_error(f"C++ analysis script not found: {script}")
        return 1

    cmd = [sys.executable, str(script), "--mode", mode] + extra_args

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except Exception as e:
        print_error(f"Failed to run C++ analysis: {e}")
        return 1


def run_python_analysis(mode, extra_args):
    """Run Python static analysis"""
    print_header("Python Static Analysis (ruff + mypy)")

    script = SCRIPTS_DIR / "run_static_analysis_python.py"
    if not script.exists():
        print_error(f"Python analysis script not found: {script}")
        return 1

    cmd = [sys.executable, str(script), "--mode", mode] + extra_args

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except Exception as e:
        print_error(f"Failed to run Python analysis: {e}")
        return 1


def run_julia_analysis(mode, extra_args):
    """Run Julia static analysis"""
    print_header("Julia Static Analysis (Lint.jl + JET.jl)")

    script = SCRIPTS_DIR / "run_static_analysis_julia.jl"
    if not script.exists():
        print_error(f"Julia analysis script not found: {script}")
        return 1

    # Check if Julia is available
    try:
        result = subprocess.run(
            ["julia", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print_warning("Julia not found. Skipping Julia analysis.")
            return 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print_warning("Julia not found. Skipping Julia analysis.")
        return 0

    cmd = ["julia", str(script), "--mode", mode] + extra_args

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode
    except Exception as e:
        print_error(f"Failed to run Julia analysis: {e}")
        return 1


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(
        description="IGSOA-SIM Unified Static Code Analysis (All Languages)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Analysis Modes:
  fast    - Quick scan (~3-5 minutes total)
  normal  - Balanced scan (~7-10 minutes total) [DEFAULT]
  full    - Comprehensive scan (~20+ minutes total)

Language Selection:
  --cpp-only     - Run only C++ analysis
  --python-only  - Run only Python analysis
  --julia-only   - Run only Julia analysis
  (default: run all languages)

Examples:
  python run_static_analysis_all.py                    # All languages, normal mode
  python run_static_analysis_all.py --mode fast        # All languages, fast mode
  python run_static_analysis_all.py --cpp-only         # Only C++
  python run_static_analysis_all.py --mode full        # All languages, full scan
        """
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "normal", "full"],
        default="normal",
        help="Analysis mode (default: normal)"
    )
    parser.add_argument(
        "--cpp-only",
        action="store_true",
        help="Run only C++ analysis"
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="Run only Python analysis"
    )
    parser.add_argument(
        "--julia-only",
        action="store_true",
        help="Run only Julia analysis"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Pass --dir argument to language-specific scripts"
    )

    args, unknown_args = parser.parse_known_args()

    # Build extra args to pass to sub-scripts
    extra_args = []
    if args.dir:
        extra_args.extend(["--dir", args.dir])
    extra_args.extend(unknown_args)

    print_header("IGSOA-SIM Unified Static Code Analysis")
    print_info(f"Project root: {PROJECT_ROOT}")
    print_info(f"Mode: {args.mode.upper()}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Determine which analyses to run
    run_cpp = args.cpp_only or not (args.python_only or args.julia_only)
    run_python = args.python_only or not (args.cpp_only or args.julia_only)
    run_julia = args.julia_only or not (args.cpp_only or args.python_only)

    languages = []
    if run_cpp:
        languages.append("C++")
    if run_python:
        languages.append("Python")
    if run_julia:
        languages.append("Julia")

    print_info(f"Running analysis for: {', '.join(languages)}")
    print()

    # Run analyses
    results = {}

    if run_cpp:
        results["C++"] = run_cpp_analysis(args.mode, extra_args)
        print()

    if run_python:
        results["Python"] = run_python_analysis(args.mode, extra_args)
        print()

    if run_julia:
        results["Julia"] = run_julia_analysis(args.mode, extra_args)
        print()

    # Print final summary
    print_header("Final Summary")

    all_passed = True
    for lang, returncode in results.items():
        if returncode == 0:
            print_success(f"{lang}: PASSED")
        else:
            print_error(f"{lang}: FAILED (exit code {returncode})")
            all_passed = False

    print()

    if all_passed:
        print_success("All static analysis checks passed!")
        return 0
    else:
        print_error("Some static analysis checks failed!")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_error("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
