"""
Logging configuration for LumiLens API.

This module provides centralized logging setup with proper formatting,
file rotation, and different log levels for development and production.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from api.config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Configure application logging with proper formatting and handlers.
    
    Args:
        log_level: Override default log level from settings
        log_file: Optional log file path for file handler
    """
    # Determine log level
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=settings.LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler to prevent large log files
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for specific loggers to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    
    # Log initial message
    logger = logging.getLogger(__name__)
    logger.info("🔧 Logging configured successfully")
    logger.info("📊 Log level: %s", level.upper())
    if log_file:
        logger.info("📁 Log file: %s", log_file)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
