# Headless JSON CLI Architecture for DASE Engine
## AI-Augmented Analog Computation Interface

**Date:** October 24, 2025
**Purpose:** Command-line JSON interface for AI integration with DASE engines
**Design:** Headless, stdin/stdout JSON, scriptable, AI-friendly

---

## Executive Summary

A lightweight command-line interface that:
- ✅ Accepts JSON commands via stdin
- ✅ Returns JSON responses via stdout
- ✅ Runs headless (no GUI, no interactive prompts)
- ✅ Supports both Phase 4B (real) and IGSOA Complex engines
- ✅ Perfect for AI agents, scripting, and automation

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  AI Agent / Script / External Process   │
│  (Claude, GPT, Custom AI)               │
└─────────────┬───────────────────────────┘
              │
              │ JSON Commands (stdin)
              ▼
┌─────────────────────────────────────────┐
│  dase_cli.exe                           │
│  ┌──────────────────────────────────┐   │
│  │  JSON Parser                     │   │
│  │  Command Router                  │   │
│  │  Engine Manager                  │   │
│  │  ┌────────────┬──────────────┐   │   │
│  │  │ Phase 4B   │ IGSOA Complex│   │   │
│  │  │ (Real)     │ (Complex)    │   │   │
│  │  └────────────┴──────────────┘   │   │
│  │  Response Formatter               │   │
│  └──────────────────────────────────┘   │
└─────────────┬───────────────────────────┘
              │
              │ JSON Responses (stdout)
              ▼
