"""Home Assistant Activity Ingestor.

A production-grade Python service that ingests all relevant Home Assistant
activity in real-time and writes it to InfluxDB.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import main components once they're implemented
from .config import Settings, get_settings, reload_settings
# from .main import IngestorService

# Import modules to make them available at package level
from . import mqtt
from . import websocket
from . import influxdb
from . import models
from . import utils

__all__ = [
    "__version__", "__author__", "__email__",
    "Settings", "get_settings", "reload_settings",
    "mqtt", "websocket", "influxdb", "models", "utils"
]
