"""
Performance Metrics Collection Framework
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import logging

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


@dataclass
class MetricPoint:
    """Single metric data point"""
    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, Any]
    timestamp: datetime
    service: str


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    operation: str
    duration_ms: float
    status: str
    timestamp: datetime
    service: str
    correlation_id: Optional[str] = None
    additional_metrics: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """Core metrics collection framework"""
    
    def __init__(self, service_name: str, influxdb_client: Optional[InfluxDBClient] = None):
        self.service_name = service_name
        self.influxdb_client = influxdb_client
        self.metrics_buffer: List[MetricPoint] = []
        self.buffer_lock = threading.Lock()
        self.buffer_size = 1000
        self.flush_interval = 30  # seconds
        
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # System metrics
        self.system_metrics_enabled = True
        self.system_metrics_interval = 30  # seconds
        
        # Background tasks
        self._flush_task: Optional[asyncio.Task] = None
        self._system_metrics_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Logger
        self.logger = logging.getLogger(f"metrics.{service_name}")
    
    async def start(self):
        """Start metrics collection"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._flush_task = asyncio.create_task(self._flush_loop())
        
        if self.system_metrics_enabled:
            self._system_metrics_task = asyncio.create_task(self._system_metrics_loop())
        
        self.logger.info(f"Metrics collector started for service: {self.service_name}")
    
    async def stop(self):
        """Stop metrics collection"""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel background tasks
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        if self._system_metrics_task:
            self._system_metrics_task.cancel()
            try:
                await self._system_metrics_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining metrics
        await self._flush_metrics()
        
        self.logger.info(f"Metrics collector stopped for service: {self.service_name}")
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        
        point = MetricPoint(
            measurement="counters",
            tags=tags or {},
            fields={name: self.counters[name]},
            timestamp=datetime.utcnow(),
            service=self.service_name
        )
        
        self._add_to_buffer(point)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        self.gauges[name] = value
        
        point = MetricPoint(
            measurement="gauges",
            tags=tags or {},
            fields={name: value},
            timestamp=datetime.utcnow(),
            service=self.service_name
        )
        
        self._add_to_buffer(point)
    
    def record_timer(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        self.timers[name].append(duration_ms)
        
        # Calculate percentiles
        values = list(self.timers[name])
        values.sort()
        
        percentiles = {}
        if values:
            percentiles = {
                f"{name}_p50": values[int(len(values) * 0.5)],
                f"{name}_p95": values[int(len(values) * 0.95)] if len(values) > 20 else values[-1],
                f"{name}_p99": values[int(len(values) * 0.99)] if len(values) > 100 else values[-1],
                f"{name}_avg": sum(values) / len(values),
                f"{name}_min": min(values),
                f"{name}_max": max(values)
            }
        
        point = MetricPoint(
            measurement="timers",
            tags=tags or {},
            fields=percentiles,
            timestamp=datetime.utcnow(),
            service=self.service_name
        )
        
        self._add_to_buffer(point)
    
    def record_performance_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        tags = {
            "operation": metrics.operation,
            "status": metrics.status,
            "service": metrics.service
        }
        
        if metrics.correlation_id:
            tags["correlation_id"] = metrics.correlation_id
        
        fields = {
            "duration_ms": metrics.duration_ms
        }
        
        if metrics.additional_metrics:
            fields.update(metrics.additional_metrics)
        
        point = MetricPoint(
            measurement="performance",
            tags=tags,
            fields=fields,
            timestamp=metrics.timestamp,
            service=metrics.service
        )
        
        self._add_to_buffer(point)
    
    def _add_to_buffer(self, point: MetricPoint):
        """Add metric point to buffer"""
        with self.buffer_lock:
            self.metrics_buffer.append(point)
            
            # Flush if buffer is full
            if len(self.metrics_buffer) >= self.buffer_size:
                asyncio.create_task(self._flush_metrics())
    
    async def _flush_loop(self):
        """Background task to flush metrics periodically"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in flush loop: {e}")
    
    async def _flush_metrics(self):
        """Flush buffered metrics to InfluxDB"""
        if not self.influxdb_client or not self.metrics_buffer:
            return
        
        with self.buffer_lock:
            if not self.metrics_buffer:
                return
            
            points_to_flush = self.metrics_buffer.copy()
            self.metrics_buffer.clear()
        
        try:
            write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
            
            influx_points = []
            for point in points_to_flush:
                influx_point = Point(point.measurement)
                
                # Add tags
                for key, value in point.tags.items():
                    influx_point = influx_point.tag(key, value)
                
                # Add fields
                for key, value in point.fields.items():
                    if isinstance(value, (int, float)):
                        influx_point = influx_point.field(key, value)
                    else:
                        influx_point = influx_point.field(key, str(value))
                
                influx_point = influx_point.time(point.timestamp)
                influx_points.append(influx_point)
            
            # Write to InfluxDB
            write_api.write(bucket="ha-ingestor-metrics", record=influx_points)
            write_api.close()
            
            self.logger.debug(f"Flushed {len(points_to_flush)} metrics to InfluxDB")
            
        except Exception as e:
            self.logger.error(f"Error flushing metrics to InfluxDB: {e}")
            # Put metrics back in buffer on error
            with self.buffer_lock:
                self.metrics_buffer.extend(points_to_flush)
    
    async def _system_metrics_loop(self):
        """Background task to collect system metrics"""
        while self._running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.system_metrics_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process = psutil.Process()
            process_cpu_percent = process.cpu_percent()
            process_memory_info = process.memory_info()
            process_memory_percent = process.memory_percent()
            
            # Create system metrics point
            point = MetricPoint(
                measurement="system_metrics",
                tags={"service": self.service_name},
                fields={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "memory_percent": memory_percent,
                    "memory_used_bytes": memory_used,
                    "memory_total_bytes": memory_total,
                    "disk_percent": disk_percent,
                    "disk_used_bytes": disk_used,
                    "disk_total_bytes": disk_total,
                    "network_bytes_sent": network_bytes_sent,
                    "network_bytes_recv": network_bytes_recv,
                    "process_cpu_percent": process_cpu_percent,
                    "process_memory_rss": process_memory_info.rss,
                    "process_memory_vms": process_memory_info.vms,
                    "process_memory_percent": process_memory_percent
                },
                timestamp=datetime.utcnow(),
                service=self.service_name
            )
            
            self._add_to_buffer(point)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return {
            "service": self.service_name,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {name: list(timer) for name, timer in self.timers.items()},
            "buffer_size": len(self.metrics_buffer),
            "running": self._running
        }


class PerformanceMonitor:
    """Performance monitoring decorator and context manager"""
    
    def __init__(self, metrics_collector: MetricsCollector, operation: str):
        self.metrics_collector = metrics_collector
        self.operation = operation
        self.start_time = None
        self.correlation_id = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
        status = "error" if exc_type else "success"
        
        metrics = PerformanceMetrics(
            operation=self.operation,
            duration_ms=duration,
            status=status,
            timestamp=datetime.utcnow(),
            service=self.metrics_collector.service_name,
            correlation_id=self.correlation_id
        )
        
        self.metrics_collector.record_performance_metrics(metrics)
    
    def set_correlation_id(self, corr_id: str):
        """Set correlation ID for this operation"""
        self.correlation_id = corr_id


def performance_monitor(metrics_collector: MetricsCollector, operation: str = None):
    """Decorator for automatic performance monitoring"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            with PerformanceMonitor(metrics_collector, op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class SystemMetricsCollector:
    """System-wide metrics collection"""
    
    def __init__(self, influxdb_client: Optional[InfluxDBClient] = None):
        self.influxdb_client = influxdb_client
        self.collectors: Dict[str, MetricsCollector] = {}
        self._running = False
    
    def register_service(self, service_name: str) -> MetricsCollector:
        """Register a service for metrics collection"""
        if service_name not in self.collectors:
            collector = MetricsCollector(service_name, self.influxdb_client)
            self.collectors[service_name] = collector
        return self.collectors[service_name]
    
    async def start_all(self):
        """Start all registered collectors"""
        self._running = True
        for collector in self.collectors.values():
            await collector.start()
    
    async def stop_all(self):
        """Stop all registered collectors"""
        self._running = False
        for collector in self.collectors.values():
            await collector.stop()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics summary for all services"""
        return {
            service: collector.get_metrics_summary()
            for service, collector in self.collectors.items()
        }


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector(service_name: str) -> MetricsCollector:
    """Get or create metrics collector for a service"""
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector(service_name)
    
    return _global_metrics_collector


def setup_metrics_collection(service_name: str, influxdb_client: Optional[InfluxDBClient] = None) -> MetricsCollector:
    """Setup metrics collection for a service"""
    collector = MetricsCollector(service_name, influxdb_client)
    return collector
