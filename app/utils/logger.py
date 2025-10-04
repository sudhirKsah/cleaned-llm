"""
Simple logging configuration for the Mistral API server.
"""
import logging
import sys
from typing import Optional

from app.config.settings import settings


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Setup and configure logger."""
    logger = logging.getLogger(name or __name__)
    
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger("mistral_api")
