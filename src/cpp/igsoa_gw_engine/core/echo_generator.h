/**
 * IGSOA GW Engine - Echo Generator
 *
 * Implements IGSOA's unique prediction: post-merger gravitational wave echoes
 * with timing structure following prime number gaps.
 *
 * In IGSOA theory, information restoration after black hole merger occurs in
 * discrete steps correlated with prime number distribution, creating observable
 * echo signals that distinguish IGSOA from General Relativity.
 *
 * Echo timing: Δt_n = τ₀ × (p_{n+1} - p_n)
 * where p_n is the nth prime number and τ₀ is the fundamental timescale.
 */

#pragma once

#include "symmetry_field.h"
#include <vector>
#include <complex>

namespace dase {
namespace igsoa {
namespace gw {

/**
 * Configuration for echo generation
 */
struct EchoConfig {
    // Post-merger parameters
    double merger_time;              // Time when merger occurs (s), 0 = auto-detect
    double fundamental_timescale;    // τ₀ - base echo delay (s), typically 0.001

    // Prime number parameters
    int max_primes;                  // Number of primes to use (default: 50)
    int prime_start_index;           // Start at nth prime (default: 0)
    int max_prime_value;             // Generate primes up to this value (default: 1000)

    // Echo signal parameters
    double echo_amplitude_base;      // Base echo amplitude (relative to merger)
    double echo_amplitude_decay;     // Exponential decay rate: A_n = A₀ exp(-n/decay)
    double echo_frequency_shift;     // Frequency shift per echo (Hz)
    double echo_gaussian_width;      // Spatial width of echo Gaussian (m)

    // Detection parameters
    bool auto_detect_merger;         // Automatically detect merger event
    double merger_detection_threshold; // Field energy threshold for merger

    EchoConfig()
        : merger_time(0.0)
        , fundamental_timescale(0.001)  // 1 ms default
        , max_primes(50)
        , prime_start_index(0)
        , max_prime_value(1000)
        , echo_amplitude_base(0.1)       // 10% of merger signal
        , echo_amplitude_decay(10.0)     // Decay over ~10 echoes
        , echo_frequency_shift(10.0)     // 10 Hz shift per echo
        , echo_gaussian_width(5000.0)    // 5 km
        , auto_detect_merger(true)
        , merger_detection_threshold(1e9)
    {}
};

/**
 * Single echo event
 */
struct EchoEvent {
    double time;                     // Echo arrival time (s)
    double amplitude;                // Relative amplitude (0.0 to 1.0)
    double frequency;                // Characteristic frequency (Hz)
    int prime_gap;                   // Associated prime gap (p_{n+1} - p_n)
    int prime_index;                 // Index n of prime pair
    int echo_number;                 // Echo index (1, 2, 3, ...)

    EchoEvent()
        : time(0.0)
        , amplitude(0.0)
        , frequency(0.0)
        , prime_gap(0)
        , prime_index(0)
        , echo_number(0)
    {}

    EchoEvent(double t, double amp, double freq, int gap, int idx, int num)
        : time(t)
        , amplitude(amp)
        , frequency(freq)
        , prime_gap(gap)
        , prime_index(idx)
        , echo_number(num)
    {}
};

/**
 * Echo generator using prime number gaps
 *
 * This class implements IGSOA's distinctive prediction: gravitational wave
 * echoes following black hole merger have timing structure determined by
 * gaps between consecutive prime numbers.
 *
 * This provides a clear observational signature distinguishing IGSOA from GR:
 * - GR: Exponential ringdown with smooth decay
 * - IGSOA: Discrete echoes with prime-gap timing structure
 */
class EchoGenerator {
public:
    /**
     * Constructor
     * @param config Echo generation configuration
     */
    explicit EchoGenerator(const EchoConfig& config);

    // === Prime Number Utilities ===

    /**
     * Generate prime numbers up to max_value using Sieve of Eratosthenes
     * @param max_value Maximum value to check for primality
     * @return Vector of prime numbers in ascending order
     */
    static std::vector<int> generatePrimes(int max_value);

    /**
     * Compute gaps between consecutive primes: p_{n+1} - p_n
     * @param primes Vector of prime numbers (must be sorted)
     * @return Vector of gaps (size = primes.size() - 1)
     */
    static std::vector<int> computePrimeGaps(const std::vector<int>& primes);

    /**
     * Get nth prime number (0-indexed)
     * @param n Index of prime to retrieve
     * @return nth prime number, or -1 if not available
     */
    int getPrime(int n) const;

