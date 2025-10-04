# Performance Standards

This document defines performance standards, monitoring requirements, and optimization strategies for the Home Assistant Ingestor project.

## Performance Framework Overview

The Home Assistant Ingestor implements comprehensive performance monitoring and optimization across all services to ensure reliable, scalable operation.

### Performance Domains

1. **Response Time** - API endpoint response times and latency
2. **Throughput** - Requests per second and data processing rates
3. **Resource Usage** - CPU, memory, and disk utilization
4. **Database Performance** - Query execution times and connection efficiency
5. **Network Performance** - Bandwidth usage and connection stability

## Response Time Standards

### API Performance Targets

#### Response Time Requirements
```python
# services/admin-api/src/performance_standards.py
from typing import Dict, Any

class PerformanceStandards:
    """Performance standards and targets"""
    
    # Response time targets (in milliseconds)
    RESPONSE_TIME_TARGETS = {
        "health_check": 100,      # Health check endpoints
        "read_operations": 500,   # GET requests
        "write_operations": 1000, # POST/PUT/PATCH requests
        "delete_operations": 800, # DELETE requests
        "complex_queries": 2000,  # Complex data queries
        "aggregation_queries": 3000, # Statistical aggregations
        "export_operations": 5000 # Data export operations
    }
    
    # Throughput targets (requests per second)
    THROUGHPUT_TARGETS = {
        "health_check": 1000,
        "read_operations": 500,
        "write_operations": 100,
        "delete_operations": 200,
        "complex_queries": 50,
        "aggregation_queries": 20,
        "export_operations": 5
    }
    
    # Resource usage limits
    RESOURCE_LIMITS = {
        "memory_per_service": 512,  # MB
        "cpu_percentage": 80,       # %
        "disk_io_ops": 1000,        # IOPS
        "network_bandwidth": 100,   # Mbps
        "database_connections": 20
    }
```

#### Performance Monitoring Implementation
```python
# services/admin-api/src/performance_monitor.py
import time
import psutil
from typing import Dict, Any
from datetime import datetime
import asyncio

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
    
    async def measure_endpoint_performance(self, endpoint: str, operation: str):
        """Decorator to measure endpoint performance"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success metrics
                    execution_time = (time.time() - start_time) * 1000  # Convert to ms
                    await self._record_metrics(endpoint, operation, execution_time, True)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    execution_time = (time.time() - start_time) * 1000
                    await self._record_metrics(endpoint, operation, execution_time, False, str(e))
                    raise
            
            return wrapper
        return decorator
    
    async def _record_metrics(self, endpoint: str, operation: str, 
                            execution_time: float, success: bool, error: str = None):
        """Record performance metrics"""
        metric_key = f"{endpoint}:{operation}"
        
        if metric_key not in self.metrics:
            self.metrics[metric_key] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "success_count": 0,
                "error_count": 0,
                "errors": []
            }
        
        metrics = self.metrics[metric_key]
        metrics["count"] += 1
        metrics["total_time"] += execution_time
        metrics["min_time"] = min(metrics["min_time"], execution_time)
        metrics["max_time"] = max(metrics["max_time"], execution_time)
        
        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1
            if error:
                metrics["errors"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": error
                })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {}
        
        for metric_key, metrics in self.metrics.items():
            avg_time = metrics["total_time"] / metrics["count"] if metrics["count"] > 0 else 0
            success_rate = (metrics["success_count"] / metrics["count"]) * 100 if metrics["count"] > 0 else 0
            
            summary[metric_key] = {
                "requests": metrics["count"],
                "avg_response_time_ms": round(avg_time, 2),
                "min_response_time_ms": round(metrics["min_time"], 2),
                "max_response_time_ms": round(metrics["max_time"], 2),
                "success_rate_percent": round(success_rate, 2),
                "error_count": metrics["error_count"]
            }
        
        return summary

# Usage example
performance_monitor = PerformanceMonitor()

@router.get("/events")
@performance_monitor.measure_endpoint_performance("/events", "read")
async def get_events():
    """Get events with performance monitoring"""
    pass
```

