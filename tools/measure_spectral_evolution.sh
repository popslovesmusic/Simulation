#!/bin/bash
# Spectral Evolution Measurement Tool
# Captures state at fine time intervals to measure spectral cutoff dynamics
#
# Usage: ./measure_spectral_evolution.sh

set -e

# Configuration
AMPLITUDE=100.0
R_C=1.0
CENTER=2048
WIDTH=256
NUM_NODES=4096
ITERATIONS_PER_NODE=30

# Time points to sample (fine resolution for spectral decay)
TIMESTEPS=(1 2 3 5 10 20)

# Output directory
OUTPUT_DIR="spectral_evolution_study"
mkdir -p "${OUTPUT_DIR}"

echo "======================================================================="
echo "SPECTRAL EVOLUTION MEASUREMENT"
echo "======================================================================="
echo "Amplitude: ${AMPLITUDE}"
echo "R_c: ${R_C}"
echo "Timesteps: ${TIMESTEPS[@]}"
echo "Output: ${OUTPUT_DIR}/"
echo "======================================================================="
echo

cd dase_cli || { echo "Error: dase_cli directory not found"; exit 1; }

# Run simulation for each timestep
for T in "${TIMESTEPS[@]}"; do
    echo "=== Running T=${T} timesteps ==="

    # Create test configuration
    cat > "${OUTPUT_DIR}/test_t${T}.json" <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":${NUM_NODES},"R_c":${R_C}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":${AMPLITUDE},"center_node":${CENTER},"width":${WIDTH},"baseline_phi":0.0,"mode":"blend","beta":1.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":${T},"iterations_per_node":${ITERATIONS_PER_NODE}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

    # Run simulation
    cat "${OUTPUT_DIR}/test_t${T}.json" | ./dase_cli.exe > "${OUTPUT_DIR}/output_t${T}.json" 2>&1

    echo "  Simulation complete"

    # Run analysis
    cd ..
    python analyze_igsoa_state.py "dase_cli/${OUTPUT_DIR}/output_t${T}.json" ${R_C} \
        --output-dir "dase_cli/${OUTPUT_DIR}/analysis_t${T}" 2>&1 | grep -v "findfont"
    cd dase_cli

    echo "  Analysis complete"
    echo
done

echo "======================================================================="
echo "SPECTRAL EVOLUTION COMPLETE"
echo "======================================================================="
echo
echo "Output files in: ${OUTPUT_DIR}/"
echo
echo "Next steps:"
echo "1. Extract spectral peaks from each analysis_t*/analysis_report_*.txt"
echo "2. Plot |Phi_hat(k)|^2 vs time for specific k values"
echo "3. Fit exponential decay: |Phi_hat(k,t)| ~ exp(-gamma_k * t)"
echo "4. Check if gamma_k increases with k (spectral cutoff signature)"
echo

cd ..
