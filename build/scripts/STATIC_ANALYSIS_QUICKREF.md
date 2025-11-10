# Static Analysis Quick Reference Card

## 🚀 Quick Commands

```bash
# Run analysis (Windows)
build\scripts\run_static_analysis.bat

# Run analysis (Linux/Mac)
python3 build/scripts/run_static_analysis.py

# Check if cppcheck is installed
cppcheck --version
```

## 📊 Report Locations

```
build/analysis_reports/cppcheck_report_TIMESTAMP.txt    ← Read this
build/analysis_reports/cppcheck_summary_TIMESTAMP.json  ← Statistics
build/analysis_reports/cppcheck_report_TIMESTAMP.xml    ← For CI/CD
```

## 🎯 Priority Matrix

| Severity | Priority | Action |
|----------|----------|--------|
| **error** | 🔴 CRITICAL | Fix immediately, blocks release |
| **warning** | 🟡 HIGH | Fix before merge |
| **style** | 🔵 MEDIUM | Fix when time permits |
| **performance** | 🟢 LOW | Optimize if it matters |
| **information** | ⚪ INFO | Review, may ignore |

## 🐛 Common Issues for IGSOA-SIM

### Thread Safety (CRITICAL for your project!)
```cpp
// ❌ BAD
static EngineMetrics g_metrics;  // Race condition!

// ✅ GOOD
thread_local EngineMetrics g_metrics;  // Thread-safe
```

### Memory Leaks (FFTW plans)
```cpp
// ❌ BAD
fftw_plan p = fftw_plan_dft_1d(...);
// Missing cleanup

// ✅ GOOD
fftw_plan p = fftw_plan_dft_1d(...);
fftw_destroy_plan(p);  // Clean up
```

### Null Pointer Dereference
```cpp
// ❌ BAD
auto result = map.find(key);
return result->second;  // May be end()!

// ✅ GOOD
auto result = map.find(key);
if (result != map.end()) {
    return result->second;
}
```

### Buffer Overflow
```cpp
// ❌ BAD
char buf[256];
strcpy(buf, user_input);  // Unsafe!

// ✅ GOOD
char buf[256];
strncpy(buf, user_input, sizeof(buf) - 1);
buf[255] = '\0';
```

## 🔇 Suppressing False Positives

### Inline (Preferred)
```cpp
// cppcheck-suppress nullPointer
void* ptr = get_pointer();  // We validate this above
```

### Block
```cpp
// cppcheck-suppress-begin nullPointer
// Multiple lines of code
// that trigger false positive
// cppcheck-suppress-end nullPointer
```

### Global (suppressions.txt)
```
nullPointer:src/cpp/my_file.cpp:123
```

## 📈 Typical Issue Counts (Your Codebase)

Based on initial code review, expect:

| Category | Count | Status |
|----------|-------|--------|
| Thread Safety | 5-10 | 🔴 Must fix |
| Memory Leaks | 3-7 | 🟡 High priority |
| Null Pointers | 10-20 | 🟡 High priority |
| Style Issues | 50-100 | 🔵 Medium |
| Performance | 20-40 | 🟢 Review |

## 🔄 Workflow

```
┌─────────────┐
│ Run Analysis│
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Review Report   │
│ (focus on      │
│  errors first) │
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│ Fix Issues  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Re-run      │◄────┐
│ Analysis    │     │
└──────┬──────┘     │
       │            │
       ▼            │
┌─────────────┐     │
│ Still have  │─YES─┘
│ issues?     │
└──────┬──────┘
       │ NO
       ▼
┌─────────────┐
│ Commit Code │
└─────────────┘
```

## ⚙️ CI/CD Integration

Add to `.github/workflows/static-analysis.yml`:

```yaml
name: Static Analysis

on: [push, pull_request]

jobs:
  cppcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Install cppcheck
        run: sudo apt-get install -y cppcheck

      - name: Run Analysis
        run: python3 build/scripts/run_static_analysis.py

      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: cppcheck-report
          path: build/analysis_reports/

      - name: Check for Critical Issues
        run: |
          if grep -q "error:" build/analysis_reports/cppcheck_report_*.txt; then
            echo "Critical errors found!"
            exit 1
          fi
```

## 🛠️ Complementary Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **cppcheck** | Static analysis | Always (CI/CD) |
| **clang-tidy** | Modern C++ checks | Pre-commit |
| **MSVC /analyze** | Windows-specific | Windows builds |
| **valgrind** | Runtime memory check | Testing phase |
| **AddressSanitizer** | Runtime undefined behavior | Testing phase |

## 📚 Key Resources

- **cppcheck Manual:** http://cppcheck.sourceforge.net/manual.pdf
- **C++ Core Guidelines:** https://isocpp.github.io/CppCoreGuidelines/
- **Your Issues:** `docs/issues-fixes/ISSUES_SUMMARY.md`

## 🎓 Learning from Your Issues

Your codebase has these documented issues:

1. **C2.1** - Thread safety: `g_metrics` global state
2. **C2.2** - FFTW plan cache race condition
3. **C5.2** - Resource cleanup not guaranteed
4. **C5.3** - Engine ID generation not thread-safe

**Static analysis will find similar patterns!**

## 💡 Pro Tips

1. **Run before every commit** - Catch issues early
2. **Fix errors first** - Don't ignore critical issues
3. **Understand warnings** - Each warning is a potential bug
4. **Suppress carefully** - Document why you're suppressing
5. **Track progress** - Compare reports over time
6. **Automate** - Add to CI/CD pipeline

## 🏆 Goal

**Zero critical issues (errors/warnings) in production code!**

Target metrics:
- Errors: 0
- Warnings: < 10 (well-documented)
- Style: Improving over time

---

**Questions?** See `STATIC_ANALYSIS_README.md` for full documentation.
