import json
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# --- Configuration ---
INPUT_LOG_FILE = "raw_output_max.txt"
R_C = 1.0

def analyze_exotic_cost(log_file):
    """
    Reads the raw log file, extracts the Phi field, computes the spatial 
    gradient (nabla_phi), and plots the exotic energy cost, E_exotic.
    """
    # 1. Extract the Phi field data
    phi_data = None
    if not os.path.exists(log_file):
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '"command":"get_state"' in line and '"status":"success"' in line:
                try:
                    data = json.loads(line)
                    phi_data = np.array(data['result']['phi'])
                    break
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if phi_data is None:
        print(f"Error: Could not find clean 'phi' state data in {log_file}.")
        sys.exit(1)

    N = len(phi_data)
    x = np.arange(N)

    # 2. Compute Spatial Gradient (nabla_phi)
    # We use numpy.gradient to calculate the numerical derivative (dPhi/dx).
    # This gradient squared (nabla_phi^2) is proportional to the spatial part 
    # of the exotic stress-energy T_munu.
    
    nabla_phi = np.gradient(phi_data, x)
    
    # E_exotic (Spatial Component): Proportional to the square of the gradient
    # E_exotic ∝ |∇Φ|²
    exotic_energy_density = nabla_phi**2

    # 3. Find the bubble center and region for plotting
    peak_phi_index = np.argmax(phi_data[100:N-100]) + 100
    width = 256
    
    # --- Plotting the Exotic Cost Profile ---
    plt.figure(figsize=(10, 6))
    
    # Plot the square of the gradient
    plt.plot(x, exotic_energy_density, label='$E_{\\text{exotic}} \\propto |\\nabla\\Phi|^2$', 
             color='#FF4500', linewidth=2)
    
    # Annotate the centerimport json
import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# --- Configuration / dynamic input selection ---
# usage: python analyze_exotic_cost.py raw_translation_log_v2.txt
if len(sys.argv) > 1:
    INPUT_LOG_FILE = sys.argv[1]
else:
    INPUT_LOG_FILE = "raw_output_max.txt"   # legacy default

R_C = 1.0

def analyze_exotic_cost(log_file):
    """
    Reads the raw log file, extracts the Phi field, computes the spatial 
    gradient (nabla_phi), and plots the exotic energy cost, E_exotic.
    """

    # 1. Extract the Phi field data
    phi_data = None
    if not os.path.exists(log_file):
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '"command":"get_state"' in line and '"status":"success"' in line:
                try:
                    data = json.loads(line)
                    phi_data = np.array(data['result']['phi'])
                    break
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if phi_data is None:
        print(f"Error: Could not find clean 'phi' state data in {log_file}.")
        sys.exit(1)

    N = len(phi_data)
    x = np.arange(N)

    # 2. Compute Spatial Gradient (nabla_phi)
    nabla_phi = np.gradient(phi_data, x)
    exotic_energy_density = nabla_phi**2   # E_exotic ∝ |∇Φ|²

    # 3. Find bubble center approx
    peak_phi_index = np.argmax(phi_data[100:N-100]) + 100
    width = 256
    
    # --- Plotting Exotic Cost Profile ---
    plt.figure(figsize=(10, 6))
    plt.plot(x, exotic_energy_density, label='$E_{\\text{exotic}} \\propto |\\nabla\\Phi|^2$', 
             linewidth=2)
    plt.axvline(peak_phi_index, color='k', linestyle=':', alpha=0.7, 
                label=f'Bubble Center ({peak_phi_index})')

    plt.title('Exotic Energy Cost Profile ($A=100.0$ SATP Bubble)', fontsize=14)
    plt.xlabel('Lattice Site $x$', fontsize=12)
    plt.ylabel('Spatial Exotic Energy Density ($|\\nabla\\Phi|^2$)', fontsize=12)

    plt.xlim(peak_phi_index - 3 * width, peak_phi_index + 3 * width)
    plt.legend()
    plt.grid(True, alpha=0.3)

    output_image = 'satp_exotic_cost_profile.png'
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. Quantify Exotic Cost
    total_cost = np.sum(exotic_energy_density)
    max_density = np.max(exotic_energy_density)

    print("=" * 60)
    print("SATP EXOTIC COST ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Log File Processed: {log_file}")
    print(f"Total Integrated Exotic Cost (Energy): {total_cost:.4e} [a.u.]")
    print(f"Maximum Energy Density (|∇Φ|² peak): {max_density:.4e} [a.u.]")
    print(f"Bubble Width (Approximation): {2 * width} sites")
    print(f"\n✅ Exotic cost profile plotted to {output_image}")

if __name__ == "__main__":
    analyze_exotic_cost(INPUT_LOG_FILE)

    