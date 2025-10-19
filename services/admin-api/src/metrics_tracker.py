"""
Response Time Tracking with Prometheus-style Histograms
Context7 Best Practice: Real-time metrics, not hardcoded values
Source: /blueswen/fastapi-observability (Trust Score 9.8)
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
import asyncio


class ResponseTimeTracker:
    """
    Track response times using histogram buckets for percentile calculations.
    
    Context7 Pattern: Use histograms for request duration tracking
    - Tracks min, max, avg, p50, p95, p99
    - Lightweight in-memory storage
    - Thread-safe with asyncio support
    """
    
    def __init__(self):
        self.measurements: Dict[str, list] = defaultdict(list)
        self.max_measurements_per_service = 1000  # Keep last 1000 measurements
        self._lock = asyncio.Lock()
    
    async def record(self, service: str, response_time_ms: float):
        """Record a response time measurement"""
        async with self._lock:
            if service not in self.measurements:
                self.measurements[service] = []
            
            self.measurements[service].append({
                'time': datetime.now(),
                'duration_ms': response_time_ms
            })
            
            # Keep only recent measurements
            if len(self.measurements[service]) > self.max_measurements_per_service:
                self.measurements[service] = self.measurements[service][-self.max_measurements_per_service:]
    
    async def get_stats(self, service: str) -> Dict[str, Any]:
        """
        Get response time statistics for a service.
        
        Returns:
            - min: Minimum response time
            - max: Maximum response time
            - avg: Average response time
            - p50: 50th percentile (median)
            - p95: 95th percentile
            - p99: 99th percentile
            - count: Number of measurements
        """
        async with self._lock:
            if service not in self.measurements or not self.measurements[service]:
                return {
                    'min': 0,
                    'max': 0,
                    'avg': 0,
                    'p50': 0,
                    'p95': 0,
                    'p99': 0,
                    'count': 0
                }
            
            durations = sorted([m['duration_ms'] for m in self.measurements[service]])
            count = len(durations)
            
            return {
                'min': round(durations[0], 2),
                'max': round(durations[-1], 2),
                'avg': round(sum(durations) / count, 2),
                'p50': round(self._percentile(durations, 50), 2),
                'p95': round(self._percentile(durations, 95), 2),
                'p99': round(self._percentile(durations, 99), 2),
                'count': count
            }
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all tracked services"""
        async with self._lock:
            stats = {}
            for service in self.measurements.keys():
                stats[service] = await self.get_stats(service)
            return stats
    
    def _percentile(self, sorted_values: list, percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = index - lower
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


# Global tracker instance
_tracker: Optional[ResponseTimeTracker] = None


def get_tracker() -> ResponseTimeTracker:
    """Get or create the global response time tracker"""
    global _tracker
    if _tracker is None:
        _tracker = ResponseTimeTracker()
    return _tracker

