import json
import sys

# --- SATP Simulation Parameters (Based on successful A=100.0 test) ---
NUM_NODES = 4096
AMPLITUDE = 100.0  # Confirmed max stable amplitude
WIDTH = 256
BASELINE_PHI = 0.0
R_C = 1.0

# --- Translation Profile Parameters ---
START_CENTER = 2048
SHIFT_PER_CYCLE = 100
NUM_CYCLES = 10
STEPS_PER_CYCLE = 50
ITERATIONS_PER_NODE = 30
OUTPUT_DIR = "satp_translation_results" # Define the directory name

# --- Mission Generation ---

# 1. Create Engine
create_cmd = {"command": "create_engine", "params": {"engine_type": "igsoa_complex", "num_nodes": NUM_NODES, "R_c": R_C}}
sys.stdout.write(json.dumps(create_cmd, separators=(',', ':')) + '\n')

# 2. Sequential Translation Cycles
for i in range(NUM_CYCLES):
    # Calculate the new center for this cycle
    current_center = START_CENTER + SHIFT_PER_CYCLE * i
    cycle_label = i + 1
    
    # 2a. Set State (Updates the Gaussian center for translation)
    set_cmd = {
        "command": "set_igsoa_state",
        "params": {
            "engine_id": "engine_001",
            "profile_type": "gaussian",
            "params": {
                "amplitude": AMPLITUDE,
                "center_node": current_center,
                "width": WIDTH,
                "baseline_phi": BASELINE_PHI
            }
        }
    }
    sys.stdout.write(json.dumps(set_cmd, separators=(',', ':')) + '\n')

    # 2b. Run Mission (Simulate 50 steps of movement)
    run_cmd = {
        "command": "run_mission",
        "params": {
            "engine_id": "engine_001",
            "num_steps": STEPS_PER_CYCLE,
            "iterations_per_node": ITERATIONS_PER_NODE
        }
    }
    sys.stdout.write(json.dumps(run_cmd, separators=(',', ':')) + '\n')

    # 2c. Get State (Extract data for this specific cycle, with correct path)
    output_filename = f"{OUTPUT_DIR}/satp_translation_cycle{cycle_label}.json"
    get_state_cmd = {
        "command": "get_state",
        "params": {
            "engine_id": "engine_001",
            "output_file": output_filename 
        }
    }
    sys.stdout.write(json.dumps(get_state_cmd, separators=(',', ':')) + '\n')

# 3. Destroy Engine
destroy_cmd = {"command": "destroy_engine", "params": {"engine_id": "engine_001"}}
sys.stdout.write(json.dumps(destroy_cmd, separators=(',', ':')) + '\n')

sys.stderr.write(f"\n# Generated mission script: {NUM_CYCLES} translation cycles.")
