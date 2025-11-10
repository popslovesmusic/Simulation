# Mission Generator - Quick Reference Guide

## Overview

The Mission Generator creates properly formatted mission files for `dase_cli.exe` in **newline-delimited JSON format** (one command per line).

## Quick Start

```bash
# Generate a Gaussian pulse mission
python tools/mission_generator.py --template gaussian --rc 0.5 --output missions/test.json

# Run it
cat missions/test.json | dase_cli/dase_cli.exe
```

## Usage Examples

### 1. Basic Templates

```bash
# Gaussian pulse (default)
python tools/mission_generator.py --template gaussian --rc 0.5 --output missions/gaussian.json

# Soliton
python tools/mission_generator.py --template soliton --rc 1.0 --output missions/soliton.json

# Plane wave
python tools/mission_generator.py --template plane_wave --rc 0.5 --output missions/wave.json

# 2D Gaussian
python tools/mission_generator.py --template 2d_gaussian --output missions/2d_test.json
```

### 2. Custom Parameters

```bash
# Custom Gaussian with specific parameters
python tools/mission_generator.py \
  --template gaussian \
  --rc 0.75 \
  --nodes 8192 \
  --steps 100 \
  --amplitude 2.0 \
  --width 512 \
  --center 4096 \
  --output missions/custom.json
```

### 3. R_c Parameter Sweep

Generate multiple missions sweeping R_c from 0.1 to 2.0:

```bash
# Generate 5 missions with R_c = [0.1, 0.55, 1.0, 1.45, 2.0]
python tools/mission_generator.py \
  --rc-sweep 0.1 2.0 5 \
  --output missions/rc_sweep/

# Run all missions
for f in missions/rc_sweep/*.json; do
  cat $f | dase_cli/dase_cli.exe > ${f%.json}_output.json
done
```

### 4. Interactive Mode

```bash
python tools/mission_generator.py --interactive
```

This will guide you through creating a mission with prompts:
```
Engine Configuration:
  Engine type [igsoa_complex]:
  Number of nodes [4096]: 8192
  R_c value [0.5]: 0.75

Initial State:
  1. Gaussian
  2. Soliton
  3. Plane wave
  Choice [1]: 1

...
```

## Command-Line Options

### Templates
- `--template`, `-t` : Template type
  - `gaussian` - Gaussian pulse (default)
  - `soliton` - Soliton propagation
  - `plane_wave` - Plane wave
  - `2d_gaussian` - 2D Gaussian

### Engine Parameters
- `--rc` : R_c value (default: 0.5)
- `--nodes`, `-n` : Number of nodes (default: 4096)
- `--steps`, `-s` : Number of simulation steps (default: 50)

### Initial State Parameters
- `--amplitude`, `-a` : Initial amplitude (default: 1.5)
- `--width`, `-w` : Width parameter (default: 256)
- `--center`, `-c` : Center node (default: N/2)

### Output
- `--output`, `-o` : Output file path

### Special Modes
- `--interactive`, `-i` : Interactive mode
- `--rc-sweep MIN MAX POINTS` : Generate R_c sweep

## Available Templates

### Gaussian Pulse
```bash
python tools/mission_generator.py --template gaussian --rc 0.5
```

**Parameters:**
- `amplitude`: Gaussian amplitude (default: 1.5)
- `width`: Gaussian width (default: 256)
- `center`: Center position (default: N/2)

**Commands generated:**
1. `create_engine` (with include_psi: true)
2. `set_igsoa_state` (profile_type: gaussian)
3. `run_mission` (50 steps, 30 iterations/node)
4. `get_state`
5. `destroy_engine`

### Soliton
```bash
python tools/mission_generator.py --template soliton --rc 1.0
```

**Parameters:**
- `amplitude`: Soliton amplitude (default: 1.0)
- `width`: Soliton width (default: 100)
- `center`: Center position (default: N/2)

**Uses:** 100 steps, 50 iterations/node (longer for stability)

### Plane Wave
```bash
python tools/mission_generator.py --template plane_wave --rc 0.5
```

**Parameters:**
- `amplitude`: Wave amplitude (default: 1.0)
- `wavelength`: Wavelength (default: 512) - use `--width` parameter

### 2D Gaussian
```bash
python tools/mission_generator.py --template 2d_gaussian
```

**Parameters:**
- Automatically calculates N_x, N_y from `--nodes` (assumes square: N_x = N_y = √nodes)
- Uses engine_type: `igsoa_complex_2d`

## Output Format

Generated files are in **newline-delimited JSON** format:

```json
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":4096,"R_c":0.5,"include_psi":true}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.5,"center_node":2048,"width":256}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":50,"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
```

