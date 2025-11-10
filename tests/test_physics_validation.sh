#!/bin/bash
# IGSOA Physics Validation Test Suite
# Automated regression testing for SATP predictions
#
# Usage: ./test_physics_validation.sh

set -e

# Configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$TEST_DIR")"
CLI_DIR="${ROOT_DIR}/dase_cli"

# Test parameters
NUM_NODES=4096
R_C=1.0
AMPLITUDE=100.0
CENTER=2048
WIDTH=256
TIMESTEP=1

# Thresholds
DRIFT_THRESHOLD_PCT=1.0  # 1% of N
XI_RC_MIN=0.8
XI_RC_MAX=1.2
NORM_TOLERANCE=1e-6

# Colors for output
RED='\033[0.31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

echo "======================================================================="
echo "IGSOA PHYSICS VALIDATION TEST SUITE"
echo "======================================================================="
echo "Test directory: ${TEST_DIR}"
echo "CLI directory: ${CLI_DIR}"
echo "======================================================================="
echo

# Function to print test result
print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}[PASS]${NC} ${test_name}"
        echo "       ${message}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}[FAIL]${NC} ${test_name}"
        echo "       ${message}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo
}

# Change to CLI directory
cd "${CLI_DIR}" || { echo "Error: Cannot find dase_cli directory"; exit 1; }

# Check if dase_cli.exe exists
if [ ! -f "dase_cli.exe" ]; then
    echo "Error: dase_cli.exe not found. Please build first."
    exit 1
fi

echo "-----------------------------------------------------------------------"
echo "TEST 1: Zero Drift Validation"
echo "-----------------------------------------------------------------------"

# Create test configuration
cat > test_zero_drift.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":${NUM_NODES},"R_c":${R_C}}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":${AMPLITUDE},"center_node":${CENTER},"width":${WIDTH},"baseline_phi":0.0,"mode":"blend","beta":1.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":${TIMESTEP},"iterations_per_node":30}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

# Run simulation
cat test_zero_drift.json | ./dase_cli.exe > output_zero_drift.json 2>&1

# Run drift analysis
cd "${ROOT_DIR}"
DRIFT_OUTPUT=$(python dase_cli/extract_drift.py dase_cli/output_zero_drift.json ${CENTER} 2>&1 | grep "Absolute drift:")

# Extract drift value (column 3)
DRIFT=$(echo "$DRIFT_OUTPUT" | awk '{print $3}')

# Calculate threshold using Python
THRESHOLD=$(python -c "print(${NUM_NODES} * ${DRIFT_THRESHOLD_PCT} / 100)")

# Compare using Python
PASS_TEST=$(python -c "print('1' if ${DRIFT} < ${THRESHOLD} else '0')")

if [ "$PASS_TEST" = "1" ]; then
    print_result "Zero Drift" "PASS" "Drift = ${DRIFT} nodes < ${THRESHOLD} nodes (${DRIFT_THRESHOLD_PCT}% threshold)"
else
    print_result "Zero Drift" "FAIL" "Drift = ${DRIFT} nodes >= ${THRESHOLD} nodes (exceeds ${DRIFT_THRESHOLD_PCT}% threshold)"
fi

cd "${CLI_DIR}"

echo "-----------------------------------------------------------------------"
echo "TEST 2: Correlation Length Scaling (ξ = R_c)"
echo "-----------------------------------------------------------------------"

# Run analysis
cd "${CLI_DIR}"
python analyze_igsoa_state.py output_zero_drift.json ${R_C} --output-dir test_validation_analysis > /dev/null 2>&1

# Extract ξ/R_c ratio
XI_RC_RATIO=$(grep "Ratio ξ/R_c:" test_validation_analysis/analysis_report_R${R_C}.txt | awk '{print $NF}')

# Check if within range using Python
PASS_TEST=$(python -c "print('1' if ${XI_RC_MIN} <= ${XI_RC_RATIO} <= ${XI_RC_MAX} else '0')")

if [ "$PASS_TEST" = "1" ]; then
    print_result "Correlation Length Scaling" "PASS" "ξ/R_c = ${XI_RC_RATIO} ∈ [${XI_RC_MIN}, ${XI_RC_MAX}]"
