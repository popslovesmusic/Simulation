# IGSOA 3D Engine Implementation Report

The three-dimensional IGSOA lattice extends the previously delivered 1D and 2D
engines into a toroidal volume.  Development was executed in three explicit
stages so downstream teams can audit the transition from core physics to CLI
exposure and validation.

## Stage 1 – Core Physics and Data Structures

* Added `IGSOAPhysics3D` to generalize the non-local coupling kernel to a
  spherical neighborhood with periodic wrapping across all axes.
* Introduced `IGSOAComplexEngine3D` to manage a row-major `(x, y, z)` lattice
  with time stepping, metrics, and cache-friendly memory layout.
* Delivered `IGSOAStateInit3D` helpers for Gaussian, spherical Gaussian,
  plane-wave, uniform, and random initialization profiles plus center-of-mass
  utilities.

## Stage 2 – CLI and Engine Manager Integration

* Extended the CLI engine manager to construct, track, and destroy
  `igsoa_complex_3d` instances, including 3D-aware state setters, getters, and
  center-of-mass calculation.
* Updated the JSON command router so `create_engine`, `set_igsoa_state`,
  `get_state`, and `get_center_of_mass` recognize and surface three-dimensional
  metadata (`N_x`, `N_y`, `N_z`, `z_cm`).
* Refreshed the usage guide and architecture notes with new command examples
  and parameter schemas.

## Stage 3 – Validation and Operational Checks

* Added `tests/test_igsoa_3d.cpp`, a regression that seeds a spherical Gaussian
  packet, advances several steps, and asserts bounded drift in `(x, y, z)`.
* Documented the full 3D lifecycle (creation, initialization, mission run,
  analysis) so operators can reproduce local runs using the CLI and state export
  tools.
* Confirmed the 3D metrics plumbing by reusing the existing instrumentation in
  the engine manager.

## Running the 3D Regression Test

```bash
g++ -std=c++17 -I src/cpp -O2 tests/test_igsoa_3d.cpp -o build/tests/test_igsoa_3d
./build/tests/test_igsoa_3d
```

(Add `-lfftw3` if you link against the dynamic library elsewhere.  The
regression prints the initial/final center of mass and exits with status code 1
if the packet drifts more than ~0.75 lattice units.)

## CLI Quick Reference

1. Create a 3D lattice:
   ```json
   {"command":"create_engine","params":{"engine_type":"igsoa_complex_3d","N_x":32,"N_y":32,"N_z":32,"R_c":3.0,"kappa":1.0,"gamma":0.1,"dt":0.01}}
   ```
2. Seed a spherical Gaussian:
   ```json
   {"command":"set_igsoa_state","params":{"engine_id":"engine_003","profile_type":"spherical_gaussian","params":{"amplitude":1.0,"center_x":16.0,"center_y":16.0,"center_z":16.0,"sigma":6.0}}}
   ```
3. Evolve and inspect drift:
   ```json
   {"command":"run_mission","params":{"engine_id":"engine_003","num_steps":4096,"iterations_per_node":20}}
   {"command":"get_center_of_mass","params":{"engine_id":"engine_003"}}
   ```

For full context on initialization modes and analysis tooling, pair this report
with the updated `dase_cli/USAGE.md` and `tools/analyze_igsoa_2d.py`
capabilities.  A 3D spectral analyzer can be layered on later if needed; the
current export path is sufficient for offline processing via Python or MATLAB.
