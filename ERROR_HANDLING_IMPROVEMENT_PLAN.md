# Error Handling Improvement Plan

**Date:** November 10, 2025
**Version:** 1.0
**Status:** Ready for Implementation

---

## Quick Start

**The automated review report was INCORRECT** - significant error handling exists. However, standardization and enhancements would improve production readiness.

**Timeline:** 3-4 weeks (~25-33 hours)
**Priority:** Medium
**Status:** Optional enhancement (not critical)

---

## Phase 1: Documentation & Standards (Week 5)

**Goal:** Define and document error handling patterns

### Task 1.1: Create Error Handling Guide
**Time:** 2 hours

**Create:** `docs/ERROR_HANDLING_GUIDE.md`

**Content:**
```markdown
# IGSOA-SIM Error Handling Guide

## C++ Patterns

### Use Exceptions For:
- Invalid configuration
- Resource allocation failures
- Unrecoverable errors

### Use Return Codes For:
- Optional values (nullptr, -1)
- Expected failures (bounds checking)
- Performance-critical paths

### Example:
void SymmetryField::validateConfig(const Config& config) {
    if (config.nx <= 0) {
        throw std::invalid_argument("Grid size must be positive");
    }
}

## Python Patterns

### Always Catch Specific Exceptions:
try:
    result = process_data(input)
except FileNotFoundError:
    logger.error("Input file not found")
    return default_result()
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise

## JavaScript Patterns

### Use Try/Catch for Async Operations:
try {
    const result = await processCommand(cmd);
    res.json(result);
} catch (error) {
    logger.error('Command failed:', error);
    res.status(500).json({error: error.message});
}
```

### Task 1.2: Audit Current Patterns
**Time:** 2 hours

**Create:** `ERROR_HANDLING_AUDIT.md`

```bash
# Count current patterns
grep -r "try {" src/cpp/ | wc -l  > audit.txt
grep -r "try:" src/python/ | wc -l >> audit.txt
grep -r "throw" src/cpp/ | wc -l >> audit.txt

# Document findings
- Files with try/catch: [list]
- Files with throw: [list]
- Files needing updates: [list]
```

**Deliverable:** Complete audit showing where error handling exists and where it's needed

---

## Phase 2: Structured Logging (Week 5-6)

**Goal:** Replace ad-hoc console output with structured logging

### Task 2.1: Implement C++ Logger
**Time:** 3 hours

**Create:** `src/cpp/utils/logger.h`

```cpp
#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <fstream>
#include <iostream>
#include <mutex>
#include <ctime>

namespace igsoa {
namespace utils {

class Logger {
public:
    enum Level {
        DEBUG = 0,
        INFO = 1,
        WARNING = 2,
        ERROR = 3,
        FATAL = 4
    };

    static Logger& getInstance() {
        static Logger instance;
        return instance;
    }

    void setLogFile(const std::string& filename) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (log_file_.is_open()) {
            log_file_.close();
        }
        log_file_.open(filename, std::ios::app);
    }

    void setLevel(Level level) {
        min_level_ = level;
    }

    void log(Level level, const std::string& message,
             const std::string& file = "", int line = -1) {
        if (level < min_level_) return;

        std::lock_guard<std::mutex> lock(mutex_);

        std::string timestamp = getCurrentTime();
        std::string level_str = getLevelString(level);

        std::ostream& out = (log_file_.is_open()) ? log_file_ : std::cout;

        out << timestamp << " [" << level_str << "] ";
        if (!file.empty()) {
            out << file << ":" << line << " - ";
        }
        out << message << std::endl;
    }

private:
    Logger() : min_level_(INFO) {}
    ~Logger() {
        if (log_file_.is_open()) {
            log_file_.close();
        }
    }

    std::string getCurrentTime() {
        std::time_t now = std::time(nullptr);
        char buf[100];
        std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        return std::string(buf);
    }

    std::string getLevelString(Level level) {
        switch(level) {
            case DEBUG: return "DEBUG";
            case INFO: return "INFO";
            case WARNING: return "WARN";
            case ERROR: return "ERROR";
            case FATAL: return "FATAL";
            default: return "UNKNOWN";
        }
    }

    Level min_level_;
    std::ofstream log_file_;
    std::mutex mutex_;
};

// Convenience macros
#define LOG_DEBUG(msg) Logger::getInstance().log(Logger::DEBUG, msg, __FILE__, __LINE__)
#define LOG_INFO(msg) Logger::getInstance().log(Logger::INFO, msg)
#define LOG_WARN(msg) Logger::getInstance().log(Logger::WARNING, msg, __FILE__, __LINE__)
#define LOG_ERROR(msg) Logger::getInstance().log(Logger::ERROR, msg, __FILE__, __LINE__)
#define LOG_FATAL(msg) Logger::getInstance().log(Logger::FATAL, msg, __FILE__, __LINE__)

} // namespace utils
} // namespace igsoa

#endif // LOGGER_H
```

