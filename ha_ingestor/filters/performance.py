"""Performance profiling utilities for the filter system."""

import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import defaultdict, deque

from ..utils.logging import get_logger
from ..models.events import Event
from .base import Filter, FilterChain

logger = get_logger(__name__)


@dataclass
class FilterProfile:
    """Profile information for a single filter."""
    
    filter_name: str
    filter_type: str
    total_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    events_filtered: int = 0
    events_passed: int = 0
    last_call_time: Optional[float] = None
    
    def update(self, processing_time_ms: float, cache_hit: bool, event_filtered: bool) -> None:
        """Update profile with new execution data."""
        self.total_calls += 1
        self.total_time_ms += processing_time_ms
        self.avg_time_ms = self.total_time_ms / self.total_calls
        self.min_time_ms = min(self.min_time_ms, processing_time_ms)
        self.max_time_ms = max(self.max_time_ms, processing_time_ms)
        self.last_call_time = time.time()
        
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
            
        if event_filtered:
            self.events_filtered += 1
        else:
            self.events_passed += 1


@dataclass
class FilterChainProfile:
    """Profile information for a filter chain."""
    
    chain_name: str
    total_events: int = 0
    total_filtered: int = 0
    total_passed: int = 0
    total_processing_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    min_processing_time_ms: float = float('inf')
    max_processing_time_ms: float = 0.0
    filter_profiles: Dict[str, FilterProfile] = field(default_factory=dict)
    recent_processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def update_chain_stats(self, total_time_ms: float, event_filtered: bool) -> None:
        """Update chain-level statistics."""
        self.total_events += 1
        self.total_processing_time_ms += total_time_ms
        self.avg_processing_time_ms = self.total_processing_time_ms / self.total_events
        self.min_processing_time_ms = min(self.min_processing_time_ms, total_time_ms)
        self.max_processing_time_ms = max(self.max_processing_time_ms, total_time_ms)
        self.recent_processing_times.append(total_time_ms)
        
        if event_filtered:
            self.total_filtered += 1
        else:
            self.total_passed += 1
    
    def get_filter_rate(self) -> float:
        """Get the rate of events filtered out."""
        return self.total_filtered / max(self.total_events, 1)
    
    def get_percentile_time(self, percentile: float) -> float:
        """Get the processing time at a specific percentile."""
        if not self.recent_processing_times:
            return 0.0
        
        sorted_times = sorted(self.recent_processing_times)
        n = len(sorted_times)
        
        if n == 1:
            return sorted_times[0]
        
        # Calculate the position for the percentile
        # For 80th percentile of 5 values: position = 0.8 * (5-1) = 3.2
        position = (percentile / 100.0) * (n - 1)
        
        # Get the lower and upper indices
        lower_index = int(position)
        upper_index = min(lower_index + 1, n - 1)
        
        # Calculate the fractional part
        fraction = position - lower_index
        
        # Interpolate between the two values
        if fraction == 0:
            return sorted_times[lower_index]
        else:
            return sorted_times[lower_index] * (1 - fraction) + sorted_times[upper_index] * fraction


