# DASE Engine Operations Manual

## 1. Overview

### Introduction

The Dynamic Analog Simulation Engine (DASE) is a high-performance computing platform designed for the simulation and analysis of Spatially-Aware Temporal Physics (SATP). It provides a powerful, scriptable environment for researchers to explore complex physical phenomena through two distinct, specialized computational engines.

The system is primarily operated via a headless command-line interface (`dase_cli.exe`), which accepts newline-delimited JSON commands. This design facilitates easy integration with automated scripts, AI agents, and other external tools for running complex simulation "missions."

### Dual-Engine Architecture

DASE employs a dual-engine architecture to meet diverse computational needs:

1.  **Phase 4B Analog Engine**: This is a real-valued, AVX2-optimized engine designed for maximum computational speed (benchmarked at ~2.87 ns/op). It is implemented as a dynamically loaded library (`dase_engine_phase4b.dll`) and is ideal for tasks requiring high-throughput analog signal processing and simulation where quantum effects are not the primary focus.

2.  **IGSOA Complex Engine**: This is a complex-valued, quantum-inspired engine specifically designed for high-fidelity SATP physics simulations. It correctly models non-local causal interactions up to a configurable radius (`R_c`), a critical feature for accurate physics modeling. Unlike the analog engine, the IGSOA engine is a header-only library compiled directly into the main CLI executable, ensuring tight integration and performance. It exists in 1D, 2D, and 3D variants to support different simulation dimensionalities.

### Core SATP Concepts

The IGSOA engine simulates the evolution of a quantum state (Ψ) and its interaction with a realized field (Φ). A key parameter in these simulations is the **non-local causal radius (`R_c`)**, which defines the extent of influence between different points in the simulated space. Recent critical bug fixes have ensured this parameter is correctly implemented, allowing the engine to move beyond simple nearest-neighbor interactions to true non-local physics. The engine supports advanced state manipulation techniques, such as blending external states into the simulation, enabling sophisticated "SATP v2" mission profiles.

## 2. Quick Start Guide

This guide provides a step-by-step tutorial for running a standard 1D SATP simulation, which involves scanning different E-field initial conditions and extracting the final state for each run.

### Step 1: Prepare the Mission File

A mission is a sequence of newline-delimited JSON commands that instruct the DASE CLI. For this guide, we will use `missions/SATP_v2_1D_E-field_scan.json`.

This mission file performs the following actions:
1.  **Creates** a 1D IGSOA Complex engine.
2.  **Loops** five times through the following sequence:
    a. **Sets** the initial state of the engine using `set_igsoa_state`, loading a new E-field value for the quantum state (Ψ) in each iteration.
    b. **Runs** the simulation for 10.0 seconds with a non-local causal radius (`R_c`) of 1.0.
    c. **Extracts** the final engine state using `get_state`.
3.  **Destroys** the engine to clean up resources.

Here is a snippet of the commands used in the mission:
```json
{ "command": "create_engine", "engine_type": "igsoa_complex", "engine_id": "igsoa_1d_scan", "grid_size": 1024, "dimensions": 1 }
{ "command": "set_igsoa_state", "engine_id": "igsoa_1d_scan", "mode": "overwrite", "psi_real_file": "initial_conditions/psi_1d_E_0.1.bin" }
{ "command": "run_simulation", "engine_id": "igsoa_1d_scan", "duration": 10.0, "R_c": 1.0 }
{ "command": "get_state", "engine_id": "igsoa_1d_scan", "format": "json_compact_verbose" }
...
{ "command": "destroy_engine", "engine_id": "igsoa_1d_scan" }
```

### Step 2: Run the Simulation

To run the simulation, open a command prompt in the `dase_cli` directory and pipe the mission file into the `dase_cli.exe` executable. Redirect the output to a file for later analysis.

```bash
# From the F:\satp\igsoa-sim\dase_cli directory
type ..\missions\SATP_v2_1D_E-field_scan.json | dase_cli.exe > ..\results\e_field_scan_results.json
```
*(Note: The `run_mission.bat` script provides a convenient wrapper for this command.)*

The CLI will process each JSON command in the mission file sequentially and print the JSON results to `stdout`, which are then captured in `e_field_scan_results.json`.

### Step 3: Analyze the Results

The output file contains a series of JSON objects, including the detailed final state from each `get_state` command. This state information can be used for physics analysis.

The `dase_cli` directory includes a Python script, `analyze_igsoa_state.py`, to perform spectral analysis (FFT) on the extracted state data. To run it, you would typically parse the JSON output to feed the state data into the script.

While the automation of this analysis is outside the scope of this quick start, the `analyze_igsoa_state.py` script is the primary tool for validating the physical realism of the simulation output.

## 3. Command and API Reference