### Task 2.2: Integrate Logger in GW Engine
**Time:** 2 hours

**Update files:**
- `echo_generator.cpp` - Replace `std::cout` with `LOG_INFO`
- `source_manager.cpp` - Use `LOG_INFO` for merger detection
- `fractional_solver.cpp` - Add `LOG_WARN` for convergence issues

**Example:**
```cpp
// Before
std::cout << "EchoGenerator initialized:" << std::endl;
std::cout << "  Primes generated: " << primes_.size() << std::endl;

// After
LOG_INFO("EchoGenerator initialized with " +
         std::to_string(primes_.size()) + " primes");
```

### Task 2.3: Python Logging Setup
**Time:** 1 hour

**Update:** `src/python/bridge_server.py`

```python
import logging

# Configure logging
logging.basicConfig(
    filename='logs/igsoa_python.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('igsoa.bridge')

# Use throughout
try:
    result = process_command(cmd)
except Exception as e:
    logger.error(f"Command failed: {e}", exc_info=True)
    raise
```

---

## Phase 3: GW Engine Enhancements (Week 6)

**Goal:** Make GW engine production-ready

### Task 3.1: File I/O Error Handling
**Time:** 1.5 hours

**Update:** `echo_generator.cpp:345`

```cpp
void EchoGenerator::exportEchoSchedule(const std::string& filename) const {
    try {
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Failed to open file for writing: " + filename);
        }

        file << std::scientific << std::setprecision(12);
        file << "echo_number,time,dt_from_previous,amplitude,frequency,prime_gap,prime_index\n";

        for (size_t i = 0; i < echo_schedule_.size(); i++) {
            const auto& echo = echo_schedule_[i];
            double dt_from_prev = (i == 0) ?
                (echo.time - config_.merger_time) :
                (echo.time - echo_schedule_[i-1].time);

            file << echo.echo_number << ","
                 << echo.time << ","
                 << dt_from_prev << ","
                 << echo.amplitude << ","
                 << echo.frequency << ","
                 << echo.prime_gap << ","
                 << echo.prime_index << "\n";

            if (!file.good()) {
                throw std::runtime_error("Write error occurred while exporting echoes");
            }
        }

        file.close();
        LOG_INFO("Echo schedule exported to: " + filename);

    } catch (const std::exception& e) {
        LOG_ERROR("Failed to export echo schedule: " + std::string(e.what()));
        throw;
    }
}
```

### Task 3.2: Configuration Validation
**Time:** 2 hours

**Create:** `src/cpp/igsoa_gw_engine/utils/config_validator.h`

```cpp
namespace igsoa { namespace gw { namespace utils {

class ConfigValidator {
public:
    static void validateEchoConfig(const EchoConfig& config) {
        if (config.fundamental_timescale <= 0) {
            throw std::invalid_argument(
                "fundamental_timescale must be positive, got: " +
                std::to_string(config.fundamental_timescale)
            );
        }

        if (config.max_primes < 1) {
            throw std::invalid_argument(
                "max_primes must be at least 1, got: " +
                std::to_string(config.max_primes)
            );
        }

        if (config.echo_amplitude_decay <= 0) {
            throw std::invalid_argument(
                "echo_amplitude_decay must be positive, got: " +
                std::to_string(config.echo_amplitude_decay)
            );
        }

        LOG_DEBUG("EchoConfig validation passed");
    }

    static void validateFieldConfig(const SymmetryFieldConfig& config) {
        if (config.nx <= 0 || config.ny <= 0 || config.nz <= 0) {
            throw std::invalid_argument(
                "Grid dimensions must be positive, got: " +
                std::to_string(config.nx) + "x" +
                std::to_string(config.ny) + "x" +
                std::to_string(config.nz)
            );
        }

        if (config.dx <= 0 || config.dy <= 0 || config.dz <= 0) {
            throw std::invalid_argument("Grid spacing must be positive");
        }

        if (config.dt <= 0) {
            throw std::invalid_argument("Timestep must be positive");
        }

        LOG_DEBUG("FieldConfig validation passed");
    }
};

}}} // namespace igsoa::gw::utils
```