## Resource Usage Monitoring

### System Resource Monitoring

#### Comprehensive Resource Tracking
```python
# services/admin-api/src/resource_monitor.py
import psutil
import asyncio
from typing import Dict, Any
from datetime import datetime

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.metrics_history = []
    
    async def start_monitoring(self, interval: int = 30):
        """Start continuous resource monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            metrics = self.get_current_metrics()
            self.metrics_history.append(metrics)
            
            # Keep only last 100 measurements
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
            
            # Check for resource violations
            await self._check_resource_limits(metrics)
            
            await asyncio.sleep(interval)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current resource usage metrics"""
        # Process metrics
        process_info = self.process
        memory_info = process_info.memory_info()
        cpu_percent = process_info.cpu_percent()
        
        # System metrics
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/')
        network_io = psutil.net_io_counters()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "process": {
                "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_percent": round(process_info.memory_percent(), 2),
                "cpu_percent": round(cpu_percent, 2),
                "threads": process_info.num_threads(),
                "open_files": len(process_info.open_files())
            },
            "system": {
                "memory_percent": round(system_memory.percent, 2),
                "cpu_percent": round(system_cpu, 2),
                "disk_percent": round(disk_usage.percent, 2),
                "network_bytes_sent": network_io.bytes_sent,
                "network_bytes_recv": network_io.bytes_recv
            }
        }
    
    async def _check_resource_limits(self, metrics: Dict[str, Any]):
        """Check if resource usage exceeds limits"""
        standards = PerformanceStandards()
        
        # Check memory usage
        memory_mb = metrics["process"]["memory_mb"]
        if memory_mb > standards.RESOURCE_LIMITS["memory_per_service"]:
            await self._alert_resource_violation("memory", memory_mb, 
                                               standards.RESOURCE_LIMITS["memory_per_service"])
        
        # Check CPU usage
        cpu_percent = metrics["process"]["cpu_percent"]
        if cpu_percent > standards.RESOURCE_LIMITS["cpu_percentage"]:
            await self._alert_resource_violation("cpu", cpu_percent, 
                                               standards.RESOURCE_LIMITS["cpu_percentage"])
    
    async def _alert_resource_violation(self, resource_type: str, 
                                      current_value: float, limit: float):
        """Alert on resource limit violations"""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": "resource_violation",
            "resource": resource_type,
            "current_value": current_value,
            "limit": limit,
            "severity": "warning"
        }
        
        # Log alert
        logging.warning(f"Resource violation: {resource_type} usage {current_value} exceeds limit {limit}")
        
        # Could send to monitoring system, notification service, etc.
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        if not self.metrics_history:
            return {}
        
        latest = self.metrics_history[-1]
        
        # Calculate averages over last 10 measurements
        recent_metrics = self.metrics_history[-10:]
        
        avg_memory = sum(m["process"]["memory_mb"] for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m["process"]["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
        
        return {
            "current": latest,
            "averages": {
                "memory_mb": round(avg_memory, 2),
                "cpu_percent": round(avg_cpu, 2)
            },
            "trend": self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """Calculate resource usage trend"""
        if len(self.metrics_history) < 5:
            return "insufficient_data"
        
        # Compare recent vs older measurements
        recent_avg = sum(m["process"]["memory_mb"] for m in self.metrics_history[-3:]) / 3
        older_avg = sum(m["process"]["memory_mb"] for m in self.metrics_history[-6:-3]) / 3
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
```

## Database Performance Optimization

### Query Performance Monitoring

