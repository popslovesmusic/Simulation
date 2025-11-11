/**
 * IGSOA GW Engine - Echo Generator Implementation
 */

#define _USE_MATH_DEFINES
#include "echo_generator.h"
#include <cmath>
#include <iostream>
#include <fstream>
#include <iomanip>
#include <algorithm>

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
    initialize();
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

    std::cout << "EchoGenerator initialized:" << std::endl;
    std::cout << "  Primes generated: " << primes_.size() << std::endl;
    std::cout << "  Prime gaps computed: " << prime_gaps_.size() << std::endl;
    std::cout << "  Echoes scheduled: " << echo_schedule_.size() << std::endl;
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

    std::cout << "Merger time set to " << t << " s, "
              << echo_schedule_.size() << " echoes scheduled" << std::endl;
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
        std::cout << "\n*** MERGER DETECTED at t = " << current_time << " s ***" << std::endl;
        std::cout << "Field energy: " << current_energy << std::endl;
        std::cout << "Scheduling " << echo_schedule_.size() << " echoes" << std::endl;
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
    std::ofstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return;
    }

    file << std::scientific << std::setprecision(12);
    file << "echo_number,time,dt_from_previous,amplitude,frequency,prime_gap,prime_index\n";

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
    }

    file.close();
    std::cout << "Echo schedule exported to: " << filename << std::endl;
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
