"""
Logging Configuration Module.

This module provides a centralized logging configuration with rotating file handlers
for the MarkItDown Converter application.

Example:
    >>> from src.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Conversion started")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    log_level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Creates and configures a logger with rotating file handler.

    This function sets up a logger that writes to both console and a rotating
    log file. The log file automatically rotates when it reaches the specified
    size limit.

    Args:
        name: The name of the logger (typically __name__).
        log_dir: Directory where log files will be stored.
            Defaults to 'logs' in the project root.
        log_level: The minimum logging level. Defaults to INFO.
        max_bytes: Maximum size of each log file before rotation.
            Defaults to 5 MB.
        backup_count: Number of backup files to keep. Defaults to 5.

    Returns:
        logging.Logger: Configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing file: document.pdf")
        >>> logger.error("Conversion failed", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # Determine log directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_formatter = logging.Formatter(
        fmt="%(levelname)-8s | %(message)s"
    )
    
    # Rotating File Handler
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_audit_logger(
    log_dir: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 10
) -> logging.Logger:
    """
    Creates a specialized audit logger for tracking conversion attempts.

    This logger is specifically designed to track all conversion operations,
    recording success and failure states for auditing purposes.

    Args:
        log_dir: Directory where audit log files will be stored.
            Defaults to 'logs' in the project root.
        max_bytes: Maximum size of each audit log file before rotation.
            Defaults to 10 MB.
        backup_count: Number of backup files to keep. Defaults to 10.

    Returns:
        logging.Logger: Configured audit logger instance.

    Example:
        >>> audit = get_audit_logger()
        >>> audit.info("SUCCESS | document.pdf -> document.md | 2.5s")
        >>> audit.error("FAILED | corrupted.pdf | UnsupportedFileError")
    """
    logger = logging.getLogger("audit")
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Determine log directory
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    audit_file = log_dir / "audit.log"
    
    # Audit-specific formatter
    audit_formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Rotating File Handler for audit
    file_handler = RotatingFileHandler(
        filename=audit_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(audit_formatter)
    
    logger.addHandler(file_handler)
    
    return logger
