# DASE CLI JSON Command Guide

This guide explains how to interact with the **DASE Command-Line Interface (CLI)** using JSON commands. It’s designed for simplicity — even if you’re new to JSON or command-line tools.

---

## 🧩 1. Basic JSON Structure

Every command follows this structure:

```json
{
  "command": "COMMAND_NAME",
  "params": { ... }
}
```

**Rules:**
- Always use double quotes `""` around keys and string values.
- Do not include trailing commas.
- Use a single JSON object (no arrays or multiple roots).

---

## ⚙️ 2. Supported Commands

### **a. Get Capabilities**
Check what the engine supports.

```json
{
  "command": "get_capabilities"
}
```

**Example Output:**
```json
{
  "status": "success",
  "result": {
    "cpu_features": { "avx2": true, "avx512": false, "fma": true },
    "engines": ["phase4b", "igsoa_complex"],
    "max_nodes": 1048576,
    "version": "1.0.0"
  }
}
```

---

### **b. Create Engine**
Initialize a new simulation engine.

```json
{
  "command": "create_engine",
  "params": {
    "engine_type": "phase4b",
    "num_nodes": 2048
  }
}
```

**Example Output:**
```json
{
  "status": "success",
  "result": {
    "engine_id": "engine_001",
    "engine_type": "phase4b",
    "num_nodes": 2048
  }
}
```

---

### **c. Run Mission**
Run a simulation with a specified configuration.

```json
{
  "command": "run_mission",
  "params": {
    "engine_id": "engine_001",
    "mission": {
      "engine_type": "phase4b",
      "timestep": 0.0005,
      "num_steps": 2000,
      "integrator": "rk4",
      "boundary": "periodic",
      "damping": 0.001,
      "timeout_sec": 300,
      "progress_interval": 50,
      "output_frequency": 20,
      "output_file": "mission_short.json"
    }
  }
}
```

**Example Run Command:**
```cmd
type mission_short.json | dase_cli.exe
```

---

### **d. Get Metrics**
Fetch runtime performance statistics after a mission completes.

```json
{
  "command": "get_metrics",
  "params": {
    "engine_id": "engine_001"
  }
}
```

**Example Output:**
```json
{
  "status": "success",
  "result": {
    "engine_type": "phase4b",
    "ns_per_op": 0.18,
    "ops_per_sec": 5611919849,
    "total_operations": 81920000
  }
}
```

---

## 🖥️ 3. How to Send JSON Commands

| Environment | Command |
|--------------|----------|
| **CMD (Windows)** | `type mission.json | dase_cli.exe` |
| **PowerShell** | `Get-Content mission.json -Raw | ./dase_cli.exe` |
| **Linux/macOS** | `cat mission.json | ./dase_cli` |

⚠️ **Avoid using** `echo {...}` on Windows — it corrupts quotes.

---

## 🧠 4. Recommended Workflow

1. Check engine capabilities:
   ```cmd
   type get_capabilities.json | dase_cli.exe
   ```
2. Create an engine:
   ```cmd
   type create_engine.json | dase_cli.exe
   ```
3. Run your mission:
   ```cmd
   type mission_short.json | dase_cli.exe
   ```
4. Retrieve metrics:
   ```cmd
   type get_metrics.json | dase_cli.exe
   ```

---

## 📁 5. Mission Object Fields

| Field | Type | Description |
|--------|------|-------------|
| `timestep` | float | Simulation time step in seconds |
| `num_steps` | int | Number of steps to simulate |
| `integrator` | string | Integration method (`euler`, `rk4`, or `verlet`) |
| `boundary` | string | Boundary condition (e.g., `periodic`) |
| `damping` | float | Damping factor for stability |
| `timeout_sec` | int | Maximum allowed runtime |
| `progress_interval` | int | How often to print progress updates |
| `output_frequency` | int | How often to write results to file |
| `output_file` | string | Path/name of mission output file |

---

## ✅ Example Mission (Copy & Paste Ready)

```json
{
  "command": "run_mission",
  "params": {
    "engine_id": "engine_001",
    "mission": {
      "engine_type": "phase4b",
      "timestep": 0.0005,
      "num_steps": 2000,
      "integrator": "rk4",
      "boundary": "periodic",
      "damping": 0.001,
      "timeout_sec": 300,
      "progress_interval": 50,
      "output_frequency": 20,
      "output_file": "mission_short.json"
    }
  }
}
```

---

**Pro Tip:**
If you plan to automate multiple missions, store each command as its own `.json` file and call them sequentially with a batch file or PowerShell script.