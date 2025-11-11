# Error Handling Guide

**IGSOA-SIM Project**
**Version:** 1.0
**Date:** November 11, 2025
**Status:** Official Guidelines

---

## Table of Contents

1. [Overview](#overview)
2. [General Principles](#general-principles)
3. [C++ Error Handling](#cpp-error-handling)
4. [Python Error Handling](#python-error-handling)
5. [JavaScript Error Handling](#javascript-error-handling)
6. [Error Messages](#error-messages)
7. [Logging Guidelines](#logging-guidelines)
8. [Testing Error Paths](#testing-error-paths)
9. [Examples](#examples)

---

## Overview

This guide establishes error handling standards for the IGSOA-SIM codebase. Consistent error handling makes the code more maintainable, debuggable, and production-ready.

**Goals:**
- Catch and handle errors at appropriate levels
- Provide informative error messages with context
- Enable debugging through structured logging
- Fail gracefully when possible
- Make error paths testable

**Scope:**
- C++ core engine and simulation code
- Python analysis scripts and servers
- JavaScript backend and frontend code

---

## General Principles

### 1. Fail Fast, Fail Informatively

**DO:**
```cpp
if (num_nodes <= 0) {
    throw std::invalid_argument(
        "num_nodes must be positive, got: " + std::to_string(num_nodes)
    );
}
```

**DON'T:**
```cpp
if (num_nodes <= 0) {
    num_nodes = 1;  // Silent correction - user doesn't know there's a problem
}
```

### 2. Provide Context in Errors

**DO:**
```cpp
throw std::runtime_error(
    "Failed to allocate field memory for " +
    std::to_string(nx) + "×" + std::to_string(ny) + " grid (" +
    std::to_string(required_mb) + " MB required, " +
    std::to_string(available_mb) + " MB available)"
);
```

**DON'T:**
```cpp
throw std::runtime_error("Memory allocation failed");
```

### 3. Choose the Right Error Mechanism

| Situation | Mechanism | Rationale |
|-----------|-----------|-----------|
| Invalid user input | Exception | Exceptional condition, should stop execution |
| Bounds check failed | Exception | Programming error or data corruption |
| File I/O failed | Exception | Cannot continue without the data |
| Resource exhausted | Exception | Cannot proceed, must fail gracefully |
| Optional feature unavailable | Return code | Not an error, just a limitation |
| Query returns no results | Return empty/null | Expected possibility in normal flow |

### 4. Error Propagation

**Let exceptions propagate unless you can handle them meaningfully:**

```cpp
// Good: Catch and add context, then re-throw
try {
    loadConfiguration(filename);
} catch (const std::exception& e) {
    LOG_ERROR("Failed to load config from " + filename + ": " + e.what());
    throw;  // Re-throw with logged context
}

// Good: Catch and handle fully
try {
    saveCheckpoint(filename);
} catch (const std::exception& e) {
    LOG_WARNING("Checkpoint save failed, continuing: " + std::string(e.what()));
    // Don't re-throw - this is optional functionality
}

// Bad: Catch and ignore
try {
    importantOperation();
} catch (...) {
    // Silently ignoring - caller has no idea it failed
}
```

---

## C++ Error Handling

### When to Use Exceptions vs Return Codes

#### Use Exceptions For:

1. **Invalid input that violates preconditions**
   ```cpp
   void setAlpha(double alpha) {
       if (alpha <= 0 || alpha > 2.0) {
           throw std::invalid_argument(
               "Alpha must be in (0, 2.0], got: " + std::to_string(alpha)
           );
       }
       alpha_ = alpha;
   }
   ```

2. **Resource allocation failures**
   ```cpp
   void allocateField(size_t size) {
       try {
           field_ = std::vector<std::complex<double>>(size);
       } catch (const std::bad_alloc& e) {
           throw std::runtime_error(
               "Failed to allocate " + std::to_string(size * 16 / 1024 / 1024) +
               " MB for field"
           );
       }
   }
   ```

3. **File I/O errors**
   ```cpp
   void exportData(const std::string& filename) {
       std::ofstream file(filename);
       if (!file.is_open()) {
           throw std::runtime_error("Failed to open file: " + filename);
       }

       file << data;

       if (!file.good()) {
           throw std::runtime_error(
               "Write error while exporting to: " + filename
           );
       }
   }
   ```

4. **Invariant violations**
   ```cpp
   void advance(double dt) {
       if (dt <= 0) {
           throw std::invalid_argument("dt must be positive");
       }
       if (dt > 0.5 * dx_) {
           throw std::runtime_error(
               "CFL condition violated: dt=" + std::to_string(dt) +
               " > 0.5*dx=" + std::to_string(0.5 * dx_)
           );
       }
       // ... perform time step
   }
   ```

#### Use Return Codes For:

1. **Expected "not found" scenarios**
   ```cpp
   int getPrimeIndex(int prime) const {
       auto it = std::find(primes_.begin(), primes_.end(), prime);
       if (it == primes_.end()) {
           return -1;  // Not found is an expected possibility
       }
       return std::distance(primes_.begin(), it);
   }
   ```

2. **Optional queries**
   ```cpp
   std::vector<Echo> getActiveEchoes(double t) const {
       std::vector<Echo> active;
       for (const auto& echo : echoes_) {
           if (std::abs(t - echo.time) < echo.width) {
               active.push_back(echo);
           }
       }
       return active;  // Empty vector if none active - not an error
   }
   ```

3. **Status checks**
   ```cpp
   bool isInitialized() const {
       return field_.size() > 0;
   }
   ```

### Exception Types to Use

| Exception Type | When to Use | Example |
|----------------|-------------|---------|
| `std::invalid_argument` | Invalid function parameter | Negative grid size, alpha out of range |
| `std::out_of_range` | Index out of bounds | Array access beyond size |
| `std::runtime_error` | Runtime failure (general) | File I/O error, memory allocation |
| `std::logic_error` | Programming error detected | Called function before initialization |
| `std::bad_alloc` | Memory allocation failed | (Usually caught and wrapped) |

### C++ Exception Handling Pattern

```cpp
// In public API functions (C++ to C++ calls):
ReturnType publicFunction(Args args) {
    // Validate input
    if (!validateInput(args)) {
        throw std::invalid_argument("Invalid input: " + describeError(args));
    }

    // Perform operation (let exceptions propagate)
    try {
        return performOperation(args);
    } catch (const std::exception& e) {
        // Log and re-throw with additional context
        LOG_ERROR("Operation failed: " + std::string(e.what()));
        throw;
    }
}

// In C API functions (C++ to C interface):
extern "C" {
    EngineHandle* create_engine(int num_nodes) {
        try {
            // Validate
            if (num_nodes <= 0) {
                LOG_ERROR("Invalid num_nodes: " + std::to_string(num_nodes));
                return nullptr;
            }

            // Create
            auto engine = new Engine(num_nodes);
            LOG_INFO("Engine created with " + std::to_string(num_nodes) + " nodes");
            return reinterpret_cast<EngineHandle*>(engine);

        } catch (const std::bad_alloc&) {
            LOG_ERROR("Memory allocation failed for " + std::to_string(num_nodes) + " nodes");
            return nullptr;
        } catch (const std::exception& e) {
            LOG_ERROR("Engine creation failed: " + std::string(e.what()));
            return nullptr;
        } catch (...) {
            LOG_ERROR("Unknown error during engine creation");
            return nullptr;
        }
    }
}
```

---

## Python Error Handling

### When to Catch Exceptions

#### Catch Specific Exceptions

**DO:**
```python
try:
    with open(filename, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    logger.error(f"Configuration file not found: {filename}")
    data = get_default_config()
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in {filename}: {e}")
    raise
except PermissionError:
    logger.error(f"Permission denied reading {filename}")
    raise
```

**DON'T:**
```python
try:
    with open(filename, 'r') as f:
        data = json.load(f)
except:  # Catches everything, including KeyboardInterrupt!
    data = {}
```

#### Python Exception Hierarchy

```python
# Use specific exceptions at appropriate levels:

# Built-in exceptions to catch:
FileNotFoundError       # File doesn't exist
PermissionError        # No permission to access
ValueError             # Invalid value for type
TypeError              # Wrong type passed
KeyError               # Dict key doesn't exist
IndexError             # List index out of range
json.JSONDecodeError   # Invalid JSON
OSError                # OS-related errors

# Use for catching groups:
OSError                # Catches FileNotFoundError, PermissionError, etc.
Exception              # Catches most exceptions (but not KeyboardInterrupt)

# NEVER catch these:
BaseException          # Catches system exit, keyboard interrupt
```

### Python Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

def process_data(filename):
    """
    Process data from file.

    Args:
        filename: Path to data file

    Returns:
        Processed data dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If data format is invalid
        RuntimeError: If processing fails
    """
    # Validate input
    if not filename:
        raise ValueError("filename cannot be empty")

    # Read file with specific error handling
    try:
        with open(filename, 'r') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise  # Re-raise - caller needs to know
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {e}")
        raise ValueError(f"Invalid data format in {filename}") from e
    except PermissionError:
        logger.error(f"Permission denied: {filename}")
        raise

    # Process with error handling
    try:
        processed = transform_data(raw_data)
        logger.info(f"Successfully processed {filename}")
        return processed
    except Exception as e:
        logger.error(f"Processing failed for {filename}: {e}")
        raise RuntimeError(f"Failed to process {filename}") from e
```

### Python Logging Setup

```python
import logging
import sys

def setup_logging(log_file='igsoa_sim.log', level=logging.INFO):
    """
    Configure logging for the application.

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler (errors and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[file_handler, console_handler]
    )

# Usage:
setup_logging()
logger = logging.getLogger(__name__)
logger.info("Application started")
```

---

## JavaScript Error Handling

### Synchronous Code

```javascript
function processRequest(data) {
    // Validate input
    if (!data || !data.command) {
        throw new Error('Invalid request: missing command');
    }

    // Process with error handling
    try {
        const result = executeCommand(data.command, data.params);
        return { success: true, result };
    } catch (err) {
        console.error('Command execution failed:', err.message);
        throw new Error(`Command failed: ${err.message}`);
    }
}
```

### Asynchronous Code (Promises)

```javascript
async function fetchData(url) {
    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`Successfully fetched data from ${url}`);
        return data;

    } catch (err) {
        console.error(`Failed to fetch ${url}:`, err.message);
        throw new Error(`Data fetch failed: ${err.message}`);
    }
}
```

### Express Middleware Error Handling

```javascript
const express = require('express');
const app = express();

// Route with error handling
app.post('/api/simulate', async (req, res) => {
    try {
        // Validate request
        if (!req.body.params) {
            return res.status(400).json({
                error: 'Bad Request',
                message: 'Missing simulation parameters'
            });
        }

        // Process request
        const result = await runSimulation(req.body.params);

        res.json({
            success: true,
            result: result
        });

    } catch (err) {
        console.error('Simulation failed:', err.message);
        res.status(500).json({
            error: 'Internal Server Error',
            message: err.message,
            details: process.env.NODE_ENV === 'development' ? err.stack : undefined
        });
    }
});

// Global error handler (last middleware)
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        error: 'Internal Server Error',
        message: 'An unexpected error occurred'
    });
});
```

---

## Error Messages

### Format Guidelines

**Structure:** `[Action failed]: [Specific reason]. [Context]. [Suggested fix]`

**Examples:**

**GOOD:**
```
"Failed to allocate field memory for 256×256×256 grid (256 MB required, 128 MB available).
Reduce grid size or increase available memory."
```

**BAD:**
```
"Memory error"
```

**GOOD:**
```
"CFL condition violated: dt=0.01 exceeds stability limit 0.5*dx=0.005 for current grid spacing.
Reduce dt or increase dx."
```

**BAD:**
```
"Invalid timestep"
```

### Components of a Good Error Message

1. **What failed** - The operation that couldn't complete
2. **Why it failed** - The specific condition that triggered the error
3. **Context** - Values and state that caused the problem
4. **Suggested action** - How to fix it (when possible)

### Error Message Patterns

```cpp
// Parameter validation
"Alpha must be in (0, 2.0], got: {value}"
"Grid dimensions must be positive, got: nx={nx}, ny={ny}, nz={nz}"
"Number of primes must be >= 1, got: {num_primes}"

// Resource errors
"Failed to allocate {size_mb} MB for {resource_name}"
"Failed to open file '{filename}': {system_error}"
"Write failed to '{filename}': {system_error}"

// State errors
"Cannot call evolve() before initialize()"
"Engine not ready: missing configuration"
"Simulation already running, cannot restart"

// Physical constraint violations
"CFL condition violated: dt={dt} > max_dt={max_dt}"
"Energy conservation failed: dE/E = {relative_error} exceeds threshold {threshold}"
"Field divergence: div(phi) = {divergence} exceeds tolerance {tolerance}"
```

---

## Logging Guidelines

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info | "Entering function foo with param=42" |
| **INFO** | Significant events | "Engine initialized with 1024 nodes", "Simulation completed" |
| **WARNING** | Recoverable problems | "Checkpoint save failed, continuing", "Using default config" |
| **ERROR** | Errors that impact functionality | "Failed to load config file", "Memory allocation failed" |
| **FATAL** | Unrecoverable errors | "Critical initialization failed", "Data corruption detected" |

### What to Log

**DO Log:**
- Initialization and shutdown
- Configuration loaded
- Major state transitions
- Errors and exceptions
- Performance metrics (occasionally)
- User actions (API calls)

**DON'T Log:**
- Every function call (too verbose)
- Sensitive data (passwords, keys)
- Inside tight loops (performance impact)
- Redundant information

### Logging Examples

```cpp
// C++ (once Logger class is implemented)
LOG_INFO("EchoGenerator initialized: " + std::to_string(num_primes) + " primes generated");
LOG_WARNING("Merger not detected, using fallback time: " + std::to_string(fallback_time));
LOG_ERROR("Failed to export echo schedule: " + filename);

// Python
logger.info(f"Bridge server started on port {port}")
logger.warning(f"Config file not found, using defaults: {default_config_path}")
logger.error(f"Engine creation failed: {error_msg}")

// JavaScript
console.log(`Server listening on port ${PORT}`);
console.warn(`Request timeout after ${timeout}ms, retrying...`);
console.error(`Database connection failed: ${err.message}`);
```

---

## Testing Error Paths

### Why Test Error Paths?

- Verify error messages are helpful
- Ensure exceptions are thrown correctly
- Check error handling doesn't leak resources
- Validate recovery mechanisms work

### C++ Error Path Testing

```cpp
TEST(EchoGeneratorTest, InvalidTimescale) {
    EchoConfig config;
    config.fundamental_timescale = -0.001;  // Invalid

    EXPECT_THROW({
        EchoGenerator gen(config);
    }, std::invalid_argument);
}

TEST(EchoGeneratorTest, InvalidTimescaleMessage) {
    EchoConfig config;
    config.fundamental_timescale = 0;  // Invalid

    try {
        EchoGenerator gen(config);
        FAIL() << "Expected std::invalid_argument";
    } catch (const std::invalid_argument& e) {
        std::string msg = e.what();
        EXPECT_TRUE(msg.find("timescale") != std::string::npos);
        EXPECT_TRUE(msg.find("positive") != std::string::npos);
    }
}

TEST(FileExportTest, WriteError) {
    EchoGenerator gen(valid_config);
    std::string read_only_path = "/read_only_dir/output.csv";

    EXPECT_THROW({
        gen.exportEchoSchedule(read_only_path);
    }, std::runtime_error);
}
```

### Python Error Path Testing

```python
import pytest

def test_invalid_filename():
    with pytest.raises(ValueError, match="filename cannot be empty"):
        process_data("")

def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        process_data("nonexistent_file.json")

def test_invalid_json():
    with pytest.raises(ValueError, match="Invalid data format"):
        process_data("invalid.json")  # Contains malformed JSON
```

### JavaScript Error Path Testing

```javascript
describe('Error Handling', () => {
    it('should throw error for missing command', () => {
        expect(() => {
            processRequest({});
        }).toThrow('Invalid request: missing command');
    });

    it('should return 400 for invalid params', async () => {
        const res = await request(app)
            .post('/api/simulate')
            .send({});

        expect(res.status).toBe(400);
        expect(res.body.error).toBe('Bad Request');
    });
});
```

---

## Examples

### Complete Example: C++ Module with Error Handling

```cpp
// echo_generator.h
class EchoGenerator {
public:
    explicit EchoGenerator(const EchoConfig& config);

    void setMergerTime(double t);
    std::complex<double> computeEchoSource(
        double t,
        const std::array<double, 3>& position,
        const std::array<double, 3>& merger_center
    ) const;

    void exportEchoSchedule(const std::string& filename) const;

private:
    void validateConfig(const EchoConfig& config);
    void generatePrimes();

    EchoConfig config_;
    std::vector<int> primes_;
    std::vector<Echo> echoes_;
    bool merger_time_set_;
};

// echo_generator.cpp
EchoGenerator::EchoGenerator(const EchoConfig& config)
    : config_(config), merger_time_set_(false) {

    // Validate configuration
    validateConfig(config);

    // Generate primes
    try {
        generatePrimes();
    } catch (const std::exception& e) {
        throw std::runtime_error(
            "Failed to initialize EchoGenerator: " + std::string(e.what())
        );
    }

    LOG_INFO("EchoGenerator initialized: " +
             std::to_string(primes_.size()) + " primes generated");
}

void EchoGenerator::validateConfig(const EchoConfig& config) {
    if (config.fundamental_timescale <= 0) {
        throw std::invalid_argument(
            "fundamental_timescale must be positive, got: " +
            std::to_string(config.fundamental_timescale)
        );
    }

    if (config.max_primes < 1) {
        throw std::invalid_argument(
            "max_primes must be >= 1, got: " +
            std::to_string(config.max_primes)
        );
    }

    if (config.echo_gaussian_width <= 0) {
        throw std::invalid_argument(
            "echo_gaussian_width must be positive, got: " +
            std::to_string(config.echo_gaussian_width)
        );
    }
}

void EchoGenerator::exportEchoSchedule(const std::string& filename) const {
    if (filename.empty()) {
        throw std::invalid_argument("filename cannot be empty");
    }

    if (!merger_time_set_) {
        throw std::logic_error(
            "Cannot export echo schedule: merger time not set. "
            "Call setMergerTime() first."
        );
    }

    try {
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw std::runtime_error("Failed to open file: " + filename);
        }

        // Write header
        file << "echo_number,time,dt_from_previous,amplitude,frequency,prime_gap\n";

        // Write data
        for (const auto& echo : echoes_) {
            file << echo.number << ","
                 << echo.time << ","
                 << echo.dt_from_previous << ","
                 << echo.amplitude << ","
                 << echo.frequency << ","
                 << echo.prime_gap << "\n";
        }

        if (!file.good()) {
            throw std::runtime_error(
                "Write error occurred while exporting to: " + filename
            );
        }

        LOG_INFO("Exported echo schedule to: " + filename);

    } catch (const std::exception& e) {
        LOG_ERROR("Failed to export echo schedule: " + std::string(e.what()));
        throw;
    }
}
```

### Complete Example: Python Module with Error Handling

```python
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class SimulationConfig:
    """Configuration loader with comprehensive error handling."""

    def __init__(self, config_path):
        """
        Load simulation configuration.

        Args:
            config_path: Path to JSON configuration file

        Raises:
            ValueError: If config_path is invalid
            FileNotFoundError: If config file doesn't exist
            RuntimeError: If configuration is invalid
        """
        if not config_path:
            raise ValueError("config_path cannot be empty")

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

        logger.info(f"Configuration loaded from {config_path}")

    def _load_config(self):
        """Load JSON configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config

        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_path}: {e}")
            raise ValueError(
                f"Invalid JSON format in {self.config_path}: {e}"
            ) from e

        except PermissionError:
            logger.error(f"Permission denied reading {self.config_path}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise RuntimeError(
                f"Failed to load configuration: {e}"
            ) from e

    def _validate_config(self):
        """Validate configuration values."""
        required_keys = ['num_nodes', 'alpha', 'grid_size']

        for key in required_keys:
            if key not in self.config:
                raise RuntimeError(
                    f"Missing required configuration key: {key}. "
                    f"Required keys: {required_keys}"
                )

        # Validate num_nodes
        num_nodes = self.config['num_nodes']
        if not isinstance(num_nodes, int) or num_nodes <= 0:
            raise ValueError(
                f"num_nodes must be a positive integer, got: {num_nodes}"
            )

        # Validate alpha
        alpha = self.config['alpha']
        if not isinstance(alpha, (int, float)) or alpha <= 0 or alpha > 2.0:
            raise ValueError(
                f"alpha must be in (0, 2.0], got: {alpha}"
            )

        logger.debug(f"Configuration validated: {self.config}")
```

---

## Summary

### Key Takeaways

1. **Use exceptions for exceptional conditions** - Invalid input, resource failures, invariant violations
2. **Use return codes for expected possibilities** - Not found, empty results, optional features
3. **Provide context in error messages** - What, why, values, suggested fix
4. **Log at appropriate levels** - DEBUG for diagnostics, INFO for events, ERROR for failures
5. **Test error paths** - Verify exceptions are thrown, messages are helpful
6. **Fail fast and informatively** - Don't hide errors, make them visible and debuggable

### Quick Reference

| Language | Exception | Return Code | Logging |
|----------|-----------|-------------|---------|
| **C++** | `throw std::invalid_argument()` | `return -1;` | `LOG_ERROR()` (once implemented) |
| **Python** | `raise ValueError()` | `return None` | `logger.error()` |
| **JavaScript** | `throw new Error()` | `return null` | `console.error()` |

---

**Document Status:** Official Guidelines v1.0
**Next Review:** After Phase 2 implementation
**Feedback:** Open issue or discuss with team

---

*November 11, 2025*
*IGSOA-SIM Error Handling Standards*
