"""Utility functions for the Home Assistant Activity Ingestor."""

# Import utility functions
from .logging import (
    get_logger,
    get_logger_for_module,
    log_function_call,
    log_performance,
    setup_default_logging,
    setup_logging,
)

__all__ = [
    "setup_logging",
    "setup_default_logging",
    "get_logger",
    "get_logger_for_module",
    "log_function_call",
    "log_performance",
]
