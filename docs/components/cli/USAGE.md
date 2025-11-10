# DASE CLI Usage Guide

## Quick Start

The DASE CLI reads JSON commands from stdin, one command per line.

### Windows Command Prompt

```cmd
REM Using the batch script
run_mission.bat mission_short_fixed.json

REM Or directly with type
type mission_short_fixed.json | dase_cli.exe
```

### PowerShell

```powershell
# Using the PowerShell script
.\run_mission.ps1 mission_short_fixed.json

# Or directly
Get-Content mission_short_fixed.json | .\dase_cli.exe
```

### Git Bash / Linux

```bash
cat mission_short_fixed.json | ./dase_cli.exe
```

## JSON Command Format

**IMPORTANT**: Each JSON command must be on a **single line** (no pretty-printing).

### Available Commands

#### 1. Create Engine
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
```

To start a 2D IGSOA lattice, supply lattice dimensions and physics knobs:

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex_2d","N_x":64,"N_y":64,"R_c":4.0,"kappa":1.0,"gamma":0.1,"dt":0.01}}
```

The response echoes `N_x/N_y` so downstream tools know the lattice shape.

<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
To start a 3D IGSOA lattice, include the depth (`N_z`):

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex_3d","N_x":32,"N_y":32,"N_z":32,"R_c":3.5,"kappa":1.0,"gamma":0.1,"dt":0.01}}
```

The CLI validates the `N_x × N_y × N_z` volume and returns the dimensions in the response payload so post-processing tools can infer the 3D layout.

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
#### 2. Set IGSOA State (2D Profiles)
```json
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"circular_gaussian","params":{"amplitude":1.0,"center_x":32.0,"center_y":32.0,"sigma":8.0,"baseline_phi":0.0,"mode":"overwrite"}}}
```

`profile_type` accepts the 2D presets wired into `IGSOAStateInit2D`:
`gaussian_2d`, `circular_gaussian`, `plane_wave_2d`, `uniform`, `random`, and
`reset`.  Each profile forwards its parameter block directly to the
corresponding helper, so you can pass blend factors, sigma splits, and seeds as
documented in `IGSOA_2D_ENGINE_IMPLEMENTATION.md`.

<<<<<<< ours
<<<<<<< ours
=======
=======
>>>>>>> theirs
#### 2b. Set IGSOA State (3D Profiles)

```json
{"command":"set_igsoa_state","params":{"engine_id":"engine_002","profile_type":"spherical_gaussian","params":{"amplitude":1.0,"center_x":16.0,"center_y":16.0,"center_z":16.0,"sigma":6.0,"mode":"overwrite"}}}
```

3D engines accept the presets defined by `IGSOAStateInit3D`: `gaussian_3d`, `spherical_gaussian`, `plane_wave_3d`, `uniform`, `random_3d`, and `reset`.  The argument schema mirrors the 2D helpers so you can reuse automation, but with an additional `center_z`, `sigma_z`, and optional `k_z` component where applicable.

<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
#### 3. Run Mission
```json
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":2000,"iterations_per_node":20}}
```

Parameters:
- `engine_id`: ID returned from create_engine
- `num_steps`: Number of simulation steps
- `iterations_per_node`: Iterations per node per step (default: 30)

#### 4. Get Metrics
```json
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
```

#### 5. List Engines
```json
{"command":"list_engines","params":{}}
```

#### 6. Destroy Engine
```json
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
```

#### 7. Get Capabilities
```json
{"command":"get_capabilities","params":{}}
```

#### 8. Extract State (2D-Aware)
```json
{"command":"get_state","params":{"engine_id":"engine_001"}}
```

The payload contains flattened `psi_real`, `psi_imag`, and `phi` arrays plus a
<<<<<<< ours
<<<<<<< ours
`dimensions` object with `N_x`/`N_y` whenever the engine was created as
`igsoa_complex_2d`.  Capture this output to feed directly into
`tools/analyze_igsoa_2d.py`.

#### 9. Measure 2D Drift
=======
=======
>>>>>>> theirs
`dimensions` object with `N_x`/`N_y` (and `N_z` for 3D engines) whenever the
engine was created as `igsoa_complex_2d` or `igsoa_complex_3d`.  Capture this
output to feed directly into `tools/analyze_igsoa_2d.py` or downstream
visualizers.

#### 9. Measure Drift (2D/3D)
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
```json
{"command":"get_center_of_mass","params":{"engine_id":"engine_001"}}
```

<<<<<<< ours
<<<<<<< ours
Returns the instantaneous `(x_cm, y_cm)` location of the informational density
so you can monitor drift without exporting the full lattice.
=======
=======
>>>>>>> theirs
Returns the instantaneous center-of-mass of the informational density.  For 2D
engines the payload contains `(x_cm, y_cm)`; for 3D engines a `z_cm` coordinate
is included automatically.  This allows drift monitoring without exporting the
full lattice.
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs

## Multi-Command Sessions

You can run multiple commands in one session. The CLI maintains engine state across commands:

```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":2000,"iterations_per_node":20}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
```

## Response Format

All responses are JSON with these fields:

**Success:**
```json
{
  "status": "success",
  "command": "run_mission",
  "execution_time_ms": 15.19,
  "result": {
    "steps_completed": 2000,
    "total_operations": 40960000.0
  }
}
```

**Error:**
```json
{
  "status": "error",
  "command": "run_mission",
  "error": "Mission execution failed",
  "error_code": "EXECUTION_FAILED",
  "execution_time_ms": 0.009
}
```

## Performance

Typical performance metrics:
- **0.18-0.33 ns/op**
- **3-5 billion operations/second**
- **50,000-85,000x speedup vs baseline**

## Example Session

```bash
$ cat mission.json | dase_cli.exe
{"command":"create_engine","execution_time_ms":0.093,"result":{"engine_id":"engine_001","engine_type":"phase4b","num_nodes":2048},"status":"success"}
{"command":"run_mission","execution_time_ms":15.19,"result":{"steps_completed":2000,"total_operations":40960000.0},"status":"success"}
{"command":"get_metrics","execution_time_ms":0.012,"result":{"engine_type":"phase4b","ns_per_op":0.183,"ops_per_sec":5454969202.6,"total_operations":81920000},"status":"success"}
```

## Converting Pretty-Printed JSON

If you have a pretty-printed (multi-line) JSON file, use the minify tool:

```bash
python minify_json.py mission_pretty.json mission_minified.json
```

Or manually convert to single-line format. For example:

**❌ Won't work (pretty-printed):**
```json
{
  "command": "create_engine",
  "params": {
    "engine_type": "phase4b",
    "num_nodes": 2048
  }
}
```

**✅ Will work (single line):**
```json
{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":2048}}
```

## Working Examples

See `examples.json` for a complete set of working examples covering all commands.

**Phase 4B Engine (AVX2 optimized):**
```bash
type mission_short_corrected.json | dase_cli.exe
```

**IGSOA Complex Engine:**
```bash
type mission_igsoa_complex.json | dase_cli.exe
```

## Troubleshooting

### "Missing 'command' field" error
- Check that JSON is valid and on a single line
- Windows `echo` adds quotes - use `type` or batch files instead

### "JSON parse error"
- Remove pretty-printing - each command must be on one line
- Use `python minify_json.py input.json output.json` to convert
- Validate JSON syntax at jsonlint.com

### Engine not found
- Make sure to use the `engine_id` returned from `create_engine`
- Each CLI invocation is a separate session - engines don't persist between runs
- Use multiple commands in one file to maintain state

### Segfault on exit
- This is a known issue that happens after all commands complete successfully
- It doesn't affect functionality - all your data is processed correctly
- To hide it: redirect stderr with `2>/dev/null` (bash) or `2>nul` (cmd)

### "The system cannot find the file specified"
- Check that you're in the correct directory: `cd dase_cli`
- Use full paths or `.\dase_cli.exe` (with dot-slash)
- Verify file exists with `dir mission_*.json`
