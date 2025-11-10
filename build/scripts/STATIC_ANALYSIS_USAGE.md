# Static Analysis - Quick Usage Guide

## ⚡ Fast Commands

```bash
# Fast mode (2-3 minutes) - Recommended for regular use
python run_static_analysis.py --mode fast

# Normal mode (5-7 minutes) - Balanced checks
python run_static_analysis.py --mode normal

# Full mode (10+ minutes) - Comprehensive analysis
python run_static_analysis.py --mode full
```

## 🎯 Incremental Analysis

```bash
# Analyze only src/cpp directory
python run_static_analysis.py --dir src/cpp

# Analyze only dase_cli/src directory
python run_static_analysis.py --dir dase_cli/src

# Analyze specific file
python run_static_analysis.py --file src/cpp/analog_universal_node_engine_avx2.cpp

# Combine with mode
python run_static_analysis.py --mode fast --dir src/cpp
```

## 📊 Analysis Modes Comparison

| Mode | Speed | Checks | Use Case |
|------|-------|--------|----------|
| **fast** | ~2-3 min | Errors + Warnings | Daily development, PR checks |
| **normal** | ~5-7 min | + Performance + Portability | Pre-commit, regular scans |
| **full** | ~10+ min | All checks, all configs | Weekly deep scan, release prep |

## 🔍 What Each Mode Checks

### Fast Mode
- ✅ Errors (always enabled)
- ✅ Warnings
- ✅ Single configuration (--max-configs=1)
- ❌ Style issues
- ❌ Performance hints
- ❌ Multiple configurations

### Normal Mode  (Default)
- ✅ Errors
- ✅ Warnings
- ✅ Performance issues
- ✅ Portability problems
- ✅ Up to 2 configurations
- ❌ Style issues
- ❌ Information messages

### Full Mode
- ✅ Everything (--enable=all)
- ✅ Inconclusive issues
- ✅ All configurations (--force)
- ✅ Verbose output
- ⚠️ SLOW but thorough

## 💡 Recommended Workflow

```bash
# 1. During development (run frequently)
python run_static_analysis.py --mode fast --dir src/cpp

# 2. Before committing (check your changes)
python run_static_analysis.py --mode normal

# 3. Before merging PR (full check)
python run_static_analysis.py --mode full

# 4. Weekly deep scan (catch everything)
python run_static_analysis.py --mode full > weekly_scan.log
```

## 📁 Output Files

All reports saved to: `build/analysis_reports/`

```
cppcheck_report_TIMESTAMP.txt   ← Human-readable report
cppcheck_report_TIMESTAMP.xml   ← Machine-readable (CI/CD)
cppcheck_summary_TIMESTAMP.json ← Statistics
```

## 🚀 Windows Batch File

```batch
REM Fast mode
build\scripts\run_static_analysis.bat --mode fast

REM Analyze specific directory
build\scripts\run_static_analysis.bat --dir src/cpp

REM Get help
build\scripts\run_static_analysis.bat --help
```

## 🛠️ CI/CD Integration

### GitHub Actions Example
```yaml
- name: Static Analysis (Fast)
  run: python build/scripts/run_static_analysis.py --mode fast

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: cppcheck-report
    path: build/analysis_reports/
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running static analysis..."
python build/scripts/run_static_analysis.py --mode fast --dir src/cpp

if [ $? -ne 0 ]; then
    echo "Static analysis found issues! Fix before committing."
    exit 1
fi
```

## 🔧 Troubleshooting

### "cppcheck not found"
```bash
# Windows (Chocolatey)
choco install cppcheck

# Windows (pip - already installed for you)
pip install cppcheck-wheel

# Verify
cppcheck --version
```

### Analysis too slow
```bash
# Use fast mode
python run_static_analysis.py --mode fast

# Or analyze incrementally
python run_static_analysis.py --dir src/cpp
python run_static_analysis.py --dir dase_cli/src
```

### No issues found (seems wrong)
```bash
# Check suppressions file
cat build/scripts/cppcheck_suppressions.txt

# Try without suppressions (temporarily rename it)
mv build/scripts/cppcheck_suppressions.txt build/scripts/cppcheck_suppressions.txt.bak
python run_static_analysis.py --mode fast
```

## 📈 Performance Benchmarks

Based on 52 C/C++ files in IGSOA-SIM:

- **Fast mode**: ~2-3 minutes (31 files in src/cpp)
- **Normal mode**: ~5-7 minutes (estimated)
- **Full mode**: ~10-15 minutes (all files, all configs)

## 🎯 Next Steps

1. Run initial analysis: `python run_static_analysis.py --mode fast`
2. Review report in `build/analysis_reports/`
3. Fix critical issues (errors)
4. Fix warnings
5. Re-run to verify fixes
6. Add to CI/CD pipeline

---

**Happy coding with clean, analyzed code!** 🚀
