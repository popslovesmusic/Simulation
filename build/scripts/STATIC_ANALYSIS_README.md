# Static Code Analysis Guide

This directory contains scripts for automated static code analysis of the IGSOA-SIM C/C++ codebase.

## Quick Start

### Windows
```batch
cd build\scripts
run_static_analysis.bat
```

### Linux/macOS
```bash
cd build/scripts
python3 run_static_analysis.py
```

## Prerequisites

### 1. Install Python
- Python 3.7 or later required
- Download: https://www.python.org/downloads/

### 2. Install cppcheck

**Windows:**
```batch
# Option 1: Chocolatey
choco install cppcheck

# Option 2: Manual download
# Download from: http://cppcheck.sourceforge.net/
# Add to PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install cppcheck
```

**macOS:**
```bash
brew install cppcheck
```

### 3. Verify Installation
```bash
cppcheck --version
```

## What the Script Does

1. **Discovers C/C++ Files**
   - Scans `src/cpp/`, `dase_cli/src/`, `tests/`
   - Finds all `.cpp`, `.c`, `.h`, `.hpp` files
   - Excludes archived and build directories

2. **Runs Static Analysis**
   - Uses cppcheck with comprehensive checks enabled
   - Checks for:
     - Memory leaks
     - Null pointer dereferences
     - Buffer overflows
     - Thread safety issues
     - Performance problems
     - Style issues
     - Portability concerns

3. **Generates Reports**
   - Text report: Human-readable issue list
   - XML report: Machine-readable format
   - JSON summary: Statistics and top issues

## Output Location

All reports are saved to: `build/analysis_reports/`

Example files:
- `cppcheck_report_20250107_143000.txt` - Full issue list
- `cppcheck_report_20250107_143000.xml` - XML format
- `cppcheck_summary_20250107_143000.json` - Summary statistics

## Understanding the Results

### Severity Levels

1. **error** - Critical bugs that will cause crashes or incorrect behavior
2. **warning** - Potential bugs that should be investigated
3. **style** - Code style improvements
4. **performance** - Performance optimization opportunities
5. **portability** - Portability issues across platforms
6. **information** - General information messages

### Priority of Fixes

**Fix Immediately:**
- All `error` severity issues
- Thread safety problems (`concurrency-*`)
- Memory management issues (`memleak`, `memoryLeak`)
- Null pointer dereferences (`nullPointer`)

**Fix Soon:**
- `warning` severity issues
- Performance bottlenecks in hot paths
- Resource leaks

**Fix When Time Permits:**
- Style issues
- Minor portability concerns
- Informational messages

## Suppressing False Positives

If cppcheck reports a false positive, you can suppress it:

### Inline Suppression (Recommended)
```cpp
// cppcheck-suppress nullPointer
void* ptr = get_pointer();  // We know this is safe here
```

### File-level Suppression
```cpp
// At top of file
// cppcheck-suppress-begin nullPointer
// ... code ...
// cppcheck-suppress-end nullPointer
```

### Global Suppression
Edit `build/scripts/cppcheck_suppressions.txt`:
```
nullPointer:src/cpp/my_file.cpp:123
```

Then modify the script to use `--suppressions-list=cppcheck_suppressions.txt`

## Advanced Usage

### Analyze Specific Files Only
```bash
python run_static_analysis.py --files src/cpp/specific_file.cpp
```

### Custom Configuration
Edit `run_static_analysis.py` to modify:
- `SOURCE_DIRS` - Directories to scan
- `EXCLUDE_DIRS` - Directories to skip
- `CPP_EXTENSIONS` - File extensions to analyze

### Integration with CI/CD

Add to your build pipeline:
```yaml
# Example GitHub Actions
- name: Run Static Analysis
  run: python build/scripts/run_static_analysis.py

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: static-analysis-report
    path: build/analysis_reports/
```

## Complementary Tools

Consider adding these tools for comprehensive analysis:

### 1. Clang-Tidy
More sophisticated C++ analysis:
```bash
clang-tidy src/cpp/*.cpp -- -std=c++17 -mavx2
```

### 2. MSVC Static Analyzer
Built into Visual Studio:
```bash
cl /analyze /W4 your_file.cpp
```

### 3. Valgrind (Linux only)
Runtime memory checking:
```bash
valgrind --leak-check=full ./your_program
```

## Expected Issues for IGSOA-SIM

Based on the codebase review, expect to find:

### High Priority
- **Thread safety violations** in `g_metrics` global state
- **FFTW plan cache race conditions**
- **Resource cleanup** not guaranteed in destructors
- **Non-atomic** engine ID generation

### Medium Priority
- Missing const correctness
- No bounds checking in hot paths
- Hardcoded magic numbers (48000, 0.999999)
- Memory leak risks in FFTW plan cache

### Style/Performance
- AVX2 alignment issues
- OpenMP data sharing concerns
- Missing null checks

## Workflow Example

1. **Run initial analysis:**
   ```bash
   run_static_analysis.bat
   ```

2. **Review critical issues:**
   ```bash
   # Open: build/analysis_reports/cppcheck_report_TIMESTAMP.txt
   # Focus on 'error' and 'warning' severity
   ```

3. **Fix issues:**
   - Start with thread safety (concurrency issues)
   - Fix memory leaks
   - Address null pointer dereferences

4. **Re-run analysis:**
   ```bash
   run_static_analysis.bat
   ```

5. **Verify fixes:**
   - Compare new report with previous
   - Ensure issue count decreases

6. **Iterate until clean:**
   - Aim for zero critical issues
   - Minimize warnings

## Troubleshooting

### "cppcheck not found"
- Ensure cppcheck is installed
- Add to system PATH
- On Windows, restart terminal after installation

### "Analysis timed out"
- Reduce scope: analyze one directory at a time
- Increase timeout in script (line with `timeout=600`)

### Too many false positives
- Use inline suppressions for known safe code
- Create suppressions file for systematic exclusions

## Resources

- **cppcheck Manual:** http://cppcheck.sourceforge.net/manual.pdf
- **C++ Core Guidelines:** https://isocpp.github.io/CppCoreGuidelines/
- **Thread Safety:** https://wiki.sei.cmu.edu/confluence/display/c/CON

## Contributing

When adding new C++ code:
1. Run static analysis before committing
2. Fix all errors and warnings
3. Document any necessary suppressions
4. Keep the codebase clean!

---

**Last Updated:** November 2025