class FilterProfiler:
    """Profiler for monitoring and optimizing filter performance."""
    
    def __init__(self, enabled: bool = True):
        """Initialize the filter profiler.
        
        Args:
            enabled: Whether profiling is enabled
        """
        self.enabled = enabled
        self.logger = get_logger(__name__)
        self.chain_profiles: Dict[str, FilterChainProfile] = {}
        self._start_time = time.time()
        
    def start_profiling_chain(self, chain: FilterChain) -> None:
        """Start profiling a filter chain.
        
        Args:
            chain: The filter chain to profile
        """
        if not self.enabled:
            return
            
        if chain.name not in self.chain_profiles:
            self.chain_profiles[chain.name] = FilterChainProfile(chain.name)
            
        # Initialize filter profiles
        for filter_obj in chain.filters:
            filter_key = f"{filter_obj.name}_{filter_obj._filter_type}"
            if filter_key not in self.chain_profiles[chain.name].filter_profiles:
                self.chain_profiles[chain.name].filter_profiles[filter_key] = FilterProfile(
                    filter_obj.name, filter_obj._filter_type
                )
    
    def record_filter_execution(self, chain_name: str, filter_name: str, filter_type: str,
                              processing_time_ms: float, cache_hit: bool, event_filtered: bool) -> None:
        """Record execution metrics for a filter.
        
        Args:
            chain_name: Name of the filter chain
            filter_name: Name of the filter
            filter_type: Type of the filter
            processing_time_ms: Processing time in milliseconds
            cache_hit: Whether this was a cache hit
            event_filtered: Whether the event was filtered out
        """
        if not self.enabled:
            return
            
        if chain_name not in self.chain_profiles:
            return
            
        filter_key = f"{filter_name}_{filter_type}"
        if filter_key in self.chain_profiles[chain_name].filter_profiles:
            self.chain_profiles[chain_name].filter_profiles[filter_key].update(
                processing_time_ms, cache_hit, event_filtered
            )
    
    def record_chain_execution(self, chain_name: str, total_time_ms: float, event_filtered: bool) -> None:
        """Record execution metrics for a filter chain.
        
        Args:
            chain_name: Name of the filter chain
            total_time_ms: Total processing time in milliseconds
            event_filtered: Whether the event was filtered out
        """
        if not self.enabled:
            return
            
        if chain_name in self.chain_profiles:
            self.chain_profiles[chain_name].update_chain_stats(total_time_ms, event_filtered)
    
    def get_chain_profile(self, chain_name: str) -> Optional[FilterChainProfile]:
        """Get profile for a specific filter chain.
        
        Args:
            chain_name: Name of the chain
            
        Returns:
            FilterChainProfile if found, None otherwise
        """
        return self.chain_profiles.get(chain_name)
    
    def get_all_profiles(self) -> Dict[str, FilterChainProfile]:
        """Get all filter chain profiles.
        
        Returns:
            Dictionary of all chain profiles
        """
        return self.chain_profiles.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all performance metrics.
        
        Returns:
            Dictionary with performance summary
        """
        if not self.chain_profiles:
            return {"message": "No filter chains profiled yet"}
        
        summary = {
            "total_chains": len(self.chain_profiles),
            "uptime_seconds": time.time() - self._start_time,
            "chains": {}
        }
        
        for chain_name, profile in self.chain_profiles.items():
            summary["chains"][chain_name] = {
                "total_events": profile.total_events,
                "filter_rate": profile.get_filter_rate(),
                "avg_processing_time_ms": profile.avg_processing_time_ms,
                "p95_processing_time_ms": profile.get_percentile_time(95),
                "p99_processing_time_ms": profile.get_percentile_time(99),
                "total_filters": len(profile.filter_profiles),
                "filters": {}
            }
            
            for filter_key, filter_profile in profile.filter_profiles.items():
                summary["chains"][chain_name]["filters"][filter_key] = {
                    "total_calls": filter_profile.total_calls,
                    "avg_time_ms": filter_profile.avg_time_ms,
                    "cache_hit_rate": filter_profile.cache_hits / max(filter_profile.total_calls, 1),
                    "events_filtered": filter_profile.events_filtered,
                    "events_passed": filter_profile.events_passed
                }
        
        return summary
    
    def identify_bottlenecks(self, chain_name: str) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in a filter chain.
        
        Args:
            chain_name: Name of the chain to analyze
            
        Returns:
            List of bottleneck information
        """
        if chain_name not in self.chain_profiles:
            return []
        
        profile = self.chain_profiles[chain_name]
        bottlenecks = []
        
        # Check for slow filters
        for filter_key, filter_profile in profile.filter_profiles.items():
            if filter_profile.avg_time_ms > 10.0:  # Flag filters taking >10ms on average
                bottlenecks.append({
                    "type": "slow_filter",
                    "filter": filter_key,
                    "avg_time_ms": filter_profile.avg_time_ms,
                    "recommendation": "Consider optimizing filter logic or adding caching"
                })
            
            # Check for low cache hit rates
            cache_hit_rate = filter_profile.cache_hits / max(filter_profile.total_calls, 1)
            if filter_profile.total_calls > 100 and cache_hit_rate < 0.1:  # <10% cache hit rate
                bottlenecks.append({
                    "type": "low_cache_efficiency",
                    "filter": filter_key,
                    "cache_hit_rate": cache_hit_rate,
                    "recommendation": "Review cache key strategy or increase cache size"
                })
        
        # Check overall chain performance
        if profile.avg_processing_time_ms > 50.0:  # >50ms average
            bottlenecks.append({
                "type": "slow_chain",
                "avg_time_ms": profile.avg_processing_time_ms,
                "recommendation": "Consider reducing number of filters or optimizing filter order"
            })
        
        return bottlenecks
    
    def clear_profiles(self) -> None:
        """Clear all profiling data."""
        self.chain_profiles.clear()
        self._start_time = time.time()
        self.logger.info("Cleared all filter profiles")
    
    def export_profile_data(self, format: str = "json") -> str:
        """Export profile data in the specified format.
        
        Args:
            format: Export format ("json" or "csv")
            
        Returns:
            Exported data as string
        """
        if format.lower() == "json":
            import json
            return json.dumps(self.get_performance_summary(), indent=2)
        elif format.lower() == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self) -> str:
        """Export profile data as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Chain", "Filter", "Total Calls", "Avg Time (ms)", 
            "Cache Hit Rate", "Events Filtered", "Events Passed"
        ])
        
        # Write data
        for chain_name, profile in self.chain_profiles.items():
            for filter_key, filter_profile in profile.filter_profiles.items():
                cache_hit_rate = filter_profile.cache_hits / max(filter_profile.total_calls, 1)
                writer.writerow([
                    chain_name,
                    filter_key,
                    filter_profile.total_calls,
                    f"{filter_profile.avg_time_ms:.2f}",
                    f"{cache_hit_rate:.2f}",
                    filter_profile.events_filtered,
                    filter_profile.events_passed
                ])
        
        return output.getvalue()


# Global profiler instance
_global_profiler: Optional[FilterProfiler] = None


def get_filter_profiler() -> FilterProfiler:
    """Get the global filter profiler instance.
    
    Returns:
        Global FilterProfiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = FilterProfiler()
    return _global_profiler


@asynccontextmanager
async def profile_filter_execution(chain_name: str, filter_name: str, filter_type: str):
    """Context manager for profiling filter execution.
    
    Args:
        chain_name: Name of the filter chain
        filter_name: Name of the filter
        filter_type: Type of the filter
        
    Yields:
        None
    """
    profiler = get_filter_profiler()
    start_time = time.time()
    
    try:
        yield
    finally:
        processing_time = (time.time() - start_time) * 1000
        # Note: We can't determine cache_hit and event_filtered here
        # These should be recorded separately by the filter
        profiler.record_filter_execution(
            chain_name, filter_name, filter_type, processing_time, False, False
        )
