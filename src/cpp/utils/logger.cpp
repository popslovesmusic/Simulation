#include "logger.h"
#include <iostream>
#include <iomanip>
#include <ctime>
#include <chrono>

namespace igsoa {

Logger::Logger()
    : console_level_(Level::WARNING),
      file_level_(Level::DEBUG),
      initialized_(false),
      filename_("igsoa_sim.log") {
}

Logger::~Logger() {
    shutdown();
}

Logger& Logger::getInstance() {
    static Logger instance;
    return instance;
}

void Logger::initialize(const std::string& filename, Level console_level, Level file_level) {
    std::lock_guard<std::mutex> lock(mutex_);

    // Close existing file if open
    if (file_.is_open()) {
        file_.close();
    }

    filename_ = filename;
    console_level_ = console_level;
    file_level_ = file_level;

    // Open log file in append mode
    file_.open(filename_, std::ios::out | std::ios::app);

    if (!file_.is_open()) {
        std::cerr << "[Logger] WARNING: Failed to open log file: " << filename_ << std::endl;
        std::cerr << "[Logger] Logging to console only." << std::endl;
        initialized_ = false;
        return;
    }

    initialized_ = true;

    // Log initialization
    file_ << "\n========================================\n";
    file_ << "Logger initialized: " << getCurrentTimestamp() << "\n";
    file_ << "Log file: " << filename_ << "\n";
    file_ << "Console level: " << levelToString(console_level_) << "\n";
    file_ << "File level: " << levelToString(file_level_) << "\n";
    file_ << "========================================\n\n";
    file_.flush();
}

void Logger::setConsoleLevel(Level level) {
    std::lock_guard<std::mutex> lock(mutex_);
    console_level_ = level;
}

void Logger::setFileLevel(Level level) {
    std::lock_guard<std::mutex> lock(mutex_);
    file_level_ = level;
}

void Logger::log(Level level, const std::string& message, const char* file, int line) {
    std::lock_guard<std::mutex> lock(mutex_);

    // Build log message
    std::ostringstream oss;
    oss << "[" << getCurrentTimestamp() << "] ";
    oss << "[" << levelToString(level) << "] ";

    // Add file:line if provided
    if (file != nullptr && line >= 0) {
        oss << "[" << extractFilename(file) << ":" << line << "] ";
    }

    oss << message;

    std::string formatted_message = oss.str();

    // Log to console if level is sufficient
    if (shouldLog(level, console_level_)) {
        if (level >= Level::ERROR) {
            std::cerr << formatted_message << std::endl;
        } else {
            std::cout << formatted_message << std::endl;
        }
    }

    // Log to file if initialized and level is sufficient
    if (initialized_ && file_.is_open() && shouldLog(level, file_level_)) {
        file_ << formatted_message << "\n";
        file_.flush();  // Ensure immediate write (important for errors)
    }
}

void Logger::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (initialized_ && file_.is_open()) {
        file_ << "\n========================================\n";
        file_ << "Logger shutdown: " << getCurrentTimestamp() << "\n";
        file_ << "========================================\n\n";
        file_.close();
    }

    initialized_ = false;
}

const char* Logger::levelToString(Level level) {
    switch (level) {
        case Level::DEBUG:   return "DEBUG";
        case Level::INFO:    return "INFO";
        case Level::WARNING: return "WARNING";
        case Level::ERROR:   return "ERROR";
        case Level::FATAL:   return "FATAL";
        default:             return "UNKNOWN";
    }
}

std::string Logger::getCurrentTimestamp() {
    // Get current time
    auto now = std::chrono::system_clock::now();
    auto now_c = std::chrono::system_clock::to_time_t(now);
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    ) % 1000;

    // Format: YYYY-MM-DD HH:MM:SS.mmm
    std::ostringstream oss;
    std::tm tm_buf;

#ifdef _WIN32
    localtime_s(&tm_buf, &now_c);
#else
    localtime_r(&now_c, &tm_buf);
#endif

    oss << std::put_time(&tm_buf, "%Y-%m-%d %H:%M:%S");
    oss << "." << std::setfill('0') << std::setw(3) << now_ms.count();

    return oss.str();
}

std::string Logger::extractFilename(const char* filepath) {
    if (filepath == nullptr) {
        return "";
    }

    std::string path(filepath);

    // Find last slash or backslash
    size_t pos = path.find_last_of("/\\");
    if (pos != std::string::npos) {
        return path.substr(pos + 1);
    }

    return path;
}

bool Logger::shouldLog(Level level, Level threshold) {
    return static_cast<int>(level) >= static_cast<int>(threshold);
}

} // namespace igsoa
