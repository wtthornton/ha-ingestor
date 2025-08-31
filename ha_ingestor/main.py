"""Main entry point for HA-Ingestor application.

This module provides the primary entry point for the HA-Ingestor service,
importing and delegating to the core application module.
"""

from .core.application import cli, main

# For backwards compatibility
__all__ = ["main", "cli"]

if __name__ == "__main__":
    exit(cli())