    /**
     * Get gap between nth and (n+1)th prime
     * @param n Index of first prime in gap
     * @return Gap value, or -1 if not available
     */
    int getPrimeGap(int n) const;

    // === Echo Schedule Generation ===

    /**
     * Generate complete echo event schedule from prime gaps
     * Creates discrete echo events with timing: t_n = t_merger + τ₀ Σ(gaps)
     * @return Vector of echo events in chronological order
     */
    std::vector<EchoEvent> generateEchoSchedule() const;

    /**
     * Set merger time (for manual triggering)
     * @param t Time of merger event (s)
     */
    void setMergerTime(double t);

    /**
     * Get configured merger time
     * @return Merger time (s), or 0 if not yet detected
     */
    double getMergerTime() const { return config_.merger_time; }

    // === Echo Source Terms ===

    /**
     * Compute echo source contribution at given time and position
     *
     * Returns complex amplitude for field perturbation S(x,t) due to echoes.
     * Multiple echoes can be active simultaneously.
     *
     * @param t Current simulation time (s)
     * @param position Spatial position (x,y,z) in meters
     * @param source_center Center of echo source (merger location)
     * @return Complex source amplitude
     */
    std::complex<double> computeEchoSource(
        double t,
        const Vector3D& position,
        const Vector3D& source_center) const;

    /**
     * Get amplitude of specific echo at given time
     * Returns Gaussian pulse: A exp(-((t-t_echo)/σ)²)
     * @param echo Echo event
     * @param t Current time
     * @return Instantaneous amplitude (0 outside pulse width)
     */
    double getEchoAmplitude(const EchoEvent& echo, double t) const;

    // === Merger Detection ===

    /**
     * Detect merger event from field energy
     * @param field Current symmetry field
     * @param current_time Current simulation time
     * @return True if merger detected this call
     */
    bool detectMerger(const SymmetryField& field, double current_time);

    /**
     * Check if merger has been detected
     * @return True if merger detected
     */
    bool hasMergerDetected() const { return merger_detected_; }

    // === Echo Query ===

    /**
     * Get next echo event after given time
     * @param t Reference time (s)
     * @return Next echo event, or empty event if none remaining
     */
    EchoEvent getNextEcho(double t) const;

    /**
     * Check if currently in echo phase (any echo active)
     * @param t Current time
     * @return True if at least one echo is active
     */
    bool isEchoActive(double t) const;

    /**
     * Get all echoes active at given time
     * @param t Current time
     * @param pulse_width_sigma Pulse width in units of τ₀
     * @return Vector of active echo events
     */
    std::vector<EchoEvent> getActiveEchoes(double t, double pulse_width_sigma = 3.0) const;

    /**
     * Get total number of echoes in schedule
     * @return Number of echo events
     */
    size_t getNumEchoes() const { return echo_schedule_.size(); }

    /**
     * Get echo schedule
     * @return Reference to echo schedule
     */
    const std::vector<EchoEvent>& getEchoSchedule() const { return echo_schedule_; }

    // === Configuration ===

    /**
     * Get configuration
     * @return Current echo configuration
     */
    const EchoConfig& getConfig() const { return config_; }

    // === Diagnostics ===

    /**
     * Print echo schedule to stdout
     */
    void printEchoSchedule() const;

    /**
     * Export echo schedule to CSV file
     * @param filename Output filename
     */
    void exportEchoSchedule(const std::string& filename) const;

    /**
     * Get prime number statistics
     */
    struct PrimeStats {
        int num_primes;
        int max_prime;
        double mean_gap;
        int max_gap;
        int min_gap;
    };
    PrimeStats getPrimeStatistics() const;

private:
    EchoConfig config_;                   // Configuration
    std::vector<int> primes_;             // Prime numbers
    std::vector<int> prime_gaps_;         // Gaps between primes
    std::vector<EchoEvent> echo_schedule_; // Scheduled echo events
    bool merger_detected_;                // Whether merger has occurred
    double last_field_energy_;            // For merger detection

    /**
     * Initialize: generate primes and compute gaps
     */
    void initialize();

    /**
     * Validate configuration parameters
     * Throws std::invalid_argument if any parameter is invalid
     */
    void validateConfig() const;

    /**
     * Generate single echo event
     * @param echo_number Echo index (1-based)
     * @param cumulative_time Accumulated time from all previous gaps
     * @param prime_index Index of prime gap
     * @return Echo event
     */
    EchoEvent createEchoEvent(
        int echo_number,
        double cumulative_time,
        int prime_index) const;
};

} // namespace gw
} // namespace igsoa
} // namespace dase
