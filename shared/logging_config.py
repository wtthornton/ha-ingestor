"""
Shared Logging Configuration
"""

import logging
import os
import sys
from datetime import datetime


def setup_logging(service_name: str, log_level: str = None):
    """
    Set up logging configuration for a service
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get log level from environment or parameter
    level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(service_name: str):
    """
    Get a logger for a specific service
    
    Args:
        service_name: Name of the service
        
    Returns:
        Logger instance
    """
    return logging.getLogger(service_name)
