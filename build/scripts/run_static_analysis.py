#!/usr/bin/env python3
"""
Static Code Analysis Wrapper for IGSOA-SIM
Automatically discovers C/C++ files and runs static analysis tools
"""

import os
import subprocess
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        # Enable UTF-8 mode for Windows console
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
ANALYSIS_OUTPUT_DIR = PROJECT_ROOT / "build" / "analysis_reports"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# Directories to analyze
SOURCE_DIRS = [
    "src/cpp",
    "dase_cli/src",
    "tests",
]

# Directories to exclude
EXCLUDE_DIRS = [
    "archive",
    "build",
    ".git",
    "__pycache__",
]

# File extensions to analyze
CPP_EXTENSIONS = [".cpp", ".c", ".cc", ".cxx", ".h", ".hpp", ".hxx"]


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
        # Fallback to ASCII if Unicode fails
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


def find_cpp_files():
    """
    Recursively find all C/C++ source files in the project
    Returns: List of Path objects
    """
    print_header("Discovering C/C++ Source Files")

    cpp_files = []

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
                if any(file.endswith(ext) for ext in CPP_EXTENSIONS):
                    file_path = Path(root) / file
                    cpp_files.append(file_path)

    # Sort for consistent ordering
    cpp_files.sort()

    print_success(f"Found {len(cpp_files)} C/C++ files")

    # Print breakdown by extension
    extension_counts = {}
    for file in cpp_files:
        ext = file.suffix
        extension_counts[ext] = extension_counts.get(ext, 0) + 1

    print_info("File breakdown:")
    for ext, count in sorted(extension_counts.items()):
        print(f"  {ext:8} {count:4} files")

    return cpp_files


