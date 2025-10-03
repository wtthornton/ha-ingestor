"""CLI commands package."""

from .system import app as system_app
from .events import app as events_app
from .config import app as config_app
from .export import app as export_app
from .diagnostics import app as diagnostics_app

__all__ = ["system_app", "events_app", "config_app", "export_app", "diagnostics_app"]
