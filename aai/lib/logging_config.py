"""Centralized logging configuration for aai pipeline.

Integrates with the existing --quiet CLI flag to control verbosity.
Provides structured exception logging with stack traces.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path


def configure_logging(quiet: bool = False, output_dir: str | Path | None = None) -> logging.Logger:
    """Configure and return the root logger for the aai pipeline.
    
    Parameters
    ----------
    quiet:
        If True, suppress INFO and DEBUG logs (only ERROR and CRITICAL shown).
    output_dir:
        Optional root output directory. If provided, logs are also written to a file.
    
    Returns
    -------
    logging.Logger
        Configured root logger instance.
    """
    root_logger = logging.getLogger("aai")
    
    # Clear any existing handlers (avoid duplicates on reconfiguration)
    root_logger.handlers.clear()
    
    # Set log level based on quiet flag
    log_level = logging.ERROR if quiet else logging.DEBUG
    root_logger.setLevel(log_level)
    
    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "[%(levelname)-8s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Optional file handler
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        log_file = output_path / ".eval.log"
        
        try:
            file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Always log DEBUG+ to file
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, just use console
            console_handler.emit(
                logging.LogRecord(
                    name="aai",
                    level=logging.WARNING,
                    pathname="",
                    lineno=0,
                    msg=f"Could not create log file at {log_file}: {e}",
                    args=(),
                    exc_info=None,
                )
            )
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance (e.g., 'aai.eval_runner', 'aai.agents').
    
    Parameters
    ----------
    name:
        Logger name, typically __name__ or a descriptive string.
    
    Returns
    -------
    logging.Logger
        Named logger instance.
    """
    return logging.getLogger(name)