#### Database Performance Tracking
```python
# services/admin-api/src/database_performance.py
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import time
from typing import Dict, Any

class DatabasePerformanceMonitor:
    def __init__(self):
        self.query_metrics = {}
        self.slow_queries = []
    
    def setup_monitoring(self, engine: Engine):
        """Setup database query monitoring"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            
            # Record query metrics
            self._record_query_metrics(statement, total, parameters)
            
            # Log slow queries
            if total > 1.0:  # Queries taking more than 1 second
                self._log_slow_query(statement, total, parameters)
    
    def _record_query_metrics(self, statement: str, execution_time: float, parameters: tuple):
        """Record query performance metrics"""
        # Normalize statement (remove parameters for grouping)
        normalized_statement = self._normalize_statement(statement)
        
        if normalized_statement not in self.query_metrics:
            self.query_metrics[normalized_statement] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "avg_time": 0
            }
        
        metrics = self.query_metrics[normalized_statement]
        metrics["count"] += 1
        metrics["total_time"] += execution_time
        metrics["min_time"] = min(metrics["min_time"], execution_time)
        metrics["max_time"] = max(metrics["max_time"], execution_time)
        metrics["avg_time"] = metrics["total_time"] / metrics["count"]
    
    def _normalize_statement(self, statement: str) -> str:
        """Normalize SQL statement for grouping"""
        # Remove parameter placeholders
        normalized = statement
        # Replace parameter placeholders with generic markers
        import re
        normalized = re.sub(r'%s', '?', normalized)
        normalized = re.sub(r':\w+', '?', normalized)
        return normalized.strip()
    
    def _log_slow_query(self, statement: str, execution_time: float, parameters: tuple):
        """Log slow queries for analysis"""
        slow_query = {
            "timestamp": datetime.utcnow().isoformat(),
            "statement": statement,
            "execution_time": execution_time,
            "parameters": parameters
        }
        
        self.slow_queries.append(slow_query)
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries.pop(0)
        
        logging.warning(f"Slow query detected: {execution_time:.3f}s - {statement[:100]}...")
    
    def get_query_performance_summary(self) -> Dict[str, Any]:
        """Get database query performance summary"""
        summary = {}
        
        for statement, metrics in self.query_metrics.items():
            summary[statement] = {
                "execution_count": metrics["count"],
                "avg_execution_time": round(metrics["avg_time"], 3),
                "min_execution_time": round(metrics["min_time"], 3),
                "max_execution_time": round(metrics["max_time"], 3),
                "total_execution_time": round(metrics["total_time"], 3)
            }
        
        return {
            "query_metrics": summary,
            "slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
            "total_queries": sum(m["count"] for m in self.query_metrics.values())
        }

# Usage in database setup
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)
db_monitor = DatabasePerformanceMonitor()
db_monitor.setup_monitoring(engine)
```

### Connection Pool Optimization

#### Database Connection Management
```python
# services/admin-api/src/connection_pool.py
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import logging

class OptimizedConnectionPool:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """Setup optimized database engine with connection pooling"""
        self.engine = create_engine(
            self.database_url,
            # Connection pool settings
            pool_size=10,                    # Number of connections to maintain
            max_overflow=20,                 # Additional connections when needed
            pool_timeout=30,                 # Seconds to wait for connection
            pool_recycle=3600,               # Recycle connections after 1 hour
            pool_pre_ping=True,              # Validate connections before use
            
            # Performance settings
            echo=False,                      # Don't log SQL statements
            echo_pool=False,                 # Don't log pool events
            
            # Connection settings
            connect_args={
                "connect_timeout": 10,       # Connection timeout
                "application_name": "ha_ingestor_admin_api"
            }
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            return False
```

## Caching Strategy

### Multi-Level Caching

