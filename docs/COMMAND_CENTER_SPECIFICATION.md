# DASE Command Center - Technical Specification

## 1. Overview & Vision

This document outlines the technical specification for the DASE Command Center, a comprehensive web-based graphical user interface (GUI) designed to replace and extend the capabilities of the existing command-line tools.

The vision is to create a single, integrated environment for the entire simulation workflow:
- **Mission Design:** Defining the fundamental physics, equations, and parameters of a simulation.
- **Execution:** Running simulations using any of the available DASE engine types.
- **Monitoring:** Observing simulation progress and key metrics in real-time.
- **Analysis:** Visualizing and processing results using integrated tools.

The GUI will be modeled after a spreadsheet, providing a familiar yet powerful interface for manipulating numerical data, linking parameters, and visualizing live results.

## 2. System Architecture

The Command Center will be a client-server application composed of a backend orchestrator and a frontend user interface.

### 2.1. Backend (Node.js)

The existing `backend/server.js` will be enhanced to serve as the central orchestrator.

- **Technology:** Node.js, Express.js, and a WebSocket library (e.g., `socket.io`).
- **Responsibilities:**
    - **Process Management:** Spawning and managing `dase_cli.exe` child processes for simulation runs. This includes handling process lifecycle, termination, and error reporting.
    - **I/O Streaming:** Using WebSockets to create a persistent, bidirectional communication channel with the frontend for streaming `dase_cli.exe`'s stdin, stdout, and stderr.
    - **Engine Introspection:** Interfacing with `dase_cli.exe` to discover the capabilities of different simulation engines.
    - **API Server:** Providing a RESTful API for the frontend to manage files, simulations, and analysis tasks.
    - **Metric Parsing:** Watching the stdout of a simulation for specially formatted metric data, parsing it, and pushing it to the frontend via WebSockets.

### 2.2. Frontend (React SPA)

A modern, modular Single-Page Application (SPA) will be built in the `/web` directory.

- **Technology:** React, a state management library (e.g., Redux or Zustand), a terminal component (e.g., `Xterm.js`), and a data visualization library (e.g., `Plotly.js`).
- **Responsibilities:**
    - **User Interface:** Rendering the dynamic Command Center interface, including the grid, flyout panels, and terminal.
    - **State Management:** Maintaining the complete state of the application, including mission parameters, grid cell values, and UI state.
    - **Backend Communication:** Interacting with the backend via the REST API and WebSocket connection.
    - **Dynamic UI Generation:** Building context-aware UI elements (like the Model Editor) based on data received from the backend about engine capabilities.

## 3. Core Component Specifications

### 3.1. The Main Grid

The central component of the UI. It is a dynamic calculation sheet, not a static table.

- **Formula Engine:** Cells must support Excel-like formulas for arithmetic and function calls (e.g., `=A1 * (B2 / 2)`, `=SUM(C1:C10)`).
- **Parameter Linking:** The value of any simulation parameter (e.g., a constant in an equation, an initial condition) can be linked to a grid cell by referencing its address (e.g., setting a value to `=C5`).
- **Live Metric Display:** Cells must support a special function, `=LIVE("metric_name")`, to subscribe to real-time data streams from the backend. The cell's value will update automatically as the backend pushes new metric data.

### 3.2. UI Panels

The UI will use flyout panels for configuration and output.

- **Model Panel:**
    - **Engine Selector:** A dropdown to select the active simulation engine.
    - **Dynamic Editors:** The panel will contain editors for **Differential Equations** and **Boundary Conditions**. The fields and options available in these editors will be generated dynamically based on the selected engine's capabilities.
- **Mission Panel:**
    - A file browser to load and save mission configuration files (in JSON format) from the `/missions` directory.
- **Results & Analysis Panel:**
    - A file browser for the `/results` directory.
    - An integrated viewer for common output formats (e.g., `.png`, `.csv`).
    - A data visualizer that automatically plots data from selected `.csv` files.
    - An interface to select and run Python analysis scripts from the `/analysis` directory on simulation outputs.
- **Terminal Panel:**
    - An integrated, fully functional terminal providing direct, interactive access to the running `dase_cli.exe` process.

## 4. Backend API & WebSockets

### 4.1. `dase_cli.exe` Requirements

To support this architecture, `dase_cli.exe` must be updated to:

1.  **Provide Self-Description:** Implement a `--describe` flag.
    - **Command:** `dase_cli.exe --engine [engine_name] --describe`
    - **Output:** A JSON object detailing the engine's supported equations, parameters, and boundary conditions.
2.  **Emit Structured Metrics:** During a run, output key metrics to stdout in a parsable format.
    - **Format:** `METRIC:{"name": "simulation_time", "value": 10.5, "units": "s"}`

### 4.2. REST API Endpoints

The backend will expose the following endpoints under the `/api` prefix:

- `GET /engines`: Returns a list of all available engine names.
- `GET /engines/:name`: Returns the full JSON description for a specific engine by calling the CLI's `--describe` flag.
- `POST /simulations`: Starts a new simulation. The request body will contain the complete mission JSON. Returns a simulation ID.
- `GET /simulations/:id`: Returns the status of a running simulation.
- `DELETE /simulations/:id`: Stops/terminates the specified simulation process.
- `POST /analysis`: Executes a specified Python analysis script.
- `GET /fs?path=[directory]`: Provides file/directory listings for frontend file browsers (e.g., for `/missions` or `/results`).

### 4.3. WebSocket Events

- **`client -> server`:**
    - `terminal:stdin`: Sends user input from the frontend terminal to the `dase_cli.exe` process.
- **`server -> client`:**
    - `terminal:stdout`: Streams output from `dase_cli.exe` to the frontend terminal.
    - `metrics:update`: Pushes a parsed metric object (e.g., `{ "name": "core_temp", "value": 350.5 }`) to the frontend for display in the grid.
    - `simulation:state`: Notifies the client of changes in the simulation state (e.g., `running`, `finished`, `error`).

## 5. Example User Workflow

1.  **Initialization:** User opens the Command Center. The frontend fetches the list of available engines from `GET /api/engines`.
2.  **Model Setup:** User selects an engine (e.g., `dase_engine_phase4a`) from the "Model" panel's dropdown. The frontend calls `GET /api/engines/dase_engine_phase4a` and dynamically builds the UI for its equations and boundary conditions.
3.  **Parameterization:** User defines the model's physics. For an initial condition value, instead of a number, they enter `=C1` into the input field. They then enter `100` into cell `C1` of the main grid.
4.  **Execution:** User clicks "▶ Run".
5.  **Backend Process:** The frontend compiles a mission JSON containing the model definition and all referenced grid values. It sends this to `POST /api/simulations`. The backend launches `dase_cli.exe` and establishes the I/O stream over the WebSocket.
6.  **Monitoring:** The Terminal panel shows the live output of the CLI. A grid cell with the formula `=LIVE("sim_time")` begins updating in real-time.
7.  **Analysis:** The simulation completes. A result file, `run_output.csv`, appears in the "Results" panel. The user clicks it, and a plot of the data is displayed. The user then selects `compute_autocorrelation.py`, targets `run_output.csv`, and runs the analysis via a call to `POST /api/analysis`. The result appears in the panel.