def check_cppcheck_available():
    """Check if cppcheck is installed and available"""
    try:
        result = subprocess.run(
            ["cppcheck", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"cppcheck found: {version}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print_error("cppcheck not found!")
    print_info("Install cppcheck:")
    print_info("  Windows: choco install cppcheck  OR  download from http://cppcheck.sourceforge.net/")
    print_info("  Linux:   sudo apt install cppcheck")
    print_info("  macOS:   brew install cppcheck")
    return False


def run_cppcheck(cpp_files, mode="normal"):
    """
    Run cppcheck on the discovered files

    Args:
        cpp_files: List of C/C++ files to analyze
        mode: Analysis mode ("fast", "normal", or "full")

    Returns: (return_code, report_path, summary)
    """
    print_header(f"Running Static Analysis with cppcheck ({mode.upper()} mode)")

    # Create output directory
    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Output files
    report_txt = ANALYSIS_OUTPUT_DIR / f"cppcheck_report_{TIMESTAMP}.txt"
    report_xml = ANALYSIS_OUTPUT_DIR / f"cppcheck_report_{TIMESTAMP}.xml"
    report_json = ANALYSIS_OUTPUT_DIR / f"cppcheck_summary_{TIMESTAMP}.json"

    # Convert file paths to strings relative to project root
    file_list = [str(f.relative_to(PROJECT_ROOT)) for f in cpp_files]

    # Check for suppressions file
    suppressions_file = Path(__file__).parent / "cppcheck_suppressions.txt"

    # Build cppcheck command based on mode
    cmd = ["cppcheck"]

    if mode == "fast":
        # Fast mode: Only critical checks, ~2-3x faster
        cmd.extend([
            "--enable=warning",          # Warnings (errors always enabled)
            "--language=c++",            # Force C++ mode
            "--std=c++17",
            "--platform=native",
            "--inline-suppr",
            "--max-configs=1",           # Only check one configuration (FAST!)
            "--template={file}:{line}:{column}: {severity}: {id}: {message}",
            "--xml",
            "--xml-version=2",
        ])
        print_info("Using FAST mode: errors + warnings only, single configuration")

    elif mode == "normal":
        # Normal mode: Balanced checks, good for regular use
        cmd.extend([
            "--enable=warning,performance,portability",
            "--language=c++",            # Force C++ mode
            "--std=c++17",
            "--platform=native",
            "--inline-suppr",
            "--max-configs=2",           # Check up to 2 configurations
            "--template={file}:{line}:{column}: {severity}: {id}: {message}",
            "--xml",
            "--xml-version=2",
        ])
        print_info("Using NORMAL mode: errors + warnings + performance + portability")

    elif mode == "full":
        # Full mode: Comprehensive analysis (SLOW but thorough)
        cmd.extend([
            "--enable=all",              # Enable all checks
            "--inconclusive",            # Report even uncertain issues
            "--language=c++",            # Force C++ mode
            "--std=c++17",
            "--platform=native",
            "--inline-suppr",
            "--force",                   # Force checking all configurations (SLOW!)
            "--verbose",
            "--template={file}:{line}:{column}: {severity}: {id}: {message}",
            "--xml",
            "--xml-version=2",
        ])
        print_warning("Using FULL mode: comprehensive analysis (may take 10+ minutes)")

    else:
        print_error(f"Unknown mode: {mode}")
        return 1, None, None

    # Add suppressions file if it exists (handles missingIncludeSystem, etc.)
    if suppressions_file.exists():
        cmd.append(f"--suppressions-list={suppressions_file}")
        print_info(f"Using suppressions file: {suppressions_file.name}")

    cmd += file_list

    print_info(f"Running cppcheck on {len(file_list)} files...")
    print_info("This may take a few minutes...")

    try:
        # Run cppcheck (without --output-file, capture stdout/stderr instead)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=600  # 10 minute timeout
        )

        # Write outputs to files
        # cppcheck sends results to stderr, XML also to stderr
        if result.stderr:
            with open(report_xml, 'w', encoding='utf-8') as f:
                f.write(result.stderr)

        # cppcheck text output (parse from stderr, non-XML parts)
        if result.stdout or result.stderr:
            # Filter out XML tags to get text report
            text_output = result.stdout if result.stdout else ""
            # Also include stderr messages that aren't XML
            if result.stderr and not result.stderr.strip().startswith('<?xml'):
                text_output += result.stderr

            with open(report_txt, 'w', encoding='utf-8') as f:
                f.write(text_output if text_output else "No issues found!\n")

        # Parse and summarize results
        summary = parse_cppcheck_report(report_txt)

        # Write JSON summary
        with open(report_json, 'w') as f:
            json.dump(summary, f, indent=2)

        print_success(f"Analysis complete!")
        print_info(f"Text report: {report_txt.relative_to(PROJECT_ROOT)}")
        print_info(f"XML report:  {report_xml.relative_to(PROJECT_ROOT)}")
        print_info(f"Summary:     {report_json.relative_to(PROJECT_ROOT)}")

        return 0, report_txt, summary

    except subprocess.TimeoutExpired:
        print_error("Analysis timed out after 10 minutes")
        return 1, None, None
    except Exception as e:
        print_error(f"Analysis failed: {e}")
        return 1, None, None


def parse_cppcheck_report(report_txt_path):
    """
    Parse the cppcheck XML report and create a summary
    Note: We parse the XML file, not the text file
    """
    # Derive XML path from text path
    xml_path = report_txt_path.parent / report_txt_path.name.replace('.txt', '.xml')

    if not xml_path or not xml_path.exists():
        return {"error": "XML report file not found"}

    summary = {
        "timestamp": TIMESTAMP,
        "total_issues": 0,
        "by_severity": {},
        "by_type": {},
        "by_file": {},
        "critical_issues": [],
    }

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Parse all <error> elements
        for error in root.findall('.//error'):
            issue_id = error.get('id', 'unknown')
            severity = error.get('severity', 'unknown')
            msg = error.get('msg', '')

            # Get location info
            location_elem = error.find('location')
            if location_elem is not None:
                file_name = location_elem.get('file', 'unknown')
                line = location_elem.get('line', '0')
                column = location_elem.get('column', '0')
                location = f"{file_name}:{line}:{column}"
            else:
                file_name = error.get('file0', 'unknown')
                location = f"{file_name}:0:0"

            # Skip information-only messages unless they're important
            if severity == "information" and issue_id in ["normalCheckLevelMaxBranches", "toomanyconfigs"]:
                continue

            summary["total_issues"] += 1

            # Count by severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

            # Count by type
            summary["by_type"][issue_id] = summary["by_type"].get(issue_id, 0) + 1

            # Count by file
            summary["by_file"][file_name] = summary["by_file"].get(file_name, 0) + 1

            # Track critical issues
            if severity in ["error", "warning"]:
                summary["critical_issues"].append({
                    "location": location,
                    "severity": severity,
                    "id": issue_id,
                    "message": msg
                })

    except Exception as e:
        summary["parse_error"] = str(e)

    return summary


def print_summary(summary):
    """Print analysis summary to console"""
    print_header("Analysis Summary")

    if "error" in summary or "parse_error" in summary:
        print_error("Failed to parse results")
        return

    total = summary.get("total_issues", 0)

    if total == 0:
        print_success("No issues found! 🎉")
        return

    print_info(f"Total issues found: {total}")
    print()

    # Print by severity
    print(f"{Colors.BOLD}By Severity:{Colors.ENDC}")
    severities = summary.get("by_severity", {})
    for severity in ["error", "warning", "style", "performance", "portability", "information"]:
        count = severities.get(severity, 0)
        if count > 0:
            color = Colors.FAIL if severity == "error" else Colors.WARNING if severity == "warning" else Colors.OKCYAN
            print(f"  {color}{severity:15} {count:5}{Colors.ENDC}")
    print()

    # Print top 10 issue types
    print(f"{Colors.BOLD}Top Issue Types:{Colors.ENDC}")
    by_type = summary.get("by_type", {})
    sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:10]
    for issue_type, count in sorted_types:
        print(f"  {issue_type:30} {count:5}")
    print()

    # Print top 10 files with most issues
    print(f"{Colors.BOLD}Files with Most Issues:{Colors.ENDC}")
    by_file = summary.get("by_file", {})
    sorted_files = sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10]
    for file_name, count in sorted_files:
        print(f"  {file_name:50} {count:5}")
    print()

    # Print critical issues (first 20)
    critical = summary.get("critical_issues", [])
    if critical:
        print(f"{Colors.BOLD}Critical Issues (showing first 20):{Colors.ENDC}")
        for issue in critical[:20]:
            severity_color = Colors.FAIL if issue["severity"] == "error" else Colors.WARNING
            print(f"  {severity_color}{issue['location']}{Colors.ENDC}")
            print(f"    [{issue['severity']}] {issue['id']}: {issue['message']}")

        if len(critical) > 20:
            print(f"\n  ... and {len(critical) - 20} more critical issues")


