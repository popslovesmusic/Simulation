"""
IGSOA-SIM Python Logging Configuration

Provides standardized logging setup for all Python scripts in the project.

Usage:
    from igsoa_logging import setup_logging, get_logger

    # In main script:
    setup_logging()

    # In any module:
    logger = get_logger(__name__)
    logger.info("Processing data...")
    logger.error("An error occurred")
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_file='igsoa_sim.log',
    level=logging.INFO,
    console_level=logging.WARNING,
    format_string=None
):
    """
    Configure logging for IGSOA-SIM Python scripts.

    Args:
        log_file: Path to log file (default: 'igsoa_sim.log')
        level: File logging level (default: INFO)
        console_level: Console logging level (default: WARNING)
        format_string: Custom format string (optional)

    Returns:
        The root logger instance
    """
    # Create formatter
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    formatter = logging.Formatter(
        format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler - logs everything at specified level
    try:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)
        print("Logging to console only.", file=sys.stderr)

    # Console handler - logs warnings and errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set root logger level
    root_logger.setLevel(min(level, console_level))

    # Log initialization
    root_logger.info("=" * 50)
    root_logger.info(f"IGSOA-SIM Logging initialized")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"File level: {logging.getLevelName(level)}")
    root_logger.info(f"Console level: {logging.getLevelName(console_level)}")
    root_logger.info("=" * 50)

    return root_logger


def get_logger(name):
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Usage:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(name)


def log_exception(logger, exc, message="An error occurred"):
    """
    Log an exception with full traceback.

    Args:
        logger: Logger instance
        exc: Exception object
        message: Context message

    Usage:
        try:
            risky_operation()
        except Exception as e:
            log_exception(logger, e, "Failed to process data")
    """
    logger.error(f"{message}: {exc}", exc_info=True)


def create_timestamped_log(base_name='igsoa_sim'):
    """
    Create a timestamped log filename.

    Args:
        base_name: Base name for log file

    Returns:
        Log filename with timestamp

    Example:
        >>> create_timestamped_log('simulation')
        'simulation_20250111_120530.log'
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_{timestamp}.log"


# Convenience functions for quick logging without setup
def quick_log_info(message, log_file='igsoa_sim.log'):
    """Quick info logging without explicit setup."""
    logger = logging.getLogger('igsoa_quick')
    if not logger.handlers:
        setup_logging(log_file=log_file)
    logger.info(message)


def quick_log_error(message, log_file='igsoa_sim.log'):
    """Quick error logging without explicit setup."""
    logger = logging.getLogger('igsoa_quick')
    if not logger.handlers:
        setup_logging(log_file=log_file)
    logger.error(message)


def quick_log_warning(message, log_file='igsoa_sim.log'):
    """Quick warning logging without explicit setup."""
    logger = logging.getLogger('igsoa_quick')
    if not logger.handlers:
        setup_logging(log_file=log_file)
    logger.warning(message)


# Example usage
if __name__ == '__main__':
    # Test the logging system
    setup_logging(
        log_file='test_logging.log',
        level=logging.DEBUG,
        console_level=logging.INFO
    )

    logger = get_logger(__name__)

    logger.debug("This is a debug message (file only)")
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Test exception logging
    try:
        result = 1 / 0
    except ZeroDivisionError as e:
        log_exception(logger, e, "Math error occurred")

    print("\nLogging test complete. Check 'test_logging.log' for full output.")
