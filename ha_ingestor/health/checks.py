"""Health check implementations for dependencies."""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..utils.logging import get_logger


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class DependencyHealth:
    """Health status for a dependency."""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    last_check: Optional[float] = None
    response_time_ms: Optional[float] = None


class HealthChecker:
    """Health checker for service dependencies."""
    
    def __init__(self):
        """Initialize health checker."""
        self.logger = get_logger(__name__)
        self._dependencies: Dict[str, callable] = {}
        self._last_checks: Dict[str, DependencyHealth] = {}
        self._check_interval = 30.0  # seconds
        
    def add_dependency(self, name: str, check_func: callable) -> None:
        """Add a dependency health check.
        
        Args:
            name: Dependency name
            check_func: Async function that returns HealthStatus
        """
        self._dependencies[name] = check_func
        self.logger.debug("Added dependency health check", dependency=name)
    
    async def check_dependency(self, name: str) -> DependencyHealth:
        """Check health of a specific dependency.
        
        Args:
            name: Dependency name to check
            
        Returns:
            DependencyHealth object
        """
        if name not in self._dependencies:
            return DependencyHealth(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Unknown dependency: {name}"
            )
        
        start_time = time.time()
        
        try:
            check_func = self._dependencies[name]
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthStatus):
                status = result
                message = f"{name} is {status.value}"
                details = {"response_time_ms": response_time}
            elif isinstance(result, dict):
                status = result.get("status", HealthStatus.UNKNOWN)
                message = result.get("message", f"{name} health check completed")
                details = result.get("details", {})
                details["response_time_ms"] = response_time
            else:
                status = HealthStatus.UNKNOWN
                message = f"Unexpected health check result for {name}"
                details = {"response_time_ms": response_time}
            
            health = DependencyHealth(
                name=name,
                status=status,
                message=message,
                details=details,
                last_check=time.time(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error("Health check failed", dependency=name, error=str(e))
            
            health = DependencyHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "response_time_ms": response_time},
                last_check=time.time(),
                response_time_ms=response_time
            )
        
        self._last_checks[name] = health
        return health
    
    async def check_all_dependencies(self) -> Dict[str, DependencyHealth]:
        """Check health of all dependencies.
        
        Returns:
            Dictionary mapping dependency names to health status
        """
        self.logger.debug("Checking all dependencies", count=len(self._dependencies))
        
        tasks = []
        for name in self._dependencies:
            tasks.append(self.check_dependency(name))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for i, (name, result) in enumerate(zip(self._dependencies.keys(), results)):
            if isinstance(result, Exception):
                health_status[name] = DependencyHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check exception: {str(result)}",
                    details={"error": str(result)},
                    last_check=time.time()
                )
            else:
                health_status[name] = result
        
        return health_status
    
    def get_last_check(self, name: str) -> Optional[DependencyHealth]:
        """Get the last health check result for a dependency.
        
        Args:
            name: Dependency name
            
        Returns:
            Last DependencyHealth object or None
        """
        return self._last_checks.get(name)
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall health status based on all dependencies.
        
        Returns:
            Overall HealthStatus
        """
        if not self._last_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in self._last_checks.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_dependency_names(self) -> List[str]:
        """Get list of registered dependency names.
        
        Returns:
            List of dependency names
        """
        return list(self._dependencies.keys())


# Default health check functions
async def check_mqtt_health() -> Dict[str, Any]:
    """Default MQTT health check."""
    try:
        # This would be implemented to check actual MQTT connection
        # For now, return a mock healthy status
        return {
            "status": HealthStatus.HEALTHY,
            "message": "MQTT connection is healthy",
            "details": {"connected": True}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"MQTT health check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def check_websocket_health() -> Dict[str, Any]:
    """Default WebSocket health check."""
    try:
        # This would be implemented to check actual WebSocket connection
        # For now, return a mock healthy status
        return {
            "status": HealthStatus.HEALTHY,
            "message": "WebSocket connection is healthy",
            "details": {"connected": True}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"WebSocket health check failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def check_influxdb_health() -> Dict[str, Any]:
    """Default InfluxDB health check."""
    try:
        # This would be implemented to check actual InfluxDB connection
        # For now, return a mock healthy status
        return {
            "status": HealthStatus.HEALTHY,
            "message": "InfluxDB connection is healthy",
            "details": {"connected": True}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"InfluxDB health check failed: {str(e)}",
            "details": {"error": str(e)}
        }


def create_default_health_checker() -> HealthChecker:
    """Create a health checker with default dependencies.
    
    Returns:
        Configured HealthChecker instance
    """
    checker = HealthChecker()
    
    # Add default health checks
    checker.add_dependency("mqtt", check_mqtt_health)
    checker.add_dependency("websocket", check_websocket_health)
    checker.add_dependency("influxdb", check_influxdb_health)
    
    return checker