This section provides a detailed reference for the commands accepted by the `dase_cli.exe` interface and a brief overview of the available APIs.

### 3.1. JSON CLI Commands

The CLI accepts a newline-delimited stream of JSON objects. Each object represents a command to be executed.

#### `create_engine`
Creates and initializes a new simulation engine instance.

*   **Parameters**:
    *   `command` (string): Must be `"create_engine"`.
    *   `engine_type` (string): The type of engine to create. Can be `"igsoa_complex"` or `"phase4b"`.
    *   `engine_id` (string): A unique identifier for the new engine instance.
    *   `grid_size` (integer): The size of the simulation grid (e.g., 1024). Required for `igsoa_complex`.
    *   `dimensions` (integer): The number of spatial dimensions (1, 2, or 3). Required for `igsoa_complex`.
*   **Example**:
    ```json
    { "command": "create_engine", "engine_type": "igsoa_complex", "engine_id": "my_sim_1", "grid_size": 2048, "dimensions": 1 }
    ```

#### `run_simulation`
Runs the simulation for a specified duration.

*   **Parameters**:
    *   `command` (string): Must be `"run_simulation"`.
    *   `engine_id` (string): The ID of the engine to run.
    *   `duration` (float): The simulation time in seconds.
    *   `R_c` (float): The non-local causal radius. This is a critical physics parameter for the `igsoa_complex` engine.
    *   `status_interval` (float, optional): The interval in seconds at which to output status updates.
*   **Example**:
    ```json
    { "command": "run_simulation", "engine_id": "my_sim_1", "duration": 50.0, "R_c": 2.5 }
    ```

#### `set_igsoa_state`
Sets the state of the IGSOA engine's simulation fields (Ψ and Φ). This is a powerful command with multiple modes for advanced state manipulation.

*   **Parameters**:
    *   `command` (string): Must be `"set_igsoa_state"`.
    *   `engine_id` (string): The ID of the `igsoa_complex` engine to modify.
    *   `mode` (string): The mode of operation. See Section 3.2 for details. Can be `"overwrite"`, `"add"`, or `"blend"`.
    *   `phi_real_file` / `phi_imag_file` (string, optional): Path to a binary file containing the real/imaginary part of the Φ field.
    *   `psi_real_file` / `psi_imag_file` (string, optional): Path to a binary file containing the real/imaginary part of the Ψ field.
    *   `blend_weight` (float, optional): Required for `blend` mode. A value from 0.0 to 1.0.
*   **Example (`overwrite` mode)**:
    ```json
    { "command": "set_igsoa_state", "engine_id": "my_sim_1", "mode": "overwrite", "psi_real_file": "init/psi_real.bin", "psi_imag_file": "init/psi_imag.bin" }
    ```

#### `get_state`
Extracts the full simulation state (Ψ and Φ) from the IGSOA engine.

*   **Parameters**:
    *   `command` (string): Must be `"get_state"`.
    *   `engine_id` (string): The ID of the `igsoa_complex` engine to query.
    *   `format` (string): The desired output format. `"json_compact_verbose"` is recommended for analysis, providing a JSON object with base64-encoded binary data.
*   **Example**:
    ```json
    { "command": "get_state", "engine_id": "my_sim_1", "format": "json_compact_verbose" }
    ```

#### `destroy_engine`
Destroys an engine instance and frees its associated resources.

*   **Parameters**:
    *   `command` (string): Must be `"destroy_engine"`.
    *   `engine_id` (string): The ID of the engine to destroy.
*   **Example**:
    ```json
    { "command": "destroy_engine", "engine_id": "my_sim_1" }
    ```

### 3.2. `set_igsoa_state` Modes

The `mode` parameter in the `set_igsoa_state` command allows for fine-grained control over how initial conditions are applied.

*   **`overwrite`**: This mode completely replaces the engine's current state with the data provided in the file(s). This is the most common mode for starting a simulation from a known initial condition.

*   **`add`**: This mode performs an element-wise addition of the state data from the file(s) to the engine's existing state. This can be used to introduce perturbations or superimpose fields.

*   **`blend`**: This mode performs a weighted interpolation between the engine's existing state and the new state from the file(s). It requires the `blend_weight` parameter. The new state is calculated as: `(1 - w) * current_state + w * new_state`, where `w` is the `blend_weight`. This is used in "SATP v2" missions to smoothly introduce changes over time.

### 3.3. C++/Python APIs

While the JSON CLI is the primary interface, DASE also exposes underlying APIs:
*   **C++ API**: The core engine logic is written in C++. The header files (`.h`) in `src/cpp` define the classes and functions that can be used to directly embed the engine into other C++ applications. This is the most performant way to use the engine but requires manual integration.
*   **Python Bindings**: A Python wrapper (`dase_engine.pyd`) is provided, which exposes the C++ engine functionality to Python. This is used by some of the analysis scripts and the WebSocket bridge server. It offers a balance between performance and ease of use.

