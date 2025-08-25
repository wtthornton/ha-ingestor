"""
A production-grade Python service that ingests all relevant Home Assistant
activity in real-time and writes it to InfluxDB.
"""

__version__ = "0.3.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main components once they're implemented
# from .main import IngestorService
# Import modules to make them available at package level
from . import influxdb, models, mqtt, utils, websocket
from .config import Settings, get_settings, reload_settings

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Settings",
    "get_settings",
    "reload_settings",
    "mqtt",
    "websocket",
    "influxdb",
    "models",
    "utils",
]