else
    print_result "Correlation Length Scaling" "FAIL" "ξ/R_c = ${XI_RC_RATIO} outside range [${XI_RC_MIN}, ${XI_RC_MAX}]"
fi

cd "${CLI_DIR}"

echo "-----------------------------------------------------------------------"
echo "TEST 3: State Normalization"
echo "-----------------------------------------------------------------------"

# Extract normalization from analysis report
NORM_MEAN=$(grep "|Ψ|² mean:" test_validation_analysis/analysis_report_R${R_C}.txt | awk '{print $NF}')

# Check if ≈ 1.0 using Python
NORM_DIFF=$(python -c "print(abs(${NORM_MEAN} - 1.0))")
PASS_TEST=$(python -c "print('1' if ${NORM_DIFF} < ${NORM_TOLERANCE} else '0')")

if [ "$PASS_TEST" = "1" ]; then
    print_result "State Normalization" "PASS" "⟨|Ψ|²⟩ = ${NORM_MEAN} (within ${NORM_TOLERANCE} of 1.0)"
else
    print_result "State Normalization" "FAIL" "⟨|Ψ|²⟩ = ${NORM_MEAN} (deviation ${NORM_DIFF} exceeds ${NORM_TOLERANCE})"
fi

echo "-----------------------------------------------------------------------"
echo "TEST 4: Three-Mode State Initialization"
echo "-----------------------------------------------------------------------"

# Test overwrite mode
cat > test_modes.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"center_node":512,"width":100,"baseline_phi":0.0,"mode":"overwrite"}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":0.5,"center_node":512,"width":50,"baseline_phi":0.0,"mode":"add"}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":2.0,"center_node":512,"width":150,"baseline_phi":0.0,"mode":"blend","beta":0.3}}}
{"command":"get_state","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

MODE_OUTPUT=$(cat test_modes.json | ./dase_cli.exe 2>&1)

# Count successful set_igsoa_state commands
MODE_SUCCESS_COUNT=$(echo "$MODE_OUTPUT" | grep '"command":"set_igsoa_state"' | grep '"status":"success"' | wc -l)

if [ "$MODE_SUCCESS_COUNT" -eq 3 ]; then
    print_result "Three-Mode Initialization" "PASS" "All 3 modes (overwrite/add/blend) functional"
else
    print_result "Three-Mode Initialization" "FAIL" "Only ${MODE_SUCCESS_COUNT}/3 modes succeeded"
fi

echo "-----------------------------------------------------------------------"
echo "TEST 5: Snapshot Feature"
echo "-----------------------------------------------------------------------"

# Test run_mission_with_snapshots
cat > test_snapshots_validation.json <<EOF
{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":1024,"R_c":1.0}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":10.0,"center_node":512,"width":100,"baseline_phi":0.0,"mode":"blend","beta":1.0}}}
{"command":"run_mission_with_snapshots","params":{"engine_id":"engine_001","num_steps":6,"iterations_per_node":30,"snapshot_interval":2}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}
EOF

SNAPSHOT_OUTPUT=$(cat test_snapshots_validation.json | ./dase_cli.exe 2>&1)

# Check if snapshots were captured
SNAPSHOT_COUNT=$(echo "$SNAPSHOT_OUTPUT" | grep '"snapshot_count"' | sed 's/.*"snapshot_count":\([0-9]*\).*/\1/')

if [ "$SNAPSHOT_COUNT" -eq 3 ]; then
    print_result "Snapshot Feature" "PASS" "Captured ${SNAPSHOT_COUNT} snapshots (expected 3 for 6 steps with interval 2)"
else
    print_result "Snapshot Feature" "FAIL" "Captured ${SNAPSHOT_COUNT} snapshots (expected 3)"
fi

echo "======================================================================="
echo "TEST SUMMARY"
echo "======================================================================="
echo -e "Tests passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests failed: ${RED}${TESTS_FAILED}${NC}"
echo "Total tests:  $((TESTS_PASSED + TESTS_FAILED))"
echo "======================================================================="

# Cleanup
rm -f test_zero_drift.json output_zero_drift.json
rm -f test_modes.json
rm -f test_snapshots_validation.json
rm -rf test_validation_analysis

# Exit with error code if any tests failed
if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}VALIDATION FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi
