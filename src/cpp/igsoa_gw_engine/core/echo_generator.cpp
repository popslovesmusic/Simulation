/**
 * IGSOA GW Engine - Echo Generator Implementation
 */

#define _USE_MATH_DEFINES
#include "echo_generator.h"
#include "utils/logger.h"
#include <cmath>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <algorithm>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace dase {
namespace igsoa {
namespace gw {

// ============================================================================
// Constructor
// ============================================================================

EchoGenerator::EchoGenerator(const EchoConfig& config)
    : config_(config)
    , merger_detected_(false)
    , last_field_energy_(0.0)
{
    // Validate configuration before initialization
    validateConfig();
    initialize();
}

// ============================================================================
// Configuration Validation
// ============================================================================

void EchoGenerator::validateConfig() const {
    // Validate fundamental_timescale
    if (config_.fundamental_timescale <= 0.0) {
        std::string error_msg = "fundamental_timescale must be positive, got: " +
                               std::to_string(config_.fundamental_timescale) +
                               ". Typical range: 0.0001 to 0.01 seconds.";
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate max_primes
    if (config_.max_primes < 1) {
        std::string error_msg = "max_primes must be >= 1, got: " +
                               std::to_string(config_.max_primes);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate prime_start_index
    if (config_.prime_start_index < 0) {
        std::string error_msg = "prime_start_index must be >= 0, got: " +
                               std::to_string(config_.prime_start_index);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate max_prime_value
    if (config_.max_prime_value < 2) {
        std::string error_msg = "max_prime_value must be >= 2 (smallest prime), got: " +
                               std::to_string(config_.max_prime_value);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate echo_amplitude_base
    if (config_.echo_amplitude_base < 0.0) {
        std::string error_msg = "echo_amplitude_base must be non-negative, got: " +
                               std::to_string(config_.echo_amplitude_base);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate echo_amplitude_decay
    if (config_.echo_amplitude_decay <= 0.0) {
        std::string error_msg = "echo_amplitude_decay must be positive, got: " +
                               std::to_string(config_.echo_amplitude_decay) +
                               ". Typical range: 5.0 to 20.0.";
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate echo_frequency_shift
    if (config_.echo_frequency_shift < 0.0) {
        std::string error_msg = "echo_frequency_shift must be non-negative, got: " +
                               std::to_string(config_.echo_frequency_shift);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate echo_gaussian_width
    if (config_.echo_gaussian_width <= 0.0) {
        std::string error_msg = "echo_gaussian_width must be positive, got: " +
                               std::to_string(config_.echo_gaussian_width) +
                               " meters. Typical range: 1000 to 10000 meters.";
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Validate merger_detection_threshold
    if (config_.merger_detection_threshold <= 0.0) {
        std::string error_msg = "merger_detection_threshold must be positive, got: " +
                               std::to_string(config_.merger_detection_threshold);
        LOG_ERROR(error_msg);
        throw std::invalid_argument(error_msg);
    }

    // Consistency check: prime_start_index + max_primes should be reasonable
    if (config_.prime_start_index + config_.max_primes > 1000) {
        std::string warning_msg = "Large prime range requested: start=" +
                                 std::to_string(config_.prime_start_index) +
                                 " + count=" + std::to_string(config_.max_primes) +
                                 " = " + std::to_string(config_.prime_start_index + config_.max_primes) +
                                 " (may need to increase max_prime_value)";
        LOG_WARNING(warning_msg);
    }

    LOG_DEBUG("Configuration validated successfully");
}

// ============================================================================
// Initialization
// ============================================================================

void EchoGenerator::initialize() {
    // Generate prime numbers
    primes_ = generatePrimes(config_.max_prime_value);

    // Compute prime gaps
    prime_gaps_ = computePrimeGaps(primes_);

    // Generate echo schedule
    echo_schedule_ = generateEchoSchedule();

    LOG_INFO("EchoGenerator initialized: " + std::to_string(primes_.size()) +
             " primes, " + std::to_string(prime_gaps_.size()) + " gaps, " +
             std::to_string(echo_schedule_.size()) + " echoes scheduled");
}

// ============================================================================
// Prime Number Utilities
// ============================================================================

std::vector<int> EchoGenerator::generatePrimes(int max_value) {
    if (max_value < 2) {
        return std::vector<int>();
    }

    // Sieve of Eratosthenes
    std::vector<bool> is_prime(max_value + 1, true);
    is_prime[0] = is_prime[1] = false;

    for (int i = 2; i * i <= max_value; i++) {
        if (is_prime[i]) {
            for (int j = i * i; j <= max_value; j += i) {
                is_prime[j] = false;
            }
        }
    }

    // Collect primes
    std::vector<int> primes;
    primes.reserve(max_value / std::log(max_value)); // Approximate count

    for (int i = 2; i <= max_value; i++) {
        if (is_prime[i]) {
            primes.push_back(i);
        }
    }

    return primes;
}

std::vector<int> EchoGenerator::computePrimeGaps(const std::vector<int>& primes) {
    std::vector<int> gaps;
    if (primes.size() < 2) {
        return gaps;
    }

    gaps.reserve(primes.size() - 1);

    for (size_t i = 1; i < primes.size(); i++) {
        gaps.push_back(primes[i] - primes[i - 1]);
    }

    return gaps;
}

int EchoGenerator::getPrime(int n) const {
    if (n < 0 || n >= static_cast<int>(primes_.size())) {
        return -1;
    }
    return primes_[n];
}

int EchoGenerator::getPrimeGap(int n) const {
    if (n < 0 || n >= static_cast<int>(prime_gaps_.size())) {
        return -1;
    }
    return prime_gaps_[n];
}

// ============================================================================
// Echo Schedule Generation
// ============================================================================

std::vector<EchoEvent> EchoGenerator::generateEchoSchedule() const {
    std::vector<EchoEvent> schedule;

    if (prime_gaps_.empty()) {
        return schedule;
    }

    // Determine number of echoes
    int num_echoes = std::min(config_.max_primes, static_cast<int>(prime_gaps_.size()));

    schedule.reserve(num_echoes);

    double cumulative_time = 0.0;

    for (int i = 0; i < num_echoes; i++) {
        int gap_index = config_.prime_start_index + i;
        if (gap_index >= static_cast<int>(prime_gaps_.size())) {
            break;
        }

        int gap = prime_gaps_[gap_index];

        // Accumulate time
        cumulative_time += gap * config_.fundamental_timescale;

        // Create echo event
        EchoEvent echo = createEchoEvent(i + 1, cumulative_time, gap_index);
        schedule.push_back(echo);
    }

    return schedule;
}

EchoEvent EchoGenerator::createEchoEvent(
    int echo_number,
    double cumulative_time,
    int prime_index) const
{
    EchoEvent echo;

    // Time: merger time + accumulated prime-gap delays
    echo.time = config_.merger_time + cumulative_time;

    // Amplitude: exponential decay
    echo.amplitude = config_.echo_amplitude_base *
                     std::exp(-static_cast<double>(echo_number) / config_.echo_amplitude_decay);

    // Frequency: base + shift per echo
    echo.frequency = 244.0 + echo_number * config_.echo_frequency_shift; // Start at ~244 Hz

    // Prime gap info
    echo.prime_gap = prime_gaps_[prime_index];
    echo.prime_index = prime_index;
    echo.echo_number = echo_number;

    return echo;
}

void EchoGenerator::setMergerTime(double t) {
    config_.merger_time = t;
    merger_detected_ = true;

    // Regenerate schedule with new merger time
    echo_schedule_ = generateEchoSchedule();

    LOG_INFO("Merger time set to " + std::to_string(t) + " s, " +
             std::to_string(echo_schedule_.size()) + " echoes scheduled");
}

// ============================================================================
// Echo Source Terms
// ============================================================================

std::complex<double> EchoGenerator::computeEchoSource(
    double t,
    const Vector3D& position,
    const Vector3D& source_center) const
{
    if (!merger_detected_ || echo_schedule_.empty()) {
        return std::complex<double>(0.0, 0.0);
    }

    // Get active echoes at time t
    std::vector<EchoEvent> active = getActiveEchoes(t, 3.0);

    if (active.empty()) {
        return std::complex<double>(0.0, 0.0);
    }

    // Compute distance from source center
    Vector3D r = position - source_center;
    double distance_sq = r.x * r.x + r.y * r.y + r.z * r.z;
    double sigma_sq = config_.echo_gaussian_width * config_.echo_gaussian_width;

    // Sum contributions from all active echoes
    std::complex<double> total_source(0.0, 0.0);

    for (const auto& echo : active) {
        // Temporal Gaussian pulse
        double dt = t - echo.time;
        double pulse_width = config_.fundamental_timescale * 2.0; // 2τ₀ width
        double temporal_gaussian = std::exp(-(dt * dt) / (2.0 * pulse_width * pulse_width));

        // Spatial Gaussian
        double spatial_gaussian = std::exp(-distance_sq / (2.0 * sigma_sq));

        // Phase based on frequency
        double phase = 2.0 * M_PI * echo.frequency * dt;

        // Complex amplitude
        double amplitude = echo.amplitude * temporal_gaussian * spatial_gaussian;
        total_source += std::complex<double>(
            amplitude * std::cos(phase),
            amplitude * std::sin(phase)
        );
    }

    return total_source;
}

double EchoGenerator::getEchoAmplitude(const EchoEvent& echo, double t) const {
    double dt = t - echo.time;
    double pulse_width = config_.fundamental_timescale * 2.0;
    double temporal_gaussian = std::exp(-(dt * dt) / (2.0 * pulse_width * pulse_width));

    return echo.amplitude * temporal_gaussian;
}

// ============================================================================
// Merger Detection
// ============================================================================

bool EchoGenerator::detectMerger(const SymmetryField& field, double current_time) {
    if (merger_detected_ || !config_.auto_detect_merger) {
        return false;
    }

    // Compute current field energy
    double current_energy = field.computeTotalEnergy();

    // Detect sudden drop or peak (merger signature)
    // In real simulation, merger causes energy peak then stabilization
    bool energy_threshold_reached = current_energy > config_.merger_detection_threshold;

    if (energy_threshold_reached && last_field_energy_ < config_.merger_detection_threshold) {
        // Threshold crossed - merger detected!
        setMergerTime(current_time);
        std::ostringstream oss;
        oss << std::scientific << std::setprecision(2);
        oss << "\n*** MERGER DETECTED at t = " << current_time << " s ***\n";
        oss << "Field energy: " << current_energy << "\n";
        oss << "Scheduling " << echo_schedule_.size() << " echoes";
        LOG_INFO(oss.str());
        return true;
    }

    last_field_energy_ = current_energy;
    return false;
}

// ============================================================================
// Echo Query
// ============================================================================

EchoEvent EchoGenerator::getNextEcho(double t) const {
    for (const auto& echo : echo_schedule_) {
        if (echo.time > t) {
            return echo;
        }
    }
    return EchoEvent(); // Empty event if none remaining
}

bool EchoGenerator::isEchoActive(double t) const {
    return !getActiveEchoes(t, 3.0).empty();
}

std::vector<EchoEvent> EchoGenerator::getActiveEchoes(double t, double pulse_width_sigma) const {
    std::vector<EchoEvent> active;

    double pulse_width = config_.fundamental_timescale * pulse_width_sigma;

    for (const auto& echo : echo_schedule_) {
        double dt = std::abs(t - echo.time);
        if (dt < pulse_width) {
            active.push_back(echo);
        }
    }

    return active;
}

// ============================================================================
// Diagnostics
// ============================================================================

void EchoGenerator::printEchoSchedule() const {
    std::cout << "\n=== Echo Schedule ===" << std::endl;
    std::cout << "Merger time: " << config_.merger_time << " s" << std::endl;
    std::cout << "Fundamental timescale: " << config_.fundamental_timescale * 1000 << " ms" << std::endl;
    std::cout << "Number of echoes: " << echo_schedule_.size() << "\n" << std::endl;

    std::cout << std::setw(5) << "Echo"
              << std::setw(12) << "Time (s)"
              << std::setw(12) << "dt (ms)"
              << std::setw(12) << "Amplitude"
              << std::setw(12) << "Freq (Hz)"
              << std::setw(10) << "PrimeGap"
              << std::endl;
    std::cout << std::string(70, '-') << std::endl;

    for (size_t i = 0; i < echo_schedule_.size(); i++) {
        const auto& echo = echo_schedule_[i];
        double dt_from_prev = (i == 0) ?
            (echo.time - config_.merger_time) :
            (echo.time - echo_schedule_[i-1].time);

        std::cout << std::setw(5) << echo.echo_number
                  << std::setw(12) << std::fixed << std::setprecision(6) << echo.time
                  << std::setw(12) << std::fixed << std::setprecision(3) << dt_from_prev * 1000
                  << std::setw(12) << std::fixed << std::setprecision(4) << echo.amplitude
                  << std::setw(12) << std::fixed << std::setprecision(2) << echo.frequency
                  << std::setw(10) << echo.prime_gap
                  << std::endl;
    }
    std::cout << std::endl;
}

void EchoGenerator::exportEchoSchedule(const std::string& filename) const {
    // Validate input
    if (filename.empty()) {
        LOG_ERROR("Export failed: filename cannot be empty");
        throw std::invalid_argument("filename cannot be empty");
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
        file << "echo_number,time,dt_from_previous,amplitude,frequency,prime_gap,prime_index\n";
        if (!file.good()) {
            std::string error_msg = "Write error while writing header to: " + filename;
            LOG_ERROR(error_msg);
            throw std::runtime_error(error_msg);
        }

        // Write data
        for (size_t i = 0; i < echo_schedule_.size(); i++) {
            const auto& echo = echo_schedule_[i];
            double dt_from_prev = (i == 0) ?
                (echo.time - config_.merger_time) :
                (echo.time - echo_schedule_[i-1].time);

            file << echo.echo_number << ","
                 << echo.time << ","
                 << dt_from_prev << ","
                 << echo.amplitude << ","
                 << echo.frequency << ","
                 << echo.prime_gap << ","
                 << echo.prime_index << "\n";

            // Check write status periodically (every 100 rows)
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
            std::string error_msg = "Failed to close file properly: " + filename;
            LOG_WARNING(error_msg);
            // Don't throw - data is written, just close failed
        }

        LOG_INFO("Echo schedule exported successfully: " + filename +
                 " (" + std::to_string(echo_schedule_.size()) + " echoes)");

    } catch (const std::exception& e) {
        LOG_ERROR("Exception during echo schedule export: " + std::string(e.what()));
        throw;  // Re-throw for caller to handle
    }
}

EchoGenerator::PrimeStats EchoGenerator::getPrimeStatistics() const {
    PrimeStats stats;

    stats.num_primes = static_cast<int>(primes_.size());
    stats.max_prime = primes_.empty() ? 0 : primes_.back();

    if (prime_gaps_.empty()) {
        stats.mean_gap = 0.0;
        stats.max_gap = 0;
        stats.min_gap = 0;
        return stats;
    }

    // Compute statistics on gaps
    int sum = 0;
    stats.max_gap = prime_gaps_[0];
    stats.min_gap = prime_gaps_[0];

    for (int gap : prime_gaps_) {
        sum += gap;
        stats.max_gap = std::max(stats.max_gap, gap);
        stats.min_gap = std::min(stats.min_gap, gap);
    }

    stats.mean_gap = static_cast<double>(sum) / prime_gaps_.size();

    return stats;
}

} // namespace gw
} // namespace igsoa
} // namespace dase
