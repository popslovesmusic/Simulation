import json
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def load_and_plot_phi(json_file_path):
    """
    Loads Phi field data from a dase_cli output file and plots the spatial profile.
    
    The script assumes the JSON file contains the direct output of a get_state command.
    """
    if not os.path.exists(json_file_path):
        print(f"Error: Output file not found: {json_file_path}")
        print("Please ensure you ran the CLI mission with the 'output_file' parameter.")
        sys.exit(1)

    print(f"Loading data from {json_file_path}...")
    
    try:
        # Load the file content
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # The 'get_state' result contains the extracted fields
        if 'phi' not in data or 'num_nodes' not in data:
            print("Error: JSON file does not contain expected 'phi' or 'num_nodes' fields.")
            sys.exit(1)

        phi = np.array(data['phi'])
        num_nodes = data['num_nodes']
        
        if len(phi) != num_nodes:
             print("Error: Node count mismatch in data.")
             sys.exit(1)

        print(f"Data loaded successfully (N={num_nodes}).")

        # --- Plotting ---
        x = np.arange(num_nodes)
        
        plt.figure(figsize=(12, 6))
        plt.plot(x, phi, label='Realized Field Phi(x)\\Phi(x)Phi(x)', color='#4CAF50', linewidth=1.5)
        
        # Highlight the Gaussian parameters used for initialization
        center_node = 2048
        width = 256
        amplitude = 1.5
        
        # Annotations for SATP context
        plt.axvline(center_node, color='r', linestyle='--', alpha=0.6, label='Injected Gaussian Center')
        plt.axhline(np.mean(phi), color='k', linestyle=':', alpha=0.6, label='Mean Phi\\PhiPhi (Baseline)')
        
        plt.title('SATP 1D Simulation: Initial Field Profile Phi\\PhiPhi at t=500t=500t=500', fontsize=16)
        plt.xlabel('Lattice Site xxx (Node Index)', fontsize=14)
        plt.ylabel('Realized Field Phi=ln(Omega)\\Phi = \\ln(\\Omega)Phi=ln(Omega)', fontsize=14)
        plt.xlim(center_node - 3*width, center_node + 3*width)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        output_image = 'satp_gaussian_profile.png'
        plt.savefig(output_image, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n✅ Plot saved to {output_image}")
        print("You can now inspect the Gaussian profile used to generate the warp bubble!")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # The file name matches the one used in satp_gaussian_save.json
    load_and_plot_phi("satp_t500_state.json")