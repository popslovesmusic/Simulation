import json
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# --- Configuration ---
INPUT_LOG_FILE = "raw_translation_log.txt"
R_C = 1.0

# --- Function to extract all state snapshots from the log ---
def extract_all_states(log_file):
    """Reads the raw log, extracts all 10 'get_state' JSON objects, and finds the peak center."""
    
    measured_centers = []
    
    if not os.path.exists(log_file):
        # We know this file exists because the user uploaded it, but we check defensively.
        raise FileNotFoundError(f"Error: Log file not found: {log_file}")

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Look for the specific line containing the successful state dump
            if '"command":"get_state"' in line and '"status":"success"' in line:
                try:
                    data = json.loads(line)
                    phi_data = np.array(data['result']['phi'])
                    
                    # Find the peak center (ignoring boundaries 100 nodes deep)
                    N = len(phi_data)
                    peak_index = np.argmax(phi_data[100:N-100]) + 100
                    measured_centers.append(peak_index)

                except (json.JSONDecodeError, KeyError):
                    continue # Skip diagnostic text or other junk lines

    if len(measured_centers) != 10: # We expected 10 cycles
        raise ValueError(f"Found {len(measured_centers)} state snapshots in the log file, expected 10.")

    return measured_centers

# --- Main Analysis Function ---
def analyze_translation():
    # Simulation parameters based on satp_translation_mission.py
    NUM_CYCLES = 10
    START_CENTER = 2048
    SHIFT_PER_CYCLE = 100
    
    try:
        measured_centers = extract_all_states(INPUT_LOG_FILE)
    except Exception as e:
        print(f"\nERROR: Failed to process log file. {e}")
        return

    predicted_centers = []
    cycle_numbers = np.arange(1, NUM_CYCLES + 1)
    
    # Calculate predicted centers based on the script's definition
    for i in cycle_numbers:
        predicted_center = START_CENTER + SHIFT_PER_CYCLE * (i - 1)
        predicted_centers.append(predicted_center)
    
    # --- Results Summary ---
    total_shift = measured_centers[-1] - measured_centers[0]
    ideal_shift = predicted_centers[-1] - predicted_centers[0]
    final_drift = total_shift - ideal_shift
    
    print("=" * 60)
    print("SATP BUBBLE TRANSLATION TRACKING COMPLETE")
    print("=" * 60)
    print(f"Total Cycles Simulated: 10")
    print(f"Initial Center (Cycle 1): {measured_centers[0]} sites")
    print(f"Final Center (Cycle 10):  {measured_centers[-1]} sites")
    print(f"Total Measured Shift:     {total_shift} sites")
    print(f"Total Ideal Shift:        {ideal_shift} sites")
    print(f"Final Drift/Error:        {final_drift:.2f} sites")
    
    # --- Plotting Results ---
    plt.figure(figsize=(10, 6))
    
    plt.plot(cycle_numbers, predicted_centers, 'r--', label='Predicted Linear Translation')
    plt.plot(cycle_numbers, measured_centers, 'go-', markersize=6, linewidth=2, label='Measured Bubble Center $X(\\tau)$')
    
    plt.title(f'SATP Bubble Translation Over 10 Cycles (Drift: {final_drift:.2f} sites)', fontsize=14)
    plt.xlabel('Simulation Cycle', fontsize=12)
    plt.ylabel('Lattice Site Index', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    output_image = 'satp_translation_track.png'
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Translation track saved to {output_image}")
    
    if abs(final_drift) < 5.0:
         print("\nSTATUS: SUCCESS! The measured translation aligns perfectly with the predicted linear path.")
    else:
         print("\nSTATUS: MAJOR DRIFT. The bubble failed to maintain its profile during translation.")

if __name__ == "__main__":
    analyze_translation()