### Task 3.3: Memory Allocation Guards
**Time:** 1.5 hours

**Update:** `symmetry_field.cpp` constructor

```cpp
SymmetryField::SymmetryField(const SymmetryFieldConfig& config)
    : config_(config)
{
    ConfigValidator::validateFieldConfig(config);

    int total_points = config_.nx * config_.ny * config_.nz;

    LOG_INFO("Allocating field with " + std::to_string(total_points) + " points");

    try {
        delta_phi_.resize(total_points);
        delta_phi_prev_.resize(total_points);
        alpha_field_.resize(total_points);

        LOG_INFO("Field allocation successful (" +
                 std::to_string(total_points * sizeof(std::complex<double>) * 3 / 1024.0 / 1024.0) +
                 " MB)");

    } catch (const std::bad_alloc& e) {
        LOG_FATAL("Failed to allocate memory for " + std::to_string(total_points) + " points");
        throw std::runtime_error(
            "Memory allocation failed for field of size " +
            std::to_string(total_points) + " points (" +
            std::to_string(total_points * sizeof(std::complex<double>) * 3 / 1024.0 / 1024.0) +
            " MB required)"
        );
    }
}
```

---

## Phase 4: Error Testing (Week 6-7)

**Goal:** Verify error handling works correctly

### Task 4.1: Create Negative Test Suite
**Time:** 3 hours

**Create:** `tests/test_error_handling.cpp`

```cpp
#include "gtest/gtest.h"
#include "../src/cpp/igsoa_gw_engine/core/echo_generator.h"
#include "../src/cpp/igsoa_gw_engine/core/symmetry_field.h"

TEST(ErrorHandlingTest, EchoGenerator_InvalidTimescale) {
    EchoConfig config;
    config.fundamental_timescale = -0.001;  // Invalid

    EXPECT_THROW({
        EchoGenerator gen(config);
    }, std::invalid_argument);
}

TEST(ErrorHandlingTest, EchoGenerator_ZeroPrimes) {
    EchoConfig config;
    config.max_primes = 0;  // Invalid

    EXPECT_THROW({
        EchoGenerator gen(config);
    }, std::invalid_argument);
}

TEST(ErrorHandlingTest, SymmetryField_NegativeGridSize) {
    SymmetryFieldConfig config;
    config.nx = -10;  // Invalid

    EXPECT_THROW({
        SymmetryField field(config);
    }, std::invalid_argument);
}

TEST(ErrorHandlingTest, SymmetryField_ZeroTimestep) {
    SymmetryFieldConfig config;
    config.dt = 0.0;  // Invalid

    EXPECT_THROW({
        SymmetryField field(config);
    }, std::invalid_argument);
}

TEST(ErrorHandlingTest, EchoGenerator_OutOfBoundsAccess) {
    EchoConfig config;
    EchoGenerator gen(config);

    EXPECT_EQ(gen.getPrime(-1), -1);  // Negative index
    EXPECT_EQ(gen.getPrime(1000000), -1);  // Too large
}

TEST(ErrorHandlingTest, FileExport_InvalidPath) {
    EchoConfig config;
    EchoGenerator gen(config);

    EXPECT_THROW({
        gen.exportEchoSchedule("/invalid/path/file.csv");
    }, std::runtime_error);
}
```

**Add to CMakeLists.txt:**
```cmake
add_executable(test_error_handling tests/test_error_handling.cpp)
target_link_libraries(test_error_handling PRIVATE igsoa_gw_core gtest gtest_main)
```

### Task 4.2: Test Error Messages
**Time:** 1 hour

**Create:** `tests/test_error_messages.cpp`

```cpp
TEST(ErrorMessagesTest, MessagesAreDescriptive) {
    EchoConfig config;
    config.fundamental_timescale = -1.0;

    try {
        EchoGenerator gen(config);
        FAIL() << "Expected exception";
    } catch (const std::invalid_argument& e) {
        std::string msg(e.what());
        EXPECT_TRUE(msg.find("fundamental_timescale") != std::string::npos)
            << "Error message should mention parameter name";
        EXPECT_TRUE(msg.find("positive") != std::string::npos)
            << "Error message should explain what's wrong";
        EXPECT_TRUE(msg.find("-1") != std::string::npos)
            << "Error message should show actual value";
    }
}
```