## 4. Analysis & Validation

Once a simulation is complete, the primary goal is to analyze the output to extract meaningful data and validate the physical realism of the results. The `get_state` command provides the raw data, and a suite of Python scripts is available for processing it.

### 4.1. Key Analysis Tools

The main analysis scripts are located in the `dase_cli` directory. They are designed to operate on the JSON output produced by the CLI.

#### `analyze_igsoa_state.py`
This is the primary tool for physics validation. It parses the base64-encoded state data from a `get_state` command's output, performs a Fast Fourier Transform (FFT) on the spatial data of the Ψ and Φ fields, and plots the resulting power spectrum.

*   **Purpose**: To analyze the spectral characteristics of the simulation state. This is crucial for identifying dominant wave modes, verifying expected physical behavior, and detecting numerical instability.
*   **Usage**: The script must be modified to parse the specific JSON output file from your simulation. It then extracts the state data, decodes it, and generates plots of the power spectrum vs. wavenumber.

#### `extract_drift.py`
This script is used to measure the total energy of the simulation state over time. By comparing the energy at the beginning and end of a run, it can quantify the numerical drift of the simulation.

*   **Purpose**: To verify the energy conservation of the simulation, a key indicator of numerical stability.
*   **Usage**: This script typically requires a mission that captures the state at multiple points in time. It then calculates and plots the total energy for each snapshot. For a stable system, this value should remain nearly constant.

### 4.2. Core Validation Checks

Validation involves confirming that the simulation behaves according to the principles of SATP theory. Based on recent development and bug fixes, the following are critical validation checks:

*   **`R_c` Performance Scaling**: A fundamental validation of the IGSOA engine is to confirm that the computational cost of a simulation scales correctly with the non-local causal radius (`R_c`). As established in the `RC_FIX_FINAL_REPORT.md`, performance should decrease as `R_c` increases, reflecting the greater number of interactions being calculated. This confirms the critical non-local physics fix is active.

*   **Zero-Drift in Null Field**: When initialized with a zero-field state (or other stable configurations), the simulation should exhibit near-zero energy drift over time. The `extract_drift.py` tool is used to verify this property.

*   **Spectral Purity**: For simulations initialized with a single, pure wave mode, the power spectrum generated by `analyze_igsoa_state.py` should show a single, sharp peak at the corresponding wavenumber. The absence of other significant peaks demonstrates that the simulation is not introducing spurious numerical artifacts.

## 5. Development & Architecture

This section provides an overview of the project's structure, build system, and software architecture for developers who wish to extend or modify the DASE system.

### 5.1. Project Structure

The project is organized into the following key directories:

*   `src/`: Contains the core C++ source code for the simulation engines (`cpp/`) and the Python bindings (`python/`).
*   `dase_cli/`: Contains the source for the command-line interface, analysis scripts, and example mission commands. This is the primary user-facing component.
*   `missions/`: A collection of example and canonical mission files (in NDJSON format) for running various simulations.
*   `results/`: The default output directory for simulation results.
*   `docs/`: Contains detailed markdown documentation on various aspects of the project, from theory to implementation.
*   `build/`: The default directory for build artifacts generated by CMake.

### 5.2. Build System

The project uses a unified **CMake** build system, which has replaced the previous collection of disparate `.bat` build scripts. The primary build configuration is defined in the `CMakeLists.txt` file in the project root.

*   **Building the C++ CLI**: To build the `dase_cli.exe` executable, configure and generate the project with CMake, then use your chosen C++ compiler (e.g., MSVC, GCC). The build process will automatically include the header-only IGSOA engine.
    ```bash
    # Example build process from root directory
    mkdir build
    cd build
    cmake ..
    cmake --build .
    ```
*   **Building Python Bindings**: The `setup.py` script in `src/python` is used to build the `dase_engine.pyd` Python module. This process is also integrated into the main CMake build.

### 5.3. Architecture Overview

*   **Headless CLI Core**: The central architectural principle is the headless `dase_cli.exe` application that processes JSON commands. This ensures maximum flexibility and scriptability.

*   **Header-Only IGSOA Engine**: The IGSOA Complex engine is implemented as a header-only library (`.h` files in `src/cpp`). This means that any changes to the physics or core logic of the IGSOA engine require a full rebuild of the `dase_cli.exe` executable that includes it. The Phase 4B engine, by contrast, is a standard dynamic library.

*   **Web Interface (Future)**: As detailed in `INTEGRATION_PLAN.md`, a web-based visual interface is planned. The `src/python/bridge_server_improved.py` provides a WebSocket server that acts as a bridge between a web front-end and the Python bindings. This component is currently in a prototype stage and is not yet fully integrated.
