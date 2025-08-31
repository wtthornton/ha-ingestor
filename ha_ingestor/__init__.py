"""
HA-Ingestor: Enhanced Data Ingestion & Preparation Layer for Home Assistant

A production-grade Python service that ingests Home Assistant activity data
in real-time and writes it to InfluxDB with advanced filtering, transformation,
and monitoring capabilities.
"""

__version__ = "0.3.0"
__author__ = "HA-Ingestor Team"
__email__ = "ha-ingestor@example.com"

from . import (
    filters,
    interfaces,
    metrics,
    models,
    monitoring,
    services,
    transformers,
    utils,
)

# Import core functionality with new organized structure
from .core import EventProcessor, PipelineStats, Settings, get_settings
from .main import cli, main

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    # Core functionality
    "Settings",
    "get_settings",
    "EventProcessor",
    "PipelineStats",
    "main",
    "cli",
    # Modules
    "services",
    "interfaces",
    "models",
    "utils",
    "filters",
    "transformers",
    "metrics",
    "monitoring",
]