def main():
    """Main execution flow"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="IGSOA-SIM Static Code Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Analysis Modes:
  fast    - Quick scan (errors + warnings only, ~2-3 minutes)
  normal  - Balanced scan (+ performance + portability, ~5-7 minutes) [DEFAULT]
  full    - Comprehensive scan (all checks, may take 10+ minutes)

Incremental Options:
  --dir DIR  - Analyze only files in specific directory (e.g., src/cpp)
  --file FILE - Analyze only specific file

Examples:
  python run_static_analysis.py                    # Normal mode, all files
  python run_static_analysis.py --mode fast        # Fast mode
  python run_static_analysis.py --dir src/cpp      # Only src/cpp directory
  python run_static_analysis.py --file test.cpp    # Single file
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

    args = parser.parse_args()

    print_header("IGSOA-SIM Static Code Analysis")
    print_info(f"Project root: {PROJECT_ROOT}")
    print_info(f"Timestamp: {TIMESTAMP}")
    print_info(f"Mode: {args.mode.upper()}")

    # Step 1: Find C/C++ files
    cpp_files = find_cpp_files()

    if not cpp_files:
        print_error("No C/C++ files found to analyze!")
        return 1

    # Filter by directory or file if specified
    if args.dir:
        filter_dir = PROJECT_ROOT / args.dir
        cpp_files = [f for f in cpp_files if filter_dir in f.parents or f.parent == filter_dir]
        print_info(f"Filtered to directory: {args.dir} ({len(cpp_files)} files)")

    if args.file:
        filter_file = PROJECT_ROOT / args.file
        cpp_files = [f for f in cpp_files if f == filter_file]
        print_info(f"Filtered to file: {args.file}")

    if not cpp_files:
        print_error("No files match the filter!")
        return 1

    print()

    # Step 2: Check if cppcheck is available
    if not check_cppcheck_available():
        return 1

    print()

    # Step 3: Run analysis
    return_code, report_path, summary = run_cppcheck(cpp_files, mode=args.mode)

    if return_code != 0:
        return return_code

    print()

    # Step 4: Display summary
    if summary:
        print_summary(summary)

    print()
    print_success("Static analysis complete!")
    if report_path:
        print_info(f"Review the full report: {report_path.relative_to(PROJECT_ROOT)}")

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
