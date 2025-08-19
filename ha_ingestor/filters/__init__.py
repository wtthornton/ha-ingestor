"""Filter system for Home Assistant event processing.

This module provides a configurable filtering system that allows users to:
- Filter events by domain, entity, and attributes
- Apply custom transformation rules
- Chain multiple filters together for complex processing
- Optimize performance with caching and compiled patterns
"""

from .base import Filter, FilterChain
from .domain_filter import DomainFilter
from .entity_filter import EntityFilter
from .attribute_filter import AttributeFilter
from .time_filter import TimeFilter
from .custom_filter import CustomFilter

__all__ = [
    "Filter",
    "FilterChain",
    "DomainFilter",
    "EntityFilter",
    "AttributeFilter",
    "TimeFilter",
    "CustomFilter",
]
