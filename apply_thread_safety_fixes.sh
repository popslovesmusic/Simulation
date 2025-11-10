#!/bin/bash

echo "Applying thread safety fixes..."

# Backup files first
cp src/cpp/analog_universal_node_engine_avx2.h src/cpp/analog_universal_node_engine_avx2.h.backup
cp src/cpp/analog_universal_node_engine_avx2.cpp src/cpp/analog_universal_node_engine_avx2.cpp.backup

echo "Step 1: Adding metrics_ member to AnalogCellularEngineAVX2 class..."

# Add metrics_ member after noise_level in the header
sed -i '/double noise_level;/a\
\
    // FIX C2.1: Per-instance metrics instead of global static\
    // This prevents data races when multiple engines run concurrently\
    EngineMetrics metrics_;' src/cpp/analog_universal_node_engine_avx2.h

echo "Step 2: Removing global g_metrics and updating FFTW cache..."

# Remove the global metrics line and update FFTW destructor
sed -i '
# Remove global metrics
/^\/\/ Global metrics instance/,/^static EngineMetrics g_metrics;/d

# Update FFTW destructor to add lock
/~FFTWPlanCache() {/,/^    }$/ {
    /~FFTWPlanCache() {/ {
        a\        \/\/ FIX C2.2: Lock during destruction to prevent use-after-free\
        std::lock_guard<std::mutex> lock(cache_mutex);
    }
    /fftw_destroy_plan.*forward/ {
        s/fftw_destroy_plan(pair.second.forward);/if (pair.second.forward) fftw_destroy_plan(pair.second.forward);/
    }
    /fftw_destroy_plan.*inverse/ {
        s/fftw_destroy_plan(pair.second.inverse);/if (pair.second.inverse) fftw_destroy_plan(pair.second.inverse);/
    }
}
' src/cpp/analog_universal_node_engine_avx2.cpp

echo "Step 3: Replacing g_metrics with metrics_ in engine methods..."

# Replace g_metrics with metrics_ in all engine methods
sed -i 's/g_metrics\.reset()/metrics_.reset()/g' src/cpp/analog_universal_node_engine_avx2.cpp
sed -i 's/g_metrics\.total_execution_time_ns/metrics_.total_execution_time_ns/g' src/cpp/analog_universal_node_engine_avx2.cpp
sed -i 's/g_metrics\.total_operations/metrics_.total_operations/g' src/cpp/analog_universal_node_engine_avx2.cpp
sed -i 's/g_metrics\.node_processes/metrics_.node_processes/g' src/cpp/analog_universal_node_engine_avx2.cpp
sed -i 's/g_metrics\.update_performance()/metrics_.update_performance()/g' src/cpp/analog_universal_node_engine_avx2.cpp
sed -i 's/g_metrics\.print_metrics()/metrics_.print_metrics()/g' src/cpp/analog_universal_node_engine_avx2.cpp

echo "Done! Thread safety fixes applied."
echo "Backups saved as *.backup"

