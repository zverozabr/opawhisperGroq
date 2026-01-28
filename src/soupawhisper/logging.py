"""Logging configuration."""

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(
    debug: bool = False,
    log_file: Path | None = None,
    tui_mode: bool = False,
) -> logging.Logger:
    """Configure application logging.

    Args:
        debug: Enable debug level logging
        log_file: Optional file path for logging
        tui_mode: If True, disable console output (TUI handles display)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("soupawhisper")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler - skip in TUI mode to avoid messing up display
    if not tui_mode:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG if debug else logging.INFO)
        console.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(console)

    # File handler (optional, or always in TUI mode with debug)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the application logger."""
    return logging.getLogger("soupawhisper")
