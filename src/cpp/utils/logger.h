#ifndef IGSOA_LOGGER_H
#define IGSOA_LOGGER_H

#include <string>
#include <fstream>
#include <mutex>
#include <memory>
#include <sstream>

namespace igsoa {

/**
 * @brief Simple thread-safe logging system for IGSOA-SIM
 *
 * Provides structured logging with multiple levels (DEBUG, INFO, WARNING, ERROR, FATAL)
 * Logs to both file and console (configurable)
 * Thread-safe for potential future parallelization
 *
 * Usage:
 *   Logger::getInstance().initialize("simulation.log");
 *   LOG_INFO("Simulation started with N=" + std::to_string(N));
 *   LOG_ERROR("Failed to allocate memory");
 */
class Logger {
public:
    /**
     * @brief Log severity levels
     */
    enum class Level {
        DEBUG,      ///< Detailed diagnostic information
        INFO,       ///< Informational messages about program execution
        WARNING,    ///< Warning messages for recoverable issues
        ERROR,      ///< Error messages for failures
        FATAL       ///< Fatal errors that cause program termination
    };

    /**
     * @brief Get the singleton Logger instance
     * @return Reference to the global Logger instance
     */
    static Logger& getInstance();

    /**
     * @brief Initialize the logger with output file
     * @param filename Path to log file (default: "igsoa_sim.log")
     * @param console_level Minimum level to print to console (default: WARNING)
     * @param file_level Minimum level to write to file (default: DEBUG)
     */
    void initialize(
        const std::string& filename = "igsoa_sim.log",
        Level console_level = Level::WARNING,
        Level file_level = Level::DEBUG
    );

    /**
     * @brief Set minimum log level for console output
     * @param level Minimum level to print to console
     */
    void setConsoleLevel(Level level);

    /**
     * @brief Set minimum log level for file output
     * @param level Minimum level to write to file
     */
    void setFileLevel(Level level);

    /**
     * @brief Log a message at the specified level
     * @param level Log severity level
     * @param message Message to log
     * @param file Source file name (usually __FILE__)
     * @param line Source line number (usually __LINE__)
     */
    void log(Level level, const std::string& message,
             const char* file = nullptr, int line = -1);

    /**
     * @brief Close the log file
     */
    void shutdown();

    /**
     * @brief Check if logger is initialized
     * @return true if initialized, false otherwise
     */
    bool isInitialized() const { return initialized_; }

    // Delete copy and move constructors/assignments (singleton)
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;
    Logger(Logger&&) = delete;
    Logger& operator=(Logger&&) = delete;

private:
    Logger();
    ~Logger();

    /**
     * @brief Convert log level to string
     * @param level Log level
     * @return String representation (e.g., "INFO", "ERROR")
     */
    static const char* levelToString(Level level);

    /**
     * @brief Get current timestamp as string
     * @return Formatted timestamp "YYYY-MM-DD HH:MM:SS"
     */
    static std::string getCurrentTimestamp();

    /**
     * @brief Extract filename from full path
     * @param filepath Full file path
     * @return Just the filename
     */
    static std::string extractFilename(const char* filepath);

    /**
     * @brief Check if message should be logged at this level
     * @param level Message level
     * @param threshold Minimum level threshold
     * @return true if level >= threshold
     */
    static bool shouldLog(Level level, Level threshold);

    std::ofstream file_;           ///< Log file stream
    std::mutex mutex_;             ///< Mutex for thread safety
    Level console_level_;          ///< Minimum level for console output
    Level file_level_;             ///< Minimum level for file output
    bool initialized_;             ///< Whether logger is initialized
    std::string filename_;         ///< Current log filename
};

} // namespace igsoa

// Convenience macros for logging
// Use :: prefix to ensure global namespace lookup (works from any namespace)
#define LOG_DEBUG(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::DEBUG, msg, __FILE__, __LINE__)

#define LOG_INFO(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::INFO, msg, __FILE__, __LINE__)

#define LOG_WARNING(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::WARNING, msg, __FILE__, __LINE__)

#define LOG_ERROR(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::ERROR, msg, __FILE__, __LINE__)

#define LOG_FATAL(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::FATAL, msg, __FILE__, __LINE__)

// Alternative: Log without file/line information (cleaner output)
#define LOG_DEBUG_SIMPLE(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::DEBUG, msg)

#define LOG_INFO_SIMPLE(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::INFO, msg)

#define LOG_WARNING_SIMPLE(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::WARNING, msg)

#define LOG_ERROR_SIMPLE(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::ERROR, msg)

#define LOG_FATAL_SIMPLE(msg) \
    ::igsoa::Logger::getInstance().log(::igsoa::Logger::Level::FATAL, msg)

#endif // IGSOA_LOGGER_H
