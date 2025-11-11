/**
 * IGSOA GW Engine - Echo Detection Test
 *
 * Tests the EchoGenerator module:
 * - Prime number generation
 * - Prime gap calculation
 * - Echo schedule generation
 * - Echo signal timing
 */

#define _USE_MATH_DEFINES
#include <cmath>
#include "../src/cpp/igsoa_gw_engine/core/echo_generator.h"
#include <iostream>
#include <fstream>
#include <cassert>
#include <iomanip>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace dase::igsoa::gw;

// Helper function for test assertions
#define TEST_ASSERT(condition, message) \
    if (!(condition)) { \
        std::cerr << "TEST FAILED: " << message << std::endl; \
        std::cerr << "  at line " << __LINE__ << std::endl; \
        return false; \
    }

// ============================================================================
// Test 1: Prime Number Generation
// ============================================================================

bool test_prime_generation() {
    std::cout << "\n=== Test 1: Prime Number Generation ===" << std::endl;

    auto primes = EchoGenerator::generatePrimes(100);

    std::cout << "Generated " << primes.size() << " primes under 100" << std::endl;

    // First 10 primes: 2, 3, 5, 7, 11, 13, 17, 19, 23, 29
    TEST_ASSERT(primes.size() >= 10, "Should generate at least 10 primes");
    TEST_ASSERT(primes[0] == 2, "First prime should be 2");
    TEST_ASSERT(primes[1] == 3, "Second prime should be 3");
    TEST_ASSERT(primes[2] == 5, "Third prime should be 5");
    TEST_ASSERT(primes[3] == 7, "Fourth prime should be 7");
    TEST_ASSERT(primes[4] == 11, "Fifth prime should be 11");

    // Count primes under 100 (should be 25)
    TEST_ASSERT(primes.size() == 25, "Should be 25 primes under 100");

    std::cout << "First 10 primes: ";
    for (int i = 0; i < 10; i++) {
        std::cout << primes[i] << " ";
    }
    std::cout << std::endl;

    std::cout << "✓ Prime generation test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 2: Prime Gap Calculation
// ============================================================================

bool test_prime_gaps() {
    std::cout << "\n=== Test 2: Prime Gap Calculation ===" << std::endl;

    auto primes = EchoGenerator::generatePrimes(50);
    auto gaps = EchoGenerator::computePrimeGaps(primes);

    std::cout << "Computed " << gaps.size() << " prime gaps" << std::endl;

    // First gaps: 3-2=1, 5-3=2, 7-5=2, 11-7=4, 13-11=2
    TEST_ASSERT(gaps.size() == primes.size() - 1, "Should have N-1 gaps for N primes");
    TEST_ASSERT(gaps[0] == 1, "First gap (3-2) should be 1");
    TEST_ASSERT(gaps[1] == 2, "Second gap (5-3) should be 2");
    TEST_ASSERT(gaps[2] == 2, "Third gap (7-5) should be 2");
    TEST_ASSERT(gaps[3] == 4, "Fourth gap (11-7) should be 4");
    TEST_ASSERT(gaps[4] == 2, "Fifth gap (13-11) should be 2");

    std::cout << "First 20 prime gaps: ";
    for (int i = 0; i < std::min(20, static_cast<int>(gaps.size())); i++) {
        std::cout << gaps[i] << " ";
    }
    std::cout << std::endl;

    // Verify all gaps are positive
    for (int gap : gaps) {
        TEST_ASSERT(gap > 0, "All prime gaps should be positive");
    }

    std::cout << "✓ Prime gap calculation test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 3: Echo Schedule Generation
// ============================================================================

bool test_echo_schedule() {
    std::cout << "\n=== Test 3: Echo Schedule Generation ===" << std::endl;

    EchoConfig config;
    config.merger_time = 5.0;                   // Merger at 5 seconds
    config.fundamental_timescale = 0.001;       // 1 ms
    config.max_primes = 20;                     // First 20 echoes
    config.echo_amplitude_base = 0.1;
    config.echo_amplitude_decay = 10.0;

    EchoGenerator generator(config);

    auto schedule = generator.getEchoSchedule();

    std::cout << "Generated " << schedule.size() << " echo events" << std::endl;

    TEST_ASSERT(schedule.size() > 0, "Should generate at least one echo");
    TEST_ASSERT(schedule.size() <= 20, "Should not exceed max_primes");

    // First echo: gap=1, time = 5.0 + 1*0.001 = 5.001
    TEST_ASSERT(std::abs(schedule[0].time - 5.001) < 1e-6, "First echo time incorrect");
    TEST_ASSERT(schedule[0].prime_gap == 1, "First prime gap should be 1");
    TEST_ASSERT(schedule[0].echo_number == 1, "First echo number should be 1");

    // Second echo: gap=2, time = 5.0 + (1+2)*0.001 = 5.003
    TEST_ASSERT(std::abs(schedule[1].time - 5.003) < 1e-6, "Second echo time incorrect");
    TEST_ASSERT(schedule[1].prime_gap == 2, "Second prime gap should be 2");

    // Verify echoes are chronological
    for (size_t i = 1; i < schedule.size(); i++) {
        TEST_ASSERT(schedule[i].time > schedule[i-1].time, "Echoes should be chronological");
    }

    // Verify amplitude decay
    TEST_ASSERT(schedule[0].amplitude > schedule[1].amplitude, "Amplitude should decay");
    TEST_ASSERT(schedule[1].amplitude > schedule[5].amplitude, "Amplitude should decay");

    generator.printEchoSchedule();

    std::cout << "✓ Echo schedule generation test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 4: Echo Source Terms
// ============================================================================

bool test_echo_source() {
    std::cout << "\n=== Test 4: Echo Source Terms ===" << std::endl;

    EchoConfig config;
    config.merger_time = 1.0;
    config.fundamental_timescale = 0.001;
    config.max_primes = 10;
    config.echo_gaussian_width = 5000.0;  // 5 km
    config.auto_detect_merger = false;     // Manual merger time

    EchoGenerator generator(config);
    generator.setMergerTime(1.0);  // Explicitly set merger time

    Vector3D source_center(32000, 32000, 32000);  // 32 km
    Vector3D observer(32000, 32000, 32000);       // Same position

    // Before merger: no echoes
    auto source_before = generator.computeEchoSource(0.5, observer, source_center);
    TEST_ASSERT(std::abs(source_before) < 1e-10, "No echoes before merger");

    // At first echo time
    double first_echo_time = generator.getEchoSchedule()[0].time;
    auto source_at_echo = generator.computeEchoSource(first_echo_time, observer, source_center);
    TEST_ASSERT(std::abs(source_at_echo) > 1e-10, "Should have signal at echo time");

    std::cout << "Source at first echo: |S| = " << std::abs(source_at_echo) << std::endl;

    // Between echoes: weaker signal
    double between_echoes = (generator.getEchoSchedule()[0].time +
                             generator.getEchoSchedule()[1].time) / 2;
    auto source_between = generator.computeEchoSource(between_echoes, observer, source_center);

    std::cout << "Source between echoes: |S| = " << std::abs(source_between) << std::endl;
    std::cout << "Source at echo: |S| = " << std::abs(source_at_echo) << std::endl;

    TEST_ASSERT(std::abs(source_between) < std::abs(source_at_echo),
                "Signal should be weaker between echoes");

    std::cout << "✓ Echo source terms test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 5: Prime Statistics
// ============================================================================

bool test_prime_statistics() {
    std::cout << "\n=== Test 5: Prime Statistics ===" << std::endl;

    EchoConfig config;
    config.max_prime_value = 1000;
    EchoGenerator generator(config);

    auto stats = generator.getPrimeStatistics();

    std::cout << "Prime statistics:" << std::endl;
    std::cout << "  Number of primes: " << stats.num_primes << std::endl;
    std::cout << "  Maximum prime: " << stats.max_prime << std::endl;
    std::cout << "  Mean gap: " << std::fixed << std::setprecision(2) << stats.mean_gap << std::endl;
    std::cout << "  Min gap: " << stats.min_gap << std::endl;
    std::cout << "  Max gap: " << stats.max_gap << std::endl;

    TEST_ASSERT(stats.num_primes > 0, "Should have primes");
    TEST_ASSERT(stats.max_prime <= 1000, "Max prime should be <= 1000");
    TEST_ASSERT(stats.mean_gap > 0, "Mean gap should be positive");
    TEST_ASSERT(stats.min_gap >= 1, "Min gap should be at least 1");
    TEST_ASSERT(stats.max_gap > stats.min_gap, "Max gap should be > min gap");

    std::cout << "✓ Prime statistics test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 6: Active Echoes Query
// ============================================================================

bool test_active_echoes() {
    std::cout << "\n=== Test 6: Active Echoes Query ===" << std::endl;

    EchoConfig config;
    config.merger_time = 2.0;
    config.fundamental_timescale = 0.001;
    config.max_primes = 30;
    config.auto_detect_merger = false;     // Manual merger time

    EchoGenerator generator(config);
    generator.setMergerTime(2.0);  // Explicitly set merger time

    // At beginning: no active echoes
    auto active_0 = generator.getActiveEchoes(0.0);
    TEST_ASSERT(active_0.empty(), "No echoes before merger");

    // At first echo: one active (use larger pulse width to ensure detection)
    double first_echo_time = generator.getEchoSchedule()[0].time;
    auto active_1 = generator.getActiveEchoes(first_echo_time, 5.0);  // Wider pulse
    TEST_ASSERT(active_1.size() >= 1, "At least one echo active at first echo time");

    // Far in future: no active echoes
    auto active_future = generator.getActiveEchoes(100.0);
    TEST_ASSERT(active_future.empty(), "No echoes far in future");

    std::cout << "Active echoes at t=" << first_echo_time << ": " << active_1.size() << std::endl;

    std::cout << "✓ Active echoes query test passed" << std::endl;
    return true;
}

// ============================================================================
// Test 7: Echo Export
// ============================================================================

bool test_echo_export() {
    std::cout << "\n=== Test 7: Echo Schedule Export ===" << std::endl;

    EchoConfig config;
    config.merger_time = 3.0;
    config.fundamental_timescale = 0.001;
    config.max_primes = 25;

    EchoGenerator generator(config);

    generator.exportEchoSchedule("test_echo_schedule.csv");

    // Verify file was created (simple check)
    std::ifstream file("test_echo_schedule.csv");
    TEST_ASSERT(file.good(), "Echo schedule file should be created");
    file.close();

    std::cout << "✓ Echo export test passed" << std::endl;
    return true;
}

// ============================================================================
// Main Test Runner
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "IGSOA Echo Generator Test Suite" << std::endl;
    std::cout << "========================================" << std::endl;

    int tests_passed = 0;
    int tests_total = 7;

    if (test_prime_generation()) tests_passed++;
    if (test_prime_gaps()) tests_passed++;
    if (test_echo_schedule()) tests_passed++;
    if (test_echo_source()) tests_passed++;
    if (test_prime_statistics()) tests_passed++;
    if (test_active_echoes()) tests_passed++;
    if (test_echo_export()) tests_passed++;

    std::cout << "\n========================================" << std::endl;
    std::cout << "Test Results: " << tests_passed << "/" << tests_total << " passed" << std::endl;

    if (tests_passed == tests_total) {
        std::cout << "✓ ALL TESTS PASSED!" << std::endl;
        std::cout << "========================================" << std::endl;
        return 0;
    } else {
        std::cout << "✗ SOME TESTS FAILED" << std::endl;
        std::cout << "========================================" << std::endl;
        return 1;
    }
}
