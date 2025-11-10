# DASE CLI - Headless JSON Interface

A command-line JSON interface for the DASE (Dynamic Analog Synthesis Engine) suitable for AI augmentation and automation.

## Overview

`dase_cli.exe` provides a headless, JSON-based interface to the DASE analog computation engines:
- **Phase 4B** - High-performance real-valued analog computation (2.76 ns/op)
- **IGSOA Complex** - Quantum-inspired complex-valued physics engine (4-8 ns/op target)

Perfect for:
- ✅ AI agent integration (Claude, GPT, custom agents)
- ✅ Automation and scripting
- ✅ Batch processing
- ✅ Microservices architecture
- ✅ Cloud deployment

## Quick Start

### Building

```bash
# From project root
mkdir build
cd build
cmake ..
cmake --build . --config Release

# CLI will be at: build/Release/dase_cli.exe
```

### Basic Usage

```bash
# Send a single command
echo '{"command":"get_capabilities"}' | dase_cli.exe

# From file
dase_cli.exe < commands.json > results.json

# Interactive (for testing)
dase_cli.exe
{"command":"get_capabilities"}
# Press Ctrl+Z then Enter on Windows, or Ctrl+D on Linux to finish
```

### Python Example

```python
import subprocess
import json

# Start CLI
proc = subprocess.Popen(
    ['dase_cli.exe'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Send command
command = {"command": "get_capabilities"}
proc.stdin.write(json.dumps(command) + '\n')
proc.stdin.flush()

# Get response
response = json.loads(proc.stdout.readline())
print(f"DASE Version: {response['result']['version']}")

proc.terminate()
```

## Command Format

All commands use JSON:

**Request:**
```json
{
  "command": "command_name",
  "params": {
    // Command-specific parameters
  }
}
```

**Response:**
```json
{
  "status": "success" | "error",
  "command": "command_name",
  "result": {
    // Command-specific results
  },
  "execution_time_ms": 123.45
}
```

## Available Commands

See [HEADLESS_JSON_CLI_ARCHITECTURE.md](../docs/HEADLESS_JSON_CLI_ARCHITECTURE.md) for complete documentation.

### System Commands

- `get_capabilities` - Get CLI version, available engines, hardware info
- `list_engines` - List all active engine instances

### Engine Lifecycle

- `create_engine` - Create a new engine instance
- `destroy_engine` - Destroy an engine instance

### State Management

- `set_node_state` - Set a single node's state (real or complex)
- `set_bulk_state` - Set multiple nodes at once
- `get_node_state` - Get a node's current state
- `get_all_states` - Get all node states

### Execution

- `run_mission` - Execute simulation for N steps
- `run_benchmark` - Run performance benchmark

### Metrics

- `get_metrics` - Get engine performance metrics

## Testing

```bash
# Test basic CLI functionality
python test_cli.py
```

## Architecture

```
┌──────────────────────┐
│  AI Agent / Script   │
└──────┬───────────────┘
       │ JSON (stdin)
       ▼
┌──────────────────────┐
│  dase_cli.exe        │
│  ┌────────────────┐  │
│  │ Command Router │  │
│  ├────────────────┤  │
│  │ Phase 4B       │  │
│  │ IGSOA Complex  │  │
│  └────────────────┘  │
└──────┬───────────────┘
       │ JSON (stdout)
       ▼
┌──────────────────────┐
│  AI Agent / Script   │
└──────────────────────┘
```

## Error Handling

All errors are returned as JSON on stdout:

```json
{
  "status": "error",
  "command": "run_mission",
  "error": "Engine not found: engine_999",
  "error_code": "ENGINE_NOT_FOUND",
  "execution_time_ms": 0.1
}
```

Fatal errors (CLI crash, invalid JSON) are sent to stderr.

## Development Status

**Current Status:** Minimal skeleton implementation

**Implemented:**
- ✅ Main CLI loop (stdin/stdout)
- ✅ Basic JSON echo
- ⏳ Command parser (planned)
- ⏳ Engine management (planned)
- ⏳ Full command set (planned)

**Roadmap:**
1. Implement command router with nlohmann/json
2. Integrate Phase 4B engine
3. Add IGSOA Complex engine support
4. Full command set implementation
5. Comprehensive testing

## Example Workflow

```bash
# 1. Create engine
echo '{"command":"create_engine","engine_type":"phase4b","params":{"num_nodes":1024}}' | dase_cli.exe
# {"status":"success","result":{"engine_id":"engine_001"},...}

# 2. Set initial state
echo '{"command":"set_node_state","params":{"engine_id":"engine_001","node_index":0,"value":1.5}}' | dase_cli.exe

# 3. Run simulation
echo '{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":10000}}' | dase_cli.exe

# 4. Get results
echo '{"command":"get_node_state","params":{"engine_id":"engine_001","node_index":0}}' | dase_cli.exe
```

## License

Same as DASE project

## See Also

- [HEADLESS_JSON_CLI_ARCHITECTURE.md](../docs/HEADLESS_JSON_CLI_ARCHITECTURE.md) - Complete architecture documentation
- [IGSOA_COMPLEX_ENGINE_IMPLEMENTATION_PLAN.md](../docs/IGSOA_COMPLEX_ENGINE_IMPLEMENTATION_PLAN.md) - Complex engine design
- [Phase 4B Benchmarks](../benchmarks/) - Performance benchmarks