┌─────────────────────────────────────────┐
│  AI Agent / Script                      │
│  (Parses results, makes decisions)      │
└─────────────────────────────────────────┘
```

---

## JSON Command Format

### Standard Command Structure

```json
{
  "command": "command_name",
  "engine_type": "phase4b" | "igsoa_complex",
  "params": {
    // Command-specific parameters
  },
  "request_id": "optional_correlation_id"
}
```

### Standard Response Structure

```json
{
  "status": "success" | "error",
  "command": "command_name",
  "request_id": "optional_correlation_id",
  "result": {
    // Command-specific results
  },
  "error": "error_message (if status=error)",
  "execution_time_ms": 123.45,
  "timestamp": "2025-10-24T14:30:00Z"
}
```

---

## Supported Commands

### 1. Engine Lifecycle Commands

#### `create_engine`

**Request:**
```json
{
  "command": "create_engine",
  "engine_type": "phase4b",
  "params": {
    "num_nodes": 1024,
    "R_c": 1e-34
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "create_engine",
  "result": {
    "engine_id": "engine_001",
    "engine_type": "phase4b",
    "num_nodes": 1024,
    "memory_allocated_mb": 8.2
  },
  "execution_time_ms": 5.2
}
```

**Related Commands for 2D Engines:**

- `set_igsoa_state` accepts `gaussian_2d`, `circular_gaussian`, `plane_wave_2d`,
  `uniform`, `random`, and `reset` profiles.  Parameters mirror the structure
  of `IGSOAStateInit2D` (center coordinates, σ values, blend/add/overwrite
  modes).
- `get_state` returns flattened arrays plus a `dimensions` object with
  `N_x/N_y` for 2D lattices.
- `get_center_of_mass` reports drift diagnostics for 2D simulations.

<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
**Related Commands for 3D Engines:**

- `set_igsoa_state` accepts `gaussian_3d`, `spherical_gaussian`,
  `plane_wave_3d`, `uniform`, `random_3d`, and `reset` presets provided by
  `IGSOAStateInit3D`.
- `get_state` returns flattened arrays plus a `dimensions` object that now
  carries `N_x/N_y/N_z` metadata.
- `get_center_of_mass` emits `(x_cm, y_cm, z_cm)` coordinates for 3D lattices.

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
**2D IGSOA Example:**

```json
{
  "command": "create_engine",
  "params": {
    "engine_type": "igsoa_complex_2d",
    "N_x": 128,
    "N_y": 128,
    "R_c": 1.0,
    "kappa": 1.0,
    "gamma": 0.1,
    "dt": 0.01
  }
}
```

```json
{
  "status": "success",
  "command": "create_engine",
  "result": {
    "engine_id": "engine_002",
    "engine_type": "igsoa_complex_2d",
    "num_nodes": 16384,
    "R_c": 1.0,
    "kappa": 1.0,
    "gamma": 0.1,
    "dt": 0.01,
    "N_x": 128,
    "N_y": 128
  },
  "execution_time_ms": 7.9
}
```

<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
**3D IGSOA Example:**

```json
{
  "command": "create_engine",
  "params": {
    "engine_type": "igsoa_complex_3d",
    "N_x": 48,
    "N_y": 48,
    "N_z": 48,
    "R_c": 2.5,
    "kappa": 1.0,
    "gamma": 0.1,
    "dt": 0.01
  }
}
```

```json
{
  "status": "success",
  "command": "create_engine",
  "result": {
    "engine_id": "engine_003",
    "engine_type": "igsoa_complex_3d",
    "num_nodes": 110592,
    "R_c": 2.5,
    "kappa": 1.0,
    "gamma": 0.1,
    "dt": 0.01,
    "N_x": 48,
    "N_y": 48,
    "N_z": 48
  },
  "execution_time_ms": 11.4
}
```

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
---

#### `destroy_engine`

**Request:**
```json
{
  "command": "destroy_engine",
  "params": {
    "engine_id": "engine_001"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "destroy_engine",
  "result": {
    "engine_id": "engine_001",
    "destroyed": true
  },
  "execution_time_ms": 1.1
}
```

---

### 2. State Initialization Commands

#### `set_node_state` (Phase 4B - Real)

**Request:**
```json
{
  "command": "set_node_state",
  "params": {
    "engine_id": "engine_001",
    "node_index": 0,
    "value": 1.5
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "set_node_state",
  "result": {
    "node_index": 0,
    "value": 1.5,
    "updated": true
  },
  "execution_time_ms": 0.01
}
```

---

#### `set_node_psi` (IGSOA Complex - Complex)

**Request:**
```json
{
  "command": "set_node_psi",
  "params": {
    "engine_id": "engine_002",
    "node_index": 0,
    "real": 0.707,
    "imag": 0.707
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "set_node_psi",
  "result": {
    "node_index": 0,
    "psi": {
      "real": 0.707,
      "imag": 0.707,
      "magnitude": 1.0,
      "phase_rad": 0.785
    },
    "updated": true
  },
  "execution_time_ms": 0.01
}
```

---

#### `set_bulk_state` (Set multiple nodes at once)

**Request:**
```json
{
  "command": "set_bulk_state",
  "params": {
    "engine_id": "engine_001",
    "nodes": [
      {"index": 0, "value": 1.0},
      {"index": 1, "value": 2.0},
      {"index": 2, "value": 3.0}
    ]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "set_bulk_state",
  "result": {
    "nodes_updated": 3,
    "failed": []
  },
  "execution_time_ms": 0.5
}
```

---

### 3. Execution Commands

#### `run_mission`

**Request:**
```json
{
  "command": "run_mission",
  "params": {
    "engine_id": "engine_001",
    "num_steps": 10000,
    "iterations_per_node": 30,
    "return_states": true,
    "node_indices": [0, 1, 2]
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "run_mission",
  "result": {
    "steps_completed": 10000,
    "total_operations": 307200000,
    "final_states": [
      {"index": 0, "value": 0.543},
      {"index": 1, "value": 0.721},
      {"index": 2, "value": 0.892}
    ]
  },
  "execution_time_ms": 27.6
}
```

---

#### `run_benchmark`

**Request:**
```json
{
  "command": "run_benchmark",
  "params": {
    "engine_id": "engine_001",
    "benchmark_type": "quick" | "endurance",
    "num_steps": 54750
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "run_benchmark",
  "result": {
    "benchmark_type": "quick",
    "duration_seconds": 0.151,
    "total_operations": 168192000,
    "ns_per_op": 2.76,
    "ops_per_sec": 362000000,
    "speedup_factor": 1146.0,
    "performance_rating": "excellent"
  },
  "execution_time_ms": 151.3
}
```

---

### 4. Query Commands

#### `get_node_state`

**Request:**
```json
{
  "command": "get_node_state",
  "params": {
    "engine_id": "engine_001",
    "node_index": 0
  }
}
```

**Response (Phase 4B):**
```json
{
  "status": "success",
  "command": "get_node_state",
  "result": {
    "node_index": 0,
    "value": 0.543
  },
  "execution_time_ms": 0.01
}
```

**Response (IGSOA Complex):**
```json
{
  "status": "success",
  "command": "get_node_state",
  "result": {
    "node_index": 0,
    "psi": {
      "real": 0.707,
      "imag": 0.707,
      "magnitude": 1.0,
      "phase_rad": 0.785
    },
    "phi": 0.5,
    "F": 1.0,
    "entropy_rate": 0.001,
    "T_IGS": 1.0
  },
  "execution_time_ms": 0.01
}
```

---

#### `get_metrics`

**Request:**
```json
{
  "command": "get_metrics",
  "params": {
    "engine_id": "engine_001"
  }
}
```

**Response (Phase 4B):**
```json
{
  "status": "success",
  "command": "get_metrics",
  "result": {
    "engine_type": "phase4b",
    "num_nodes": 1024,
    "total_operations": 168192000,
    "ns_per_op": 2.76,
    "ops_per_sec": 362000000,
    "avx2_operations": 29710214265,
    "avx2_percentage": 17.66
  },
  "execution_time_ms": 0.5
}
```

**Response (IGSOA Complex):**
```json
{
  "status": "success",
  "command": "get_metrics",
  "result": {
    "engine_type": "igsoa_complex",
    "num_nodes": 1024,
    "avg_entropy_rate": 0.0012,
    "total_F": 1024.5,
    "avg_T_IGS": 1.0005,
    "max_grad_F": 0.045,
    "global_R_c": 1e-34
  },
  "execution_time_ms": 1.2
}
```

---

#### `get_all_states` (Bulk read)

**Request:**
```json
{
  "command": "get_all_states",
  "params": {
    "engine_id": "engine_001",
    "format": "array" | "sparse",
    "precision": 6
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "get_all_states",
  "result": {
    "num_nodes": 1024,
    "format": "array",
    "states": [0.543, 0.721, 0.892, ...]
  },
  "execution_time_ms": 5.0
}
```

---

### 5. Batch Commands

#### `batch`

**Request:**
```json
{
  "command": "batch",
  "params": {
    "commands": [
      {
        "command": "create_engine",
        "engine_type": "phase4b",
        "params": {"num_nodes": 1024}
      },
      {
        "command": "set_node_state",
        "params": {"engine_id": "$prev.result.engine_id", "node_index": 0, "value": 1.5}
      },
      {
        "command": "run_mission",
        "params": {"engine_id": "$prev.result.engine_id", "num_steps": 1000}
      }
    ],
    "stop_on_error": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "command": "batch",
  "result": {
    "total_commands": 3,
    "successful": 3,
    "failed": 0,
    "results": [
      {"status": "success", "command": "create_engine", ...},
      {"status": "success", "command": "set_node_state", ...},
      {"status": "success", "command": "run_mission", ...}
    ]
  },
  "execution_time_ms": 35.2
}
```

---

### 6. System Commands

#### `list_engines`

**Request:**
```json
{
  "command": "list_engines"
}
```

**Response:**
```json
{
  "status": "success",
  "command": "list_engines",
  "result": {
    "engines": [
      {
        "engine_id": "engine_001",
        "engine_type": "phase4b",
        "num_nodes": 1024,
        "created_at": "2025-10-24T14:30:00Z",
        "memory_mb": 8.2
      },
      {
        "engine_id": "engine_002",
        "engine_type": "igsoa_complex",
        "num_nodes": 512,
        "created_at": "2025-10-24T14:31:00Z",
        "memory_mb": 16.4
      }
    ],
    "total": 2
  },
  "execution_time_ms": 0.1
}
```

---

#### `get_capabilities`

**Request:**
```json
{
  "command": "get_capabilities"
}
```

**Response:**
```json
{
  "status": "success",
  "command": "get_capabilities",
  "result": {
    "version": "1.0.0",
    "engines": ["phase4b", "igsoa_complex"],
    "cpu_features": {
      "avx2": true,
      "avx512": false,
      "fma": true
    },
    "max_nodes": 1048576,
    "available_memory_gb": 24.5,
    "threads": 12
  },
  "execution_time_ms": 0.5
}
```

---

## CLI Usage Examples

### Basic Usage

```bash
# Single command
echo '{"command":"get_capabilities"}' | dase_cli.exe

# From file
dase_cli.exe < commands.json > results.json

# Pipe from script
python generate_commands.py | dase_cli.exe | python process_results.py
```

---

### AI Agent Integration (Python)

```python
import subprocess
import json

class DASEInterface:
    def __init__(self, cli_path="dase_cli.exe"):
        self.cli_path = cli_path
        self.process = None

    def start(self):
        """Start persistent CLI process"""
        self.process = subprocess.Popen(
            [self.cli_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

    def send_command(self, command_dict):
        """Send JSON command and get response"""
        # Send command
        json_command = json.dumps(command_dict) + "\n"
        self.process.stdin.write(json_command)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        return json.loads(response_line)

    def stop(self):
        """Stop CLI process"""
        if self.process:
            self.process.terminate()
            self.process.wait()

# Usage
dase = DASEInterface()
dase.start()

# Create engine
response = dase.send_command({
    "command": "create_engine",
    "engine_type": "phase4b",
    "params": {"num_nodes": 1024}
})

engine_id = response["result"]["engine_id"]
print(f"Created engine: {engine_id}")

# Set initial state
dase.send_command({
    "command": "set_node_state",
    "params": {
        "engine_id": engine_id,
        "node_index": 0,
        "value": 1.5
    }
})

# Run simulation
result = dase.send_command({
    "command": "run_mission",
    "params": {
        "engine_id": engine_id,
        "num_steps": 10000,
        "iterations_per_node": 30,
        "return_states": True,
        "node_indices": [0, 1, 2]
    }
})

print(f"Simulation complete in {result['execution_time_ms']} ms")
print(f"Final states: {result['result']['final_states']}")

dase.stop()
```

---

### AI Agent Integration (Node.js)

```javascript
const { spawn } = require('child_process');
const readline = require('readline');

class DASEInterface {
    constructor(cliPath = 'dase_cli.exe') {
        this.cliPath = cliPath;
        this.process = null;
        this.rl = null;
    }

    start() {
        return new Promise((resolve, reject) => {
            this.process = spawn(this.cliPath, [], {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.rl = readline.createInterface({
                input: this.process.stdout,
                output: this.process.stdin
            });

            // Wait for ready signal
            this.process.stdout.once('data', () => resolve());
        });
    }

    async sendCommand(commandObj) {
        return new Promise((resolve, reject) => {
            const jsonCommand = JSON.stringify(commandObj);

            // Send command
            this.process.stdin.write(jsonCommand + '\n');

            // Wait for response
            const onData = (data) => {
                const response = JSON.parse(data.toString());
                this.process.stdout.removeListener('data', onData);
                resolve(response);
            };

            this.process.stdout.on('data', onData);
        });
    }

    stop() {
        if (this.process) {
            this.process.kill();
        }
    }
}

// Usage
(async () => {
    const dase = new DASEInterface();
    await dase.start();

    // Create engine
    const createResponse = await dase.sendCommand({
        command: 'create_engine',
        engine_type: 'igsoa_complex',
        params: { num_nodes: 512, R_c: 1e-34 }
    });

    const engineId = createResponse.result.engine_id;
    console.log(`Created engine: ${engineId}`);

    // Set quantum state
    await dase.sendCommand({
        command: 'set_node_psi',
        params: {
            engine_id: engineId,
            node_index: 0,
            real: 0.707,
            imag: 0.707
        }
    });

    // Run IGSOA simulation
    const result = await dase.sendCommand({
        command: 'run_mission',
        params: {
            engine_id: engineId,
            num_steps: 5000,
            return_states: true
        }
    });

    console.log(`Simulation complete: ${result.execution_time_ms} ms`);
    console.log(`Final quantum state:`, result.result.final_states[0].psi);

    dase.stop();
})();
```

---

## Error Handling

### Error Response Format

```json
{
  "status": "error",
  "command": "run_mission",
  "error": "Engine not found: engine_999",
  "error_code": "ENGINE_NOT_FOUND",
  "details": {
    "engine_id": "engine_999",
    "available_engines": ["engine_001", "engine_002"]
  },
  "execution_time_ms": 0.1
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_JSON` | Malformed JSON input |
| `UNKNOWN_COMMAND` | Command not recognized |
| `MISSING_PARAM` | Required parameter missing |
| `INVALID_PARAM` | Parameter validation failed |
| `ENGINE_NOT_FOUND` | Engine ID doesn't exist |
| `ENGINE_CREATE_FAILED` | Failed to create engine |
| `OUT_OF_MEMORY` | Insufficient memory |
| `EXECUTION_FAILED` | Mission/benchmark failed |
| `INTERNAL_ERROR` | Unexpected internal error |

---

## Implementation Files

### File Structure

```
dase_cli/
├── src/
│   ├── main.cpp                    # CLI entry point
│   ├── json_parser.h/.cpp          # JSON parsing (nlohmann/json)
│   ├── command_router.h/.cpp       # Command dispatch
│   ├── engine_manager.h/.cpp       # Engine lifecycle
│   ├── response_formatter.h/.cpp   # JSON response generation
│   ├── commands/
│   │   ├── lifecycle_commands.cpp  # create_engine, destroy_engine
│   │   ├── state_commands.cpp      # set_node_state, get_node_state
│   │   ├── execution_commands.cpp  # run_mission, run_benchmark
│   │   ├── query_commands.cpp      # get_metrics, list_engines
│   │   └── batch_commands.cpp      # batch execution
│   └── utils/
│       ├── logging.h/.cpp          # Stderr logging (not stdout)
│       └── validators.h/.cpp       # Parameter validation
│
├── CMakeLists.txt
├── README.md
└── examples/
    ├── python_example.py
    ├── nodejs_example.js
    └── batch_example.json
```

---

### main.cpp (Entry Point)

```cpp
#include <iostream>
#include <string>
#include "json_parser.h"
#include "command_router.h"
#include "response_formatter.h"

int main(int argc, char** argv) {
    try {
        CommandRouter router;
        ResponseFormatter formatter;

        // Read JSON commands from stdin line-by-line
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;

            try {
                // Parse JSON command
                auto command = JSONParser::parse(line);

                // Execute command
                auto result = router.execute(command);

                // Format and output JSON response
                std::cout << formatter.format(result) << std::endl;
                std::cout.flush();

            } catch (const std::exception& e) {
                // Error response
                std::cout << formatter.formatError(
                    line, e.what()
                ) << std::endl;
                std::cout.flush();
            }
        }

        return 0;

    } catch (const std::exception& e) {
        // Fatal error (stderr, not stdout)
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}
```

---

### command_router.h

```cpp
#pragma once
#include <string>
#include <map>
#include <functional>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class CommandRouter {
public:
    CommandRouter();

    json execute(const json& command);

private:
    // Command handlers
    json handleCreateEngine(const json& params);
    json handleDestroyEngine(const json& params);
    json handleSetNodeState(const json& params);
    json handleGetNodeState(const json& params);
    json handleRunMission(const json& params);
    json handleRunBenchmark(const json& params);
    json handleGetMetrics(const json& params);
    json handleListEngines(const json& params);
    json handleGetCapabilities(const json& params);
    json handleBatch(const json& params);

    // Command registry
    std::map<std::string,
             std::function<json(const json&)>> commands;
};
```

---

## Build Instructions

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.15)
project(dase_cli)

set(CMAKE_CXX_STANDARD 17)

# nlohmann/json library (header-only)
include(FetchContent)
FetchContent_Declare(
    json
    URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
)
FetchContent_MakeAvailable(json)

# CLI executable
add_executable(dase_cli
    src/main.cpp
    src/json_parser.cpp
    src/command_router.cpp
    src/engine_manager.cpp
    src/response_formatter.cpp
    src/commands/lifecycle_commands.cpp
    src/commands/state_commands.cpp
    src/commands/execution_commands.cpp
    src/commands/query_commands.cpp
    src/commands/batch_commands.cpp
)

target_link_libraries(dase_cli PRIVATE
    nlohmann_json::nlohmann_json
    dase_engine_phase4b
    dase_engine_igsoa_complex
)

# Windows: Build as console application
if(WIN32)
    set_target_properties(dase_cli PROPERTIES
        WIN32_EXECUTABLE FALSE
    )
endif()
```

---

## Testing

### Test Suite (tests/test_cli.py)

```python
import subprocess
import json
import pytest

class TestDASECLI:
    @pytest.fixture
    def cli(self):
        """Start CLI process"""
        proc = subprocess.Popen(
            ['dase_cli.exe'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        yield proc
        proc.terminate()
        proc.wait()

    def send_command(self, cli, cmd):
        """Helper to send command and get response"""
        cli.stdin.write(json.dumps(cmd) + '\n')
        cli.stdin.flush()
        response = cli.stdout.readline()
        return json.loads(response)

    def test_get_capabilities(self, cli):
        """Test capabilities command"""
        response = self.send_command(cli, {
            "command": "get_capabilities"
        })

        assert response["status"] == "success"
        assert "version" in response["result"]
        assert "phase4b" in response["result"]["engines"]

    def test_create_destroy_engine(self, cli):
        """Test engine lifecycle"""
        # Create
        create_resp = self.send_command(cli, {
            "command": "create_engine",
            "engine_type": "phase4b",
            "params": {"num_nodes": 1024}
        })

        assert create_resp["status"] == "success"
        engine_id = create_resp["result"]["engine_id"]

        # Destroy
        destroy_resp = self.send_command(cli, {
            "command": "destroy_engine",
            "params": {"engine_id": engine_id}
        })

        assert destroy_resp["status"] == "success"

    def test_full_workflow(self, cli):
        """Test complete simulation workflow"""
        # Create engine
        create_resp = self.send_command(cli, {
            "command": "create_engine",
            "engine_type": "phase4b",
            "params": {"num_nodes": 1024}
        })
        engine_id = create_resp["result"]["engine_id"]

        # Set state
        set_resp = self.send_command(cli, {
            "command": "set_node_state",
            "params": {
                "engine_id": engine_id,
                "node_index": 0,
                "value": 1.5
            }
        })
        assert set_resp["status"] == "success"

        # Run mission
        run_resp = self.send_command(cli, {
            "command": "run_mission",
            "params": {
                "engine_id": engine_id,
                "num_steps": 1000,
                "return_states": True,
                "node_indices": [0]
            }
        })

        assert run_resp["status"] == "success"
        assert run_resp["result"]["steps_completed"] == 1000

        # Get metrics
        metrics_resp = self.send_command(cli, {
            "command": "get_metrics",
            "params": {"engine_id": engine_id}
        })

        assert metrics_resp["status"] == "success"
        assert "ns_per_op" in metrics_resp["result"]
```

---

## Deployment

### Building

```bash
mkdir build
cd build
cmake ..
cmake --build . --config Release

# Output: build/Release/dase_cli.exe
```

### Distribution

```
dase_cli_v1.0/
├── dase_cli.exe                      # Main executable
├── dase_engine_phase4b.dll           # Phase 4B engine
├── dase_engine_igsoa_complex.dll     # IGSOA Complex engine
├── README.md                          # Usage guide
├── COMMAND_REFERENCE.md               # Command documentation
└── examples/
    ├── python_example.py
    ├── nodejs_example.js
    └── batch_simulation.json
```

---

## Conclusion

This headless JSON CLI provides:

✅ **AI-friendly interface** - Pure JSON in/out, no interactive prompts
✅ **Dual-engine support** - Both Phase 4B and IGSOA Complex
✅ **Batch operations** - Multiple commands in one call
✅ **Error handling** - Structured error responses
✅ **Scriptable** - Easy integration with Python, Node.js, etc.
✅ **Persistent mode** - Keep process alive for multiple commands
✅ **Performance** - Direct C++ calls, minimal overhead

**Perfect for AI augmentation** - Your AI agent can now control the DASE engine!

Next: Would you like me to implement the CLI skeleton (main.cpp, command_router.cpp)?