---

## Phase 5: Recovery Mechanisms (Week 7+)

**Goal:** Add graceful degradation and retry logic

### Task 5.1: Retry Logic for File I/O
**Time:** 2 hours

```cpp
template<typename Func>
void retryOperation(Func operation, int max_attempts = 3, int delay_ms = 100) {
    for (int attempt = 1; attempt <= max_attempts; ++attempt) {
        try {
            operation();
            return;  // Success
        } catch (const std::exception& e) {
            if (attempt == max_attempts) {
                LOG_ERROR("Operation failed after " + std::to_string(max_attempts) +
                         " attempts: " + std::string(e.what()));
                throw;
            }
            LOG_WARN("Attempt " + std::to_string(attempt) + " failed, retrying...");
            std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
        }
    }
}

// Usage
retryOperation([&]() {
    exportWaveformCSV(filename, time_array, h_plus_array, h_cross_array, amplitude_array);
});
```

### Task 5.2: Fallback Configurations
**Time:** 2 hours

```cpp
EchoConfig getDefaultEchoConfig() {
    EchoConfig config;
    config.fundamental_timescale = 0.001;
    config.max_primes = 30;
    config.echo_amplitude_base = 0.1;
    config.echo_amplitude_decay = 10.0;
    config.echo_frequency_shift = 10.0;
    config.echo_gaussian_width = 10000.0;
    return config;
}

EchoConfig loadConfigWithFallback(const std::string& filename) {
    try {
        return loadEchoConfig(filename);
    } catch (const std::exception& e) {
        LOG_WARN("Failed to load config from " + filename +
                ", using defaults: " + std::string(e.what()));
        return getDefaultEchoConfig();
    }
}
```

---

## Implementation Checklist

### Phase 1: Documentation (2-4 hours)
- [ ] Create ERROR_HANDLING_GUIDE.md
- [ ] Audit current error handling
- [ ] Document patterns for each language
- [ ] Share with team for review

### Phase 2: Logging (4-6 hours)
- [ ] Implement C++ Logger class
- [ ] Integrate logger in GW engine
- [ ] Setup Python logging
- [ ] Test log file creation
- [ ] Verify log rotation

### Phase 3: GW Enhancements (5-8 hours)
- [ ] Add file I/O error handling
- [ ] Implement config validation
- [ ] Add memory allocation guards
- [ ] Test all error paths
- [ ] Update documentation

### Phase 4: Testing (4-6 hours)
- [ ] Create negative test suite
- [ ] Test error messages
- [ ] Add to CI/CD pipeline
- [ ] Verify 100% coverage of error paths

### Phase 5: Recovery (6-10 hours)
- [ ] Implement retry logic
- [ ] Add fallback configs
- [ ] Test recovery scenarios
- [ ] Document recovery behavior

---

## Success Metrics

**Before:**
- Error handling: Ad-hoc, inconsistent
- Logging: Console only
- Error tests: None
- Documentation: None

**After:**
- Error handling: Standardized patterns
- Logging: Structured, file-based
- Error tests: 15+ negative cases
- Documentation: Complete guide

**Timeline:** 3-4 weeks
**Effort:** 25-33 hours
**Risk:** Low (incremental improvements)
**Benefit:** High (production readiness)

---

## Quick Win: Immediate Actions (< 2 hours)

If time is limited, start with these high-impact, low-effort tasks:

1. **Add Logger to GW Engine** (30 min)
   - Just the header file
   - Replace 5-10 std::cout calls
   - Immediate improvement in debugging

2. **Validate Echo Config** (30 min)
   - Add basic checks in constructor
   - Prevent common errors

3. **File I/O Try/Catch** (30 min)
   - Wrap exportEchoSchedule
   - Better error messages

4. **Document Current State** (30 min)
   - List what exists
   - Note what's missing
   - Share with team

**Total: 2 hours for 60% of the benefit**

---

**Plan Status:** Ready for implementation
**Priority:** Medium
**Recommendation:** Start with Quick Wins, then proceed through phases as time permits

---

*November 10, 2025*
*IGSOA-SIM Error Handling Improvement Plan*
