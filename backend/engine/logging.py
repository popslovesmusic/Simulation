"""Logging helpers for the backend engine runtime."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

_ENGINE_LOGGER_NAME = "backend.engine"


def configure_engine_logging(
    log_file: Optional[Path] = None, level: int = logging.INFO
) -> logging.Logger:
    """Configure and return the shared engine logger."""

    logger = logging.getLogger(_ENGINE_LOGGER_NAME)
    logger.setLevel(level)

    if not logger.handlers:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(stream_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger


def get_engine_logger() -> logging.Logger:
    """Return a logger instance configured for engine components."""

    logger = logging.getLogger(_ENGINE_LOGGER_NAME)
    if not logger.handlers:
        configure_engine_logging()
    return logger


__all__ = ["configure_engine_logging", "get_engine_logger"]
