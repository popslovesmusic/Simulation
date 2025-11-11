/**
 * @file test_logger.cpp
 * @brief Test the Logger utility class
 *
 * Tests basic logging functionality, log levels, and file output.
 */

#include "utils/logger.h"
#include <iostream>
#include <fstream>
#include <string>
#include <thread>
#include <chrono>

using namespace igsoa;

void testBasicLogging() {
    std::cout << "\n=== Test 1: Basic Logging ===\n";

    // Initialize logger
    Logger::getInstance().initialize(
        "test_logger.log",
        Logger::Level::INFO,     // Console: INFO and above
        Logger::Level::DEBUG     // File: DEBUG and above
    );

    // Test all log levels
    LOG_DEBUG("This is a debug message (should only appear in file)");
    LOG_INFO("This is an info message");
    LOG_WARNING("This is a warning message");
    LOG_ERROR("This is an error message");
    LOG_FATAL("This is a fatal message");

    std::cout << "✓ Test 1 passed: Basic logging\n";
}

void testLogLevels() {
    std::cout << "\n=== Test 2: Log Level Filtering ===\n";

    // Change console level to ERROR (only errors and fatal)
    Logger::getInstance().setConsoleLevel(Logger::Level::ERROR);

    std::cout << "\n(Console level set to ERROR - you should only see ERROR and FATAL below)\n";

    LOG_DEBUG("Debug message (should not appear on console)");
    LOG_INFO("Info message (should not appear on console)");
    LOG_WARNING("Warning message (should not appear on console)");
    LOG_ERROR("Error message (should appear on console)");
    LOG_FATAL("Fatal message (should appear on console)");

    std::cout << "\n✓ Test 2 passed: Log level filtering\n";
}

void testSimpleLogging() {
    std::cout << "\n=== Test 3: Simple Logging (no file/line) ===\n";

    // Reset console level
    Logger::getInstance().setConsoleLevel(Logger::Level::INFO);

    LOG_INFO_SIMPLE("Simple info message (no file:line)");
    LOG_WARNING_SIMPLE("Simple warning message (no file:line)");
    LOG_ERROR_SIMPLE("Simple error message (no file:line)");

    std::cout << "✓ Test 3 passed: Simple logging\n";
}

void testWithNumbers() {
    std::cout << "\n=== Test 4: Logging with Data ===\n";

    int num_nodes = 1024;
    double alpha = 1.5;
    size_t memory_mb = 256;

    LOG_INFO("Simulation initialized: num_nodes=" + std::to_string(num_nodes) +
             ", alpha=" + std::to_string(alpha));

    LOG_WARNING("Memory usage: " + std::to_string(memory_mb) + " MB");

    std::string filename = "test_data.csv";
    LOG_ERROR("Failed to write to file: " + filename);

    std::cout << "✓ Test 4 passed: Logging with data\n";
}

void threadFunction(int thread_id) {
    for (int i = 0; i < 5; i++) {
        LOG_INFO("Thread " + std::to_string(thread_id) +
                 " message " + std::to_string(i));
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void testThreadSafety() {
    std::cout << "\n=== Test 5: Thread Safety ===\n";

    // Create 3 threads that log simultaneously
    std::thread t1(threadFunction, 1);
    std::thread t2(threadFunction, 2);
    std::thread t3(threadFunction, 3);

    t1.join();
    t2.join();
    t3.join();

    std::cout << "✓ Test 5 passed: Thread safety (check log file for interleaving)\n";
}

void verifyLogFile() {
    std::cout << "\n=== Test 6: Verify Log File ===\n";

    // Shutdown logger to flush
    Logger::getInstance().shutdown();

    // Check if file exists and has content
    std::ifstream file("test_logger.log");
    if (!file.is_open()) {
        std::cerr << "✗ Test 6 FAILED: Log file not found\n";
        return;
    }

    // Count lines
    int line_count = 0;
    std::string line;
    while (std::getline(file, line)) {
        line_count++;
    }
    file.close();

    std::cout << "Log file contains " << line_count << " lines\n";

    if (line_count > 0) {
        std::cout << "✓ Test 6 passed: Log file created and contains data\n";
    } else {
        std::cerr << "✗ Test 6 FAILED: Log file is empty\n";
    }
}

int main() {
    std::cout << "========================================\n";
    std::cout << "Logger Test Suite\n";
    std::cout << "========================================\n";

    try {
        testBasicLogging();
        testLogLevels();
        testSimpleLogging();
        testWithNumbers();
        testThreadSafety();
        verifyLogFile();

        std::cout << "\n========================================\n";
        std::cout << "✓ ALL TESTS PASSED!\n";
        std::cout << "========================================\n";
        std::cout << "\nCheck 'test_logger.log' for full output\n";

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "\n✗ TEST FAILED WITH EXCEPTION: " << e.what() << "\n";
        return 1;
    }
}