**Key points:**
- ✅ One JSON object per line
- ✅ No pretty-printing
- ✅ No JSON arrays
- ✅ Compatible with `dase_cli.exe` stdin

## Programmatic Usage

You can also use the MissionGenerator class in your own Python scripts:

```python
from tools.mission_generator import MissionGenerator

# Create a mission
mission = MissionGenerator()
mission.create_engine(num_nodes=4096, R_c=0.5, include_psi=True)
mission.set_gaussian_state(amplitude=1.5, center_node=2048, width=256)
mission.run_mission(num_steps=50, iterations_per_node=30)
mission.get_state()
mission.destroy_engine()

# Save it
mission.save(Path("missions/my_mission.json"))

# Or get as string
json_lines = mission.to_json_lines()
print(json_lines)
```

## Running Generated Missions

### Single Mission
```bash
# Generate
python tools/mission_generator.py --template gaussian --output missions/test.json

# Run
cat missions/test.json | dase_cli/dase_cli.exe > missions/test_output.json

# Analyze
python analysis/analyze_igsoa_state.py missions/test_output.json 0.5
```

### Batch Processing (R_c Sweep)
```bash
# Generate sweep
python tools/mission_generator.py --rc-sweep 0.1 2.0 5 --output missions/rc_sweep/

# Run all
for f in missions/rc_sweep/mission_*.json; do
  echo "Running $f..."
  cat $f | dase_cli/dase_cli.exe > ${f%.json}_output.json
done

# Analyze all
for f in missions/rc_sweep/*_output.json; do
  rc=$(echo $f | grep -oP 'rc_\K[0-9.]+')
  python analysis/analyze_igsoa_state.py $f $rc --output-dir results/rc_sweep/
done
```

## Integration with Gemini CLI

Since you're using Gemini CLI to design missions, you can now ask it to generate parameters and use this tool:

**Gemini Prompt:**
```
Design a mission for IGSOA simulation to study soliton collision:
- Two solitons with different amplitudes
- First soliton: amplitude 1.2, centered at node 1024
- Second soliton: amplitude 0.8, centered at node 3072
- R_c = 1.0, 4096 nodes, 200 steps

Output the parameters I should pass to mission_generator.py
```

Then use Gemini's output:
```bash
python tools/mission_generator.py \
  --template soliton \
  --rc 1.0 \
  --nodes 4096 \
  --steps 200 \
  --amplitude 1.2 \
  --center 1024 \
  --output missions/soliton_collision.json

# Then manually edit to add second soliton...
```

## Troubleshooting

### "JSON parse error" when running mission
- **Cause:** Mission file has incorrect format (JSON array instead of newline-delimited)
- **Solution:** Regenerate with mission_generator.py

### "Unknown command" error
- **Cause:** Command name typo or unsupported command
- **Solution:** Check template source code for exact command names

### Mission runs but no psi data in output
- **Cause:** `include_psi: false` in create_engine
- **Solution:** Regenerate - all templates set `include_psi: true` by default

### No output file created
- **Cause:** Output directory doesn't exist
- **Solution:** mission_generator.py creates directories automatically, but check permissions

## Tips

1. **Start with templates** - Modify templates rather than building from scratch
2. **Use --interactive** for one-off missions
3. **Use --rc-sweep** for parameter studies
4. **Save to missions/** directory for organization
5. **Use descriptive filenames** like `mission_gaussian_rc0.5_N8192.json`
6. **Pipe output directly** to analysis: `cat mission.json | dase_cli/dase_cli.exe | python analysis/analyze_igsoa_state.py - 0.5`

## Examples Gallery

### Study R_c Dependence
```bash
# Generate 10 missions from R_c=0.1 to 2.0
python tools/mission_generator.py --rc-sweep 0.1 2.0 10 --output missions/rc_study/

# Run all
for f in missions/rc_study/*.json; do
  cat $f | dase_cli/dase_cli.exe > ${f%.json}_output.json
done

# Batch analyze
python analysis/batch_analyze_rc.py missions/rc_study/ --output results/rc_study/
```

### High-Resolution Simulation
```bash
python tools/mission_generator.py \
  --template gaussian \
  --nodes 16384 \
  --steps 200 \
  --width 512 \
  --amplitude 2.0 \
  --output missions/hires_gaussian.json
```

### Quick Test
```bash
# Fast test mission (small, few steps)
python tools/mission_generator.py \
  --nodes 256 \
  --steps 10 \
  --output missions/quick_test.json

cat missions/quick_test.json | dase_cli/dase_cli.exe
```

---

**Created:** November 2025
**Tool:** `tools/mission_generator.py`
**Status:** Production Ready
