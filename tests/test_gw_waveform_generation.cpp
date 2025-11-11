/**
 * IGSOA GW Engine - Waveform Generation Integration Test
 *
 * This test integrates all components:
 * - SymmetryField (3D grid + evolution)
 * - FractionalSolver (memory dynamics)
 * - BinaryMerger (source terms)
 * - ProjectionOperators (GW strain extraction)
 *
 * Generates the first IGSOA gravitational waveform!
 */

#define _USE_MATH_DEFINES
#include <cmath>
#include "../src/cpp/igsoa_gw_engine/core/symmetry_field.h"
#include "../src/cpp/igsoa_gw_engine/core/fractional_solver.h"
#include "../src/cpp/igsoa_gw_engine/core/source_manager.h"
#include "../src/cpp/igsoa_gw_engine/core/projection_operators.h"
#include "../src/cpp/igsoa_gw_engine/core/echo_generator.h"
#include "../src/cpp/utils/logger.h"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <vector>
#include <chrono>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace dase::igsoa::gw;

// Helper function to export waveform to CSV
void exportWaveformCSV(
    const std::string& filename,
    const std::vector<double>& time,
    const std::vector<double>& h_plus,
    const std::vector<double>& h_cross,
    const std::vector<double>& amplitude)
{
    // Validate inputs
    if (filename.empty()) {
        LOG_ERROR("Export failed: filename cannot be empty");
        throw std::invalid_argument("filename cannot be empty");
    }

    if (time.size() != h_plus.size() || time.size() != h_cross.size() ||
        time.size() != amplitude.size()) {
        LOG_ERROR("Export failed: data vector size mismatch");
        throw std::invalid_argument("All data vectors must have the same size");
    }

    try {
        // Open file
        std::ofstream file(filename);
        if (!file.is_open()) {
            std::string error_msg = "Failed to open file for writing: " + filename +
                                   " (check permissions and disk space)";
            LOG_ERROR(error_msg);
            throw std::runtime_error(error_msg);
        }

        // Set formatting
        file << std::scientific << std::setprecision(12);

        // Write header
        file << "time,h_plus,h_cross,amplitude\n";
        if (!file.good()) {
            std::string error_msg = "Write error while writing header to: " + filename;
            LOG_ERROR(error_msg);
            throw std::runtime_error(error_msg);
        }

        // Write data
        for (size_t i = 0; i < time.size(); i++) {
            file << time[i] << ","
                 << h_plus[i] << ","
                 << h_cross[i] << ","
                 << amplitude[i] << "\n";

            // Check write status periodically
            if (i % 100 == 0 && !file.good()) {
                std::string error_msg = "Write error at row " + std::to_string(i) +
                                       " while exporting to: " + filename +
                                       " (possible disk full)";
                LOG_ERROR(error_msg);
                throw std::runtime_error(error_msg);
            }
        }

        // Final write check
        if (!file.good()) {
            std::string error_msg = "Write error occurred while exporting to: " + filename;
            LOG_ERROR(error_msg);
            throw std::runtime_error(error_msg);
        }

        file.close();

        // Verify close succeeded
        if (file.fail()) {
            LOG_WARNING("Failed to close file properly: " + filename);
        }

        LOG_INFO("Waveform exported successfully: " + filename +
                 " (" + std::to_string(time.size()) + " data points)");
        std::cout << "Exported waveform to: " + filename << std::endl;

    } catch (const std::exception& e) {
        LOG_ERROR("Exception during waveform export: " + std::string(e.what()));
        throw;  // Re-throw for caller to handle
    }
}

// Main integration test
int main(int argc, char** argv) {
    // Initialize logger
    ::igsoa::Logger::getInstance().initialize(
        "gw_waveform_test.log",
        ::igsoa::Logger::Level::INFO,    // Console: INFO and above
        ::igsoa::Logger::Level::DEBUG    // File: DEBUG and above
    );

    std::cout << "========================================" << std::endl;
    std::cout << "IGSOA GW Waveform Generation Test" << std::endl;
    std::cout << "========================================\n" << std::endl;

    // Parse command line arguments (alpha value)
    double alpha_value = 1.5;  // Default
    if (argc > 1) {
        alpha_value = std::atof(argv[1]);
        std::cout << "Using alpha = " << alpha_value << " (from command line)" << std::endl;
    } else {
        std::cout << "Using alpha = " << alpha_value << " (default)" << std::endl;
    }

    // ========================================================================
    // 1. Configure Simulation
    // ========================================================================

    std::cout << "\n=== Configuration ===" << std::endl;

    // Field configuration (small grid for fast testing)
    SymmetryFieldConfig field_config;
    field_config.nx = 32;
    field_config.ny = 32;
    field_config.nz = 32;
    field_config.dx = 2000.0;  // 2 km resolution
    field_config.dy = 2000.0;
    field_config.dz = 2000.0;
    field_config.dt = 0.001;   // 1 ms timestep

    std::cout << "Grid size: " << field_config.nx << "x"
              << field_config.ny << "x" << field_config.nz << std::endl;
    std::cout << "Resolution: " << field_config.dx / 1e3 << " km" << std::endl;
    std::cout << "Timestep: " << field_config.dt * 1000 << " ms" << std::endl;

    // Fractional solver configuration
    FractionalSolverConfig frac_config;
    frac_config.T_max = 1.0;       // 1 second simulation
    frac_config.soe_rank = 12;
    frac_config.alpha_min = alpha_value;
    frac_config.alpha_max = alpha_value;  // Fixed alpha for now

    std::cout << "Fractional memory: alpha = " << alpha_value << std::endl;
    std::cout << "SOE rank: " << frac_config.soe_rank << std::endl;

    // Binary merger configuration
    BinaryMergerConfig merger_config;
    merger_config.mass1 = 30.0;  // 30 solar masses
    merger_config.mass2 = 30.0;
    merger_config.initial_separation = 150e3;  // 150 km
    merger_config.gaussian_width = 10e3;       // 10 km
    merger_config.source_amplitude = 100.0;    // Much stronger amplitude for detectable signal
    merger_config.enable_inspiral = true;      // Enable GW-driven inspiral!
    merger_config.center = Vector3D(
        field_config.nx * field_config.dx / 2,
        field_config.ny * field_config.dy / 2,
        field_config.nz * field_config.dz / 2
    );

    std::cout << "Binary: " << merger_config.mass1 << " + " << merger_config.mass2 << " M☉" << std::endl;
    std::cout << "Separation: " << merger_config.initial_separation / 1e3 << " km" << std::endl;

    // Echo generator configuration
    EchoConfig echo_config;
    echo_config.fundamental_timescale = 0.001;  // 1 ms base echo delay
    echo_config.max_primes = 30;                 // First 30 echoes
    echo_config.echo_amplitude_base = 0.15;      // 15% of merger amplitude
    echo_config.echo_amplitude_decay = 10.0;     // Decay rate
    echo_config.echo_frequency_shift = 10.0;     // 10 Hz per echo
    echo_config.echo_gaussian_width = 10e3;      // 10 km spatial extent
    echo_config.auto_detect_merger = true;       // Enable automatic merger detection
    echo_config.merger_detection_threshold = 10.0; // Energy threshold (field ~14 peak)

    std::cout << "Echo generation: " << echo_config.max_primes << " echoes scheduled" << std::endl;
    std::cout << "Echo timescale: " << echo_config.fundamental_timescale * 1000 << " ms" << std::endl;

    // Simulation parameters
    int num_steps = 5000;  // 5 seconds - enough for merger + echoes!
    int output_interval = 10;  // Output every 10 steps

    std::cout << "Total steps: " << num_steps << std::endl;
    std::cout << "Duration: " << num_steps * field_config.dt << " seconds" << std::endl;

    // ========================================================================
    // 2. Initialize Components
    // ========================================================================

    std::cout << "\n=== Initialization ===" << std::endl;

    auto init_start = std::chrono::high_resolution_clock::now();

    SymmetryField field(field_config);
    std::cout << "✓ SymmetryField created (" << field.getTotalPoints() << " points)" << std::endl;

    FractionalSolver solver(frac_config, field.getTotalPoints());
    std::cout << "✓ FractionalSolver created (memory usage: "
              << solver.getMemoryUsage() / 1024.0 / 1024.0 << " MB)" << std::endl;

    BinaryMerger merger(merger_config);
    std::cout << "✓ BinaryMerger created" << std::endl;
    merger.printState();

    // Configure projection (observer at distance)
    ProjectionConfig proj_config;
    proj_config.observer_position = Vector3D(
        field_config.nx * field_config.dx * 0.75,  // 48 km (off-center X for asymmetry!)
        field_config.ny * field_config.dy * 0.75,  // 48 km (off-center Y)
        field_config.nz * field_config.dz * 0.75   // 48 km (3/4 up grid, INSIDE domain)
    );
    proj_config.detector_normal = Vector3D(0, 0, -1);  // Looking down
    proj_config.detector_distance = field_config.nz * field_config.dz;
    proj_config.gauge = ProjectionConfig::Gauge::TransverseTraceless;

    ProjectionOperators projector(proj_config);
    std::cout << "✓ ProjectionOperators created" << std::endl;

    EchoGenerator echo_generator(echo_config);
    std::cout << "✓ EchoGenerator created (ready for merger detection)" << std::endl;

    // Set uniform alpha field
    for (int i = 0; i < field_config.nx; i++) {
        for (int j = 0; j < field_config.ny; j++) {
            for (int k = 0; k < field_config.nz; k++) {
                field.setAlpha(i, j, k, alpha_value);
            }
        }
    }
    std::cout << "✓ Alpha field initialized to " << alpha_value << std::endl;

    auto init_end = std::chrono::high_resolution_clock::now();
    auto init_duration = std::chrono::duration_cast<std::chrono::milliseconds>(init_end - init_start).count();
    std::cout << "Initialization time: " << init_duration << " ms" << std::endl;

    // ========================================================================
    // 3. Time Evolution Loop
    // ========================================================================

    std::cout << "\n=== Time Evolution ===" << std::endl;

    std::vector<double> time_array;
    std::vector<double> h_plus_array;
    std::vector<double> h_cross_array;
    std::vector<double> amplitude_array;

    bool merger_detected = false;
    double merger_time = 0.0;

    auto evolution_start = std::chrono::high_resolution_clock::now();

    for (int step = 0; step < num_steps; step++) {
        double t = step * field_config.dt;

        // Check for merger detection
        if (!merger_detected && echo_generator.detectMerger(field, t)) {
            merger_detected = true;
            merger_time = t;
            std::cout << "\n*** MERGER DETECTED at t = " << t << " s ***" << std::endl;
            std::cout << "*** ECHO GENERATION ACTIVATED ***\n" << std::endl;
        }

        // Get source terms from binary
        auto sources = merger.computeSourceTerms(field, t);

        // Add echo sources if merger has occurred
        if (merger_detected) {
            Vector3D merger_center = merger_config.center;

            // Add echo contribution at each grid point
            for (int i = 0; i < field_config.nx; i++) {
                for (int j = 0; j < field_config.ny; j++) {
                    for (int k = 0; k < field_config.nz; k++) {
                        Vector3D pos = field.toPosition(i, j, k);
                        int idx = field.toFlatIndex(i, j, k);

                        std::complex<double> echo_source = echo_generator.computeEchoSource(t, pos, merger_center);
                        sources[idx] += echo_source;
                    }
                }
            }
        }

        // Compute fractional derivatives
        auto alpha_values = field.getAlphaValues();
        auto frac_derivs = solver.computeDerivatives(alpha_values);

        // Evolve field one timestep
        field.evolveStep(frac_derivs, sources);

        // Update fractional solver history
        // For now, use simple approximation: second derivative ≈ 0
        // TODO: Compute actual second time derivatives
        std::vector<std::complex<double>> second_derivs(field.getTotalPoints(), std::complex<double>(0.0, 0.0));
        solver.updateHistory(field.getDeltaPhiFlat(), second_derivs, alpha_values, field_config.dt);

        // Evolve binary orbit
        merger.evolveOrbit(field_config.dt);

        // Extract and record strain (every output_interval steps)
        if (step % output_interval == 0) {
            auto strain = projector.compute_strain_at_observer(field);

            time_array.push_back(t);
            h_plus_array.push_back(strain.h_plus);
            h_cross_array.push_back(strain.h_cross);
            amplitude_array.push_back(strain.amplitude);

            if (step % 100 == 0) {
                auto stats = field.getStatistics();
                std::cout << "Step " << std::setw(4) << step << " / " << num_steps
                          << " | t = " << std::setw(6) << std::fixed << std::setprecision(3) << t << " s"
                          << " | h = " << std::scientific << std::setprecision(2) << strain.amplitude
                          << " | E_field = " << std::setprecision(2) << stats.total_energy
                          << " | max_amp = " << std::setprecision(2) << stats.max_amplitude;

                if (merger_detected) {
                    auto active_echoes = echo_generator.getActiveEchoes(t);
                    if (!active_echoes.empty()) {
                        std::cout << " | Echoes: " << active_echoes.size() << " active";
                    }
                }
                std::cout << std::endl;
            }
        }
    }

    auto evolution_end = std::chrono::high_resolution_clock::now();
    auto evolution_duration = std::chrono::duration_cast<std::chrono::milliseconds>(evolution_end - evolution_start).count();

    std::cout << "\n✓ Evolution complete!" << std::endl;
    std::cout << "Evolution time: " << evolution_duration << " ms" << std::endl;
    std::cout << "Performance: " << num_steps * 1000.0 / evolution_duration << " steps/sec" << std::endl;

    // ========================================================================
    // 4. Export Results
    // ========================================================================

    std::cout << "\n=== Export ===" << std::endl;

    std::string filename = "gw_waveform_alpha_" + std::to_string(alpha_value) + ".csv";
    exportWaveformCSV(filename, time_array, h_plus_array, h_cross_array, amplitude_array);

    // Export echo schedule if merger was detected
    if (merger_detected) {
        std::string echo_filename = "echo_schedule_alpha_" + std::to_string(alpha_value) + ".csv";
        echo_generator.exportEchoSchedule(echo_filename);

        std::cout << "\nEcho Schedule Summary:" << std::endl;
        auto schedule = echo_generator.getEchoSchedule();
        std::cout << "  Total echoes: " << schedule.size() << std::endl;
        std::cout << "  First echo at: t = " << schedule[0].time << " s" << std::endl;
        if (schedule.size() > 1) {
            std::cout << "  Last echo at: t = " << schedule.back().time << " s" << std::endl;
        }
    } else {
        std::cout << "\nWARNING: No merger detected - no echoes generated!" << std::endl;
    }

    // ========================================================================
    // 5. Summary Statistics
    // ========================================================================

    std::cout << "\n=== Waveform Statistics ===" << std::endl;

    double max_h_plus = 0.0;
    double max_h_cross = 0.0;
    double max_amplitude = 0.0;

    for (size_t i = 0; i < amplitude_array.size(); i++) {
        max_h_plus = std::max(max_h_plus, std::abs(h_plus_array[i]));
        max_h_cross = std::max(max_h_cross, std::abs(h_cross_array[i]));
        max_amplitude = std::max(max_amplitude, amplitude_array[i]);
    }

    std::cout << std::scientific << std::setprecision(3);
    std::cout << "Max h_+ strain: " << max_h_plus << std::endl;
    std::cout << "Max h_× strain: " << max_h_cross << std::endl;
    std::cout << "Max amplitude: " << max_amplitude << std::endl;
    std::cout << "Data points: " << time_array.size() << std::endl;

    // ========================================================================
    // 6. Final State
    // ========================================================================

    std::cout << "\n=== Final State ===" << std::endl;
    merger.printState();

    auto field_stats = field.getStatistics();
    std::cout << "\nField Statistics:" << std::endl;
    std::cout << "  Max amplitude: " << field_stats.max_amplitude << std::endl;
    std::cout << "  Mean amplitude: " << field_stats.mean_amplitude << std::endl;
    std::cout << "  Total energy: " << field_stats.total_energy << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "SUCCESS: Generated first IGSOA waveform!" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
