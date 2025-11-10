#!/bin/bash
# Engine Test Suite - Tests all working engines with mission execution

echo "=== DASE Engine Test Suite ==="
echo ""

# Test 1: Phase 4B Engine
echo "Test 1: Phase 4B Engine (Real-valued analog)"
echo '{"command":"create_engine","params":{"engine_type":"phase4b","num_nodes":256}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":100,"iterations_per_node":10}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}' | ./dase_cli/dase_cli.exe 2>&1 | grep -E "status|ns_per_op|ops_per_second"
echo ""

# Test 2: IGSOA Complex Engine
echo "Test 2: IGSOA Complex Engine (Quantum-inspired)"
echo '{"command":"create_engine","params":{"engine_type":"igsoa_complex","num_nodes":512,"R_c":2.5,"kappa":1.0,"gamma":0.1}}
{"command":"set_igsoa_state","params":{"engine_id":"engine_001","profile_type":"gaussian","params":{"amplitude":1.0,"sigma":5.0}}}
{"command":"run_mission","params":{"engine_id":"engine_001","num_steps":50,"iterations_per_node":15}}
{"command":"get_metrics","params":{"engine_id":"engine_001"}}
{"command":"destroy_engine","params":{"engine_id":"engine_001"}}' | ./dase_cli/dase_cli.exe 2>&1 | grep -E "status|ns_per_op|ops_per_second"
echo ""

echo "=== Test Suite Complete ==="
