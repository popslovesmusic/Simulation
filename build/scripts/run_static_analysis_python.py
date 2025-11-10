#!/usr/bin/env python3
"""
Python Static Code Analysis Wrapper for IGSOA-SIM
Automatically discovers Python files and runs static analysis tools
"""

import os
import subprocess
import sys
import json
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
ANALYSIS_OUTPUT_DIR = PROJECT_ROOT / "build" / "analysis_reports" / "python"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Directories to analyze
SOURCE_DIRS = [
    "src/python",
    "analysis",
    "benchmarks/python",
    "missions",
    "tests",
    "tools",
    "fixes",
]

# Directories to exclude
EXCLUDE_DIRS = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "*.egg-info",
]


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
    UNDERLINE = '\033[4m'


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


def find_python_files():
    """
    Recursively find all Python source files in the project
    Returns: List of Path objects
    """
    print_header("Discovering Python Source Files")

    py_files = []

    for source_dir in SOURCE_DIRS:
        dir_path = PROJECT_ROOT / source_dir
        if not dir_path.exists():
            print_warning(f"Directory not found: {source_dir}")
            continue

        print_info(f"Scanning: {source_dir}")

        for root, dirs, files in os.walk(dir_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    py_files.append(file_path)

    # Sort for consistent ordering
    py_files.sort()

    print_success(f"Found {len(py_files)} Python files")
    return py_files


def check_tool_available(tool_name, install_cmd):
    """Check if a tool is installed and available"""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print_success(f"{tool_name} found: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print_error(f"{tool_name} not found!")
    print_info(f"Install with: {install_cmd}")
    return False


def run_ruff(py_files, mode="normal"):
    """
    Run ruff linter on Python files

    Args:
        py_files: List of Python files to analyze
        mode: Analysis mode (fast, normal, or full)

    Returns: (return_code, issues_count)
    """
    print_header(f"Running Ruff Linter ({mode.upper()} mode)")

    # Create output directory
    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Output file
    report_txt = ANALYSIS_OUTPUT_DIR / f"ruff_report_{TIMESTAMP}.txt"
    report_json = ANALYSIS_OUTPUT_DIR / f"ruff_report_{TIMESTAMP}.json"

    # Convert file paths to strings relative to project root
    file_list = [str(f.relative_to(PROJECT_ROOT)) for f in py_files]

    # Build ruff command based on mode
    cmd = ["ruff", "check"]

    if mode == "fast":
        # Fast mode: Only critical checks
        cmd.extend([
            "--select", "E,F,W",  # pycodestyle errors, pyflakes, warnings
            "--output-format", "json",
        ])
        print_info("Using FAST mode: errors and warnings only")

    elif mode == "normal":
        # Normal mode: Standard checks
        cmd.extend([
            "--select", "E,F,W,C90,I,N,UP",  # + complexity, imports, naming, upgrades
            "--output-format", "json",
        ])
        print_info("Using NORMAL mode: standard checks")

    elif mode == "full":
        # Full mode: All checks
        cmd.extend([
            "--select", "ALL",  # All rules
            "--output-format", "json",
        ])
        print_warning("Using FULL mode: comprehensive analysis (may find many issues)")

    cmd += file_list

    print_info(f"Running ruff on {len(file_list)} files...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300
        )

        # Write outputs
        with open(report_json, 'w', encoding='utf-8') as f:
            f.write(result.stdout if result.stdout else "[]")

        # Parse JSON and create text report
        try:
            issues = json.loads(result.stdout if result.stdout else "[]")
            with open(report_txt, 'w', encoding='utf-8') as f:
                if issues:
                    for issue in issues:
                        location = f"{issue.get('filename', 'unknown')}:{issue.get('location', {}).get('row', 0)}:{issue.get('location', {}).get('column', 0)}"
                        f.write(f"{location}: {issue.get('code', 'unknown')}: {issue.get('message', '')}\n")
                else:
                    f.write("No issues found!\n")

            print_success(f"Ruff analysis complete!")
            print_info(f"Found {len(issues)} issues")
            print_info(f"Report: {report_txt.relative_to(PROJECT_ROOT)}")

            return 0, len(issues)
        except json.JSONDecodeError:
            print_warning("Could not parse ruff JSON output")
            return 0, 0

    except subprocess.TimeoutExpired:
        print_error("Ruff analysis timed out after 5 minutes")
        return 1, 0
    except Exception as e:
        print_error(f"Ruff analysis failed: {e}")
        return 1, 0


def run_mypy(py_files, mode="normal"):
    """
    Run mypy type checker on Python files

    Args:
        py_files: List of Python files to analyze
        mode: Analysis mode (fast, normal, or full)

    Returns: (return_code, issues_count)
    """
    print_header(f"Running MyPy Type Checker ({mode.upper()} mode)")

    # Output file
    report_txt = ANALYSIS_OUTPUT_DIR / f"mypy_report_{TIMESTAMP}.txt"

    # Convert file paths to strings relative to project root
    file_list = [str(f.relative_to(PROJECT_ROOT)) for f in py_files]

    # Build mypy command based on mode
    cmd = ["mypy"]

    if mode == "fast":
        # Fast mode: Basic type checking
        cmd.extend([
            "--no-strict-optional",
            "--allow-untyped-calls",
            "--allow-untyped-defs",
        ])
        print_info("Using FAST mode: basic type checking")

    elif mode == "normal":
        # Normal mode: Standard type checking
        cmd.extend([
            "--ignore-missing-imports",
            "--no-strict-optional",
        ])
        print_info("Using NORMAL mode: standard type checking")

    elif mode == "full":
        # Full mode: Strict type checking
        cmd.extend([
            "--strict",
            "--warn-return-any",
            "--warn-unused-configs",
        ])
        print_warning("Using FULL mode: strict type checking")

    cmd += file_list

    print_info(f"Running mypy on {len(file_list)} files...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=300
        )

        # Write output
        output = result.stdout + result.stderr
        with open(report_txt, 'w', encoding='utf-8') as f:
            f.write(output if output else "No issues found!\n")

        # Count issues (lines that contain ": error:" or ": note:")
        issues_count = len([line for line in output.split('\n') if ': error:' in line])

        print_success(f"MyPy analysis complete!")
        print_info(f"Found {issues_count} type errors")
        print_info(f"Report: {report_txt.relative_to(PROJECT_ROOT)}")

        return 0, issues_count

    except subprocess.TimeoutExpired:
        print_error("MyPy analysis timed out after 5 minutes")
        return 1, 0
    except Exception as e:
        print_error(f"MyPy analysis failed: {e}")
        return 1, 0


def print_summary(ruff_issues, mypy_issues):
    """Print analysis summary"""
    print_header("Python Analysis Summary")

    total_issues = ruff_issues + mypy_issues

    if total_issues == 0:
        print_success("No issues found!")
        return

    print_info(f"Total issues found: {total_issues}")
    print()
    print(f"{Colors.BOLD}By Tool:{Colors.ENDC}")
    print(f"  Ruff (linting):      {ruff_issues:5}")
    print(f"  MyPy (type checking): {mypy_issues:5}")


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(
        description="IGSOA-SIM Python Static Code Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Analysis Modes:
  fast    - Quick scan (basic checks, ~1 minute)
  normal  - Balanced scan (standard checks, ~2-3 minutes) [DEFAULT]
  full    - Comprehensive scan (strict checks, ~5+ minutes)

Incremental Options:
  --dir DIR  - Analyze only files in specific directory (e.g., src/python)
  --file FILE - Analyze only specific file

Examples:
  python run_static_analysis_python.py                    # Normal mode, all files
  python run_static_analysis_python.py --mode fast        # Fast mode
  python run_static_analysis_python.py --dir src/python   # Only src/python
  python run_static_analysis_python.py --file test.py     # Single file
        """
    )
    parser.add_argument(
        "--mode",
        choices=["fast", "normal", "full"],
        default="normal",
        help="Analysis mode (default: normal)"
    )
    parser.add_argument(
        "--dir",
        type=str,
        help="Analyze only files in this directory"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Analyze only this specific file"
    )
    parser.add_argument(
        "--skip-ruff",
        action="store_true",
        help="Skip ruff linting"
    )
    parser.add_argument(
        "--skip-mypy",
        action="store_true",
        help="Skip mypy type checking"
    )

    args = parser.parse_args()

    print_header("IGSOA-SIM Python Static Code Analysis")
    print_info(f"Project root: {PROJECT_ROOT}")
    print_info(f"Timestamp: {TIMESTAMP}")
    print_info(f"Mode: {args.mode.upper()}")

    # Step 1: Find Python files
    py_files = find_python_files()

    if not py_files:
        print_error("No Python files found to analyze!")
        return 1

    # Filter by directory or file if specified
    if args.dir:
        filter_dir = PROJECT_ROOT / args.dir
        py_files = [f for f in py_files if filter_dir in f.parents or f.parent == filter_dir]
        print_info(f"Filtered to directory: {args.dir} ({len(py_files)} files)")

    if args.file:
        filter_file = PROJECT_ROOT / args.file
        py_files = [f for f in py_files if f == filter_file]
        print_info(f"Filtered to file: {args.file}")

    if not py_files:
        print_error("No files match the filter!")
        return 1

    print()

    # Step 2: Check tools availability
    tools_ok = True

    if not args.skip_ruff:
        if not check_tool_available("ruff", "pip install ruff"):
            tools_ok = False
            args.skip_ruff = True

    if not args.skip_mypy:
        if not check_tool_available("mypy", "pip install mypy"):
            tools_ok = False
            args.skip_mypy = True

    if not tools_ok:
        print_warning("Some tools are missing. Install them and re-run.")
        print_info("Quick install: pip install ruff mypy")
        # Continue with available tools

    print()

    # Step 3: Run analyses
    ruff_issues = 0
    mypy_issues = 0

    if not args.skip_ruff:
        _, ruff_issues = run_ruff(py_files, mode=args.mode)
        print()

    if not args.skip_mypy:
        _, mypy_issues = run_mypy(py_files, mode=args.mode)
        print()

    # Step 4: Display summary
    print_summary(ruff_issues, mypy_issues)

    print()
    print_success("Python static analysis complete!")

    return 0


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