#### Comprehensive Caching Implementation
```python
# services/admin-api/src/caching.py
import redis
import json
from typing import Optional, Any, Union
from datetime import timedelta
import hashlib

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # Cache configuration
        self.default_ttl = 300  # 5 minutes
        self.cache_prefix = "ha_ingestor:"
    
    def get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        key_data = ":".join(str(arg) for arg in args)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.cache_prefix}{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            logging.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logging.error(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}{pattern}")
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")
            return 0

# Caching decorators
def cache_result(ttl: int = 300, key_prefix: str = "default"):
    """Cache function result"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_manager = CacheManager()
            
            # Generate cache key
            cache_key = cache_manager.get_cache_key(
                key_prefix, 
                func.__name__, 
                str(args), 
                str(sorted(kwargs.items()))
            )
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """Invalidate cache on function execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            cache_manager = CacheManager()
            await cache_manager.invalidate_pattern(pattern)
            
            return result
        return wrapper
    return decorator

# Usage examples
@router.get("/events/stats")
@cache_result(ttl=600, key_prefix="stats")  # Cache for 10 minutes
async def get_event_stats():
    """Get event statistics - cached"""
    pass

@router.post("/events")
@cache_invalidate("events:*")  # Invalidate event-related cache
async def create_event():
    """Create event - invalidate cache"""
    pass
```

## Performance Testing

### Load Testing Framework

#### Comprehensive Performance Testing
```python
# tests/test_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from services.admin-api.src.main import app

client = TestClient(app)

class PerformanceTester:
    def __init__(self, client: TestClient):
        self.client = client
    
    def test_response_time(self, endpoint: str, max_time_ms: int = 500):
        """Test endpoint response time"""
        start_time = time.time()
        response = self.client.get(endpoint)
        response_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, f"Endpoint failed: {response.status_code}"
        assert response_time <= max_time_ms, f"Response time {response_time:.2f}ms exceeds limit {max_time_ms}ms"
    
    def test_concurrent_requests(self, endpoint: str, num_requests: int = 100, max_avg_time_ms: int = 1000):
        """Test concurrent request handling"""
        def make_request():
            start_time = time.time()
            response = self.client.get(endpoint)
            response_time = (time.time() - start_time) * 1000
            return response.status_code, response_time
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]
        
        # Analyze results
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        # Check success rate
        success_rate = (status_codes.count(200) / len(status_codes)) * 100
        assert success_rate >= 95, f"Success rate {success_rate:.1f}% is too low"
        
        # Check average response time
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time <= max_avg_time_ms, f"Average response time {avg_response_time:.2f}ms exceeds limit"
        
        # Check max response time
        max_response_time = max(response_times)
        assert max_response_time <= max_avg_time_ms * 2, f"Max response time {max_response_time:.2f}ms is too high"

def test_api_response_times():
    """Test API endpoint response times"""
    tester = PerformanceTester(client)
    
    # Test various endpoints
    tester.test_response_time("/api/v1/health", max_time_ms=100)
    tester.test_response_time("/api/v1/events", max_time_ms=500)
    tester.test_response_time("/api/v1/stats", max_time_ms=1000)

def test_concurrent_load():
    """Test concurrent request handling"""
    tester = PerformanceTester(client)
    
    # Test concurrent requests to different endpoints
    tester.test_concurrent_requests("/api/v1/health", num_requests=200, max_avg_time_ms=200)
    tester.test_concurrent_requests("/api/v1/events", num_requests=100, max_avg_time_ms=800)

def test_memory_usage():
    """Test memory usage under load"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform load testing
    tester = PerformanceTester(client)
    tester.test_concurrent_requests("/api/v1/events", num_requests=1000, max_avg_time_ms=1000)
    
    # Check memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 100MB)
    assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB is too high"

def test_database_performance():
    """Test database query performance"""
    # Test database queries with various parameters
    test_cases = [
        {"limit": 10, "offset": 0},
        {"limit": 100, "offset": 0},
        {"limit": 1000, "offset": 0},
        {"entity_id": "sensor.temperature"},
        {"start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-02T00:00:00Z"}
    ]
    
    for params in test_cases:
        start_time = time.time()
        response = client.get("/api/v1/events", params=params)
        response_time = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, f"Query failed: {params}"
        assert response_time <= 2000, f"Query too slow: {response_time:.2f}ms for {params}"
```

These performance standards ensure the Home Assistant Ingestor maintains high performance and scalability across all services and components.
