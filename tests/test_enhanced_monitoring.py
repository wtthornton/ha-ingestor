"""Tests for the enhanced connection monitoring system."""

import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from ha_ingestor.monitoring import (
    ConnectionMonitor, ConnectionHealth, ConnectionMetrics,
    HealthTracker, ServiceHealth, ServiceStatus,
    ConnectionPool, PooledConnection, ConnectionState
)
from ha_ingestor.monitoring.connection_monitor import get_connection_monitor
from ha_ingestor.monitoring.health_tracker import get_health_tracker


class TestConnectionMonitor:
    """Test ConnectionMonitor functionality."""
    
    def test_connection_monitor_initialization(self):
        """Test connection monitor initialization."""
        monitor = ConnectionMonitor()
        
        assert monitor.name == "connection_monitor"
        assert len(monitor._connections) == 0
        assert len(monitor._health_checks) == 0
        assert monitor._running is False
    
    def test_add_connection(self):
        """Test adding a connection to monitor."""
        monitor = ConnectionMonitor()
        
        def mock_health_check():
            return True
        
        monitor.add_connection("test_service", mock_health_check)
        
        assert "test_service" in monitor._connections
        assert "test_service" in monitor._health_checks
        assert monitor._connections["test_service"].service_name == "test_service"
        assert monitor._connections["test_service"].status.value == "disconnected"
    
    def test_remove_connection(self):
        """Test removing a connection from monitoring."""
        monitor = ConnectionMonitor()
        
        def mock_health_check():
            return True
        
        monitor.add_connection("test_service", mock_health_check)
        assert "test_service" in monitor._connections
        
        monitor.remove_connection("test_service")
        assert "test_service" not in monitor._connections
        assert "test_service" not in monitor._health_checks
    
    def test_record_connection_event(self):
        """Test recording connection events."""
        monitor = ConnectionMonitor()
        
        def mock_health_check():
            return True
        
        monitor.add_connection("test_service", mock_health_check)
        
        # Record connect event
        monitor.record_connection_event("test_service", "connect")
        assert monitor._connections["test_service"].status.value == "connected"
        
        # Record disconnect event
        monitor.record_connection_event("test_service", "disconnect")
        assert monitor._connections["test_service"].status.value == "disconnected"
        
        # Record reconnect event
        monitor.record_connection_event("test_service", "reconnect")
        assert monitor._connections["test_service"].metrics.reconnect_count == 1
        
        # Record error event
        monitor.record_connection_event("test_service", "error", {"error": "Test error"})
        assert monitor._connections["test_service"].status.value == "failing"
        assert monitor._connections["test_service"].error_message == "Test error"
    
    def test_get_connection_summary(self):
        """Test getting connection summary."""
        monitor = ConnectionMonitor()
        
        def mock_health_check():
            return True
        
        monitor.add_connection("service1", mock_health_check)
        monitor.add_connection("service2", mock_health_check)
        
        # Set different statuses
        monitor.record_connection_event("service1", "connect")
        monitor.record_connection_event("service2", "error", {"error": "Test error"})
        
        summary = monitor.get_connection_summary()
        
        assert summary["overall_status"] == "failing"
        assert summary["total_connections"] == 2
        assert summary["healthy_connections"] == 1
        assert "service1" in summary["connections"]
        assert "service2" in summary["connections"]
        assert summary["connections"]["service1"]["status"] == "connected"
        assert summary["connections"]["service2"]["status"] == "failing"


class TestHealthTracker:
    """Test HealthTracker functionality."""
    
    def test_health_tracker_initialization(self):
        """Test health tracker initialization."""
        tracker = HealthTracker()
        
        assert len(tracker._services) == 0
        assert len(tracker._health_checks) == 0
        assert tracker._running is False
    
    def test_register_service(self):
        """Test registering a service."""
        tracker = HealthTracker()
        
        def mock_health_check():
            return True
        
        tracker.register_service("test_service", mock_health_check)
        
        assert "test_service" in tracker._services
        assert "test_service" in tracker._health_checks
        assert tracker._services["test_service"].service_name == "test_service"
        assert tracker._services["test_service"].status == ServiceStatus.UNKNOWN
    
    def test_set_service_status(self):
        """Test setting service status."""
        tracker = HealthTracker()
        tracker.register_service("test_service")
        
        # Set starting status
        tracker.set_service_status("test_service", ServiceStatus.STARTING)
        assert tracker._services["test_service"].status == ServiceStatus.STARTING
        assert tracker._services["test_service"].start_time is not None
        
        # Set running status
        tracker.set_service_status("test_service", ServiceStatus.RUNNING)
        assert tracker._services["test_service"].status == ServiceStatus.RUNNING
        assert tracker._services["test_service"].last_heartbeat is not None
        
        # Set error status
        tracker.set_service_status("test_service", ServiceStatus.ERROR, {"error": "Test error"})
        assert tracker._services["test_service"].status == ServiceStatus.ERROR
        assert tracker._services["test_service"].error_count == 1
    
    def test_record_heartbeat(self):
        """Test recording service heartbeat."""
        tracker = HealthTracker()
        tracker.register_service("test_service")
        
        # Set initial status
        tracker.set_service_status("test_service", ServiceStatus.RUNNING)
        initial_uptime = tracker._services["test_service"].uptime_seconds
        
        # Wait a bit and record heartbeat
        time.sleep(0.1)
        tracker.record_heartbeat("test_service")
        
        # Check that uptime was updated
        updated_uptime = tracker._services["test_service"].uptime_seconds
        assert updated_uptime > initial_uptime
    
    def test_record_error_and_warning(self):
        """Test recording service errors and warnings."""
        tracker = HealthTracker()
        tracker.register_service("test_service")
        tracker.set_service_status("test_service", ServiceStatus.RUNNING)
        
        # Record error
        tracker.record_error("test_service", "Test error", {"details": "Error details"})
        assert tracker._services["test_service"].error_count == 1
        assert tracker._services["test_service"].last_error == "Test error"
        assert tracker._services["test_service"].status == ServiceStatus.ERROR
        
        # Reset to running
        tracker.set_service_status("test_service", ServiceStatus.RUNNING)
        
        # Record warning
        tracker.record_warning("test_service", "Test warning", {"details": "Warning details"})
        assert tracker._services["test_service"].warning_count == 1
        assert tracker._services["test_service"].last_warning == "Test warning"
        assert tracker._services["test_service"].status == ServiceStatus.DEGRADED
    
    def test_get_health_summary(self):
        """Test getting health summary."""
        tracker = HealthTracker()
        
        tracker.register_service("service1")
        tracker.register_service("service2")
        
        # Set different statuses
        tracker.set_service_status("service1", ServiceStatus.RUNNING)
        tracker.set_service_status("service2", ServiceStatus.ERROR, {"error": "Test error"})
        
        summary = tracker.get_health_summary()
        
        assert summary["overall_status"] == "error"
        assert summary["total_services"] == 2
        assert summary["healthy_services"] == 1
        assert "service1" in summary["services"]
        assert "service2" in summary["services"]
        assert summary["services"]["service1"]["status"] == "running"
        assert summary["services"]["service2"]["status"] == "error"


class TestConnectionPool:
    """Test ConnectionPool functionality."""
    
    def test_connection_pool_initialization(self):
        """Test connection pool initialization."""
        pool = ConnectionPool("test_pool", max_connections=5, min_connections=2)
        
        assert pool.name == "test_pool"
        assert pool.max_connections == 5
        assert pool.min_connections == 2
        assert pool.max_idle_time == 300.0
        assert len(pool._connections) == 0
        assert pool._running is False
    
    def test_set_connection_factory(self):
        """Test setting connection factory."""
        pool = ConnectionPool("test_pool")
        
        def mock_factory():
            return "mock_connection"
        
        pool.set_connection_factory(mock_factory)
        assert pool._connection_factory == mock_factory
    
    def test_set_health_checker(self):
        """Test setting health checker."""
        pool = ConnectionPool("test_pool")
        
        def mock_checker(connection):
            return True
        
        pool.set_health_checker(mock_checker)
        assert pool._health_checker == mock_checker
    
    def test_set_connection_validator(self):
        """Test setting connection validator."""
        pool = ConnectionPool("test_pool")
        
        def mock_validator(connection):
            return True
        
        pool.set_connection_validator(mock_validator)
        assert pool._connection_validator == mock_validator
    
    def test_pool_stats(self):
        """Test getting pool statistics."""
        pool = ConnectionPool("test_pool", max_connections=10, min_connections=2)
        
        stats = pool.get_pool_stats()
        
        assert stats["name"] == "test_pool"
        assert stats["running"] is False
        assert stats["max_connections"] == 10
        assert stats["min_connections"] == 2
        assert stats["total_connections"] == 0
        assert stats["active_connections"] == 0
        assert stats["idle_connections"] == 0
        assert stats["error_connections"] == 0
        assert stats["total_created"] == 0
        assert stats["total_destroyed"] == 0
        assert stats["utilization_percent"] == 0.0


class TestPooledConnection:
    """Test PooledConnection functionality."""
    
    def test_pooled_connection_initialization(self):
        """Test pooled connection initialization."""
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        assert pooled.id == "test_1"
        assert pooled.connection == connection
        assert pooled.state == ConnectionState.IDLE
        assert pooled.use_count == 0
        assert pooled.error_count == 0
        assert pooled.last_error is None
    
    def test_pooled_connection_health_check(self):
        """Test pooled connection health check."""
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        # Should be healthy when idle
        assert pooled.is_healthy() is True
        
        # Should be healthy when active
        pooled.state = ConnectionState.ACTIVE
        assert pooled.is_healthy() is True
        
        # Should not be healthy when error
        pooled.state = ConnectionState.ERROR
        assert pooled.is_healthy() is False
    
    def test_pooled_connection_expiry_check(self):
        """Test pooled connection expiry check."""
        from datetime import timedelta
        
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now() - timedelta(seconds=400)  # 400 seconds ago
        )
        
        # Should be expired with 300 second max idle time
        assert pooled.is_expired(300.0) is True
        
        # Should not be expired with 500 second max idle time
        assert pooled.is_expired(500.0) is False
    
    def test_pooled_connection_mark_used(self):
        """Test marking connection as used."""
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        initial_use_count = pooled.use_count
        initial_last_used = pooled.last_used
        
        time.sleep(0.1)  # Small delay
        pooled.mark_used()
        
        assert pooled.use_count == initial_use_count + 1
        assert pooled.last_used > initial_last_used
        assert pooled.state == ConnectionState.ACTIVE
    
    def test_pooled_connection_mark_idle(self):
        """Test marking connection as idle."""
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.ACTIVE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        pooled.mark_idle()
        assert pooled.state == ConnectionState.IDLE
    
    def test_pooled_connection_mark_error(self):
        """Test marking connection as error."""
        connection = "mock_connection"
        pooled = PooledConnection(
            id="test_1",
            connection=connection,
            state=ConnectionState.IDLE,
            created_at=datetime.now(),
            last_used=datetime.now()
        )
        
        initial_error_count = pooled.error_count
        
        pooled.mark_error("Test error message")
        
        assert pooled.state == ConnectionState.ERROR
        assert pooled.error_count == initial_error_count + 1
        assert pooled.last_error == "Test error message"


class TestGlobalInstances:
    """Test global monitoring instances."""
    
    def test_get_connection_monitor(self):
        """Test getting global connection monitor."""
        monitor = get_connection_monitor()
        assert isinstance(monitor, ConnectionMonitor)
        
        # Should return same instance
        monitor2 = get_connection_monitor()
        assert monitor is monitor2
    
    def test_get_health_tracker(self):
        """Test getting global health tracker."""
        tracker = get_health_tracker()
        assert isinstance(tracker, HealthTracker)
        
        # Should return same instance
        tracker2 = get_health_tracker()
        assert tracker is tracker2


if __name__ == "__main__":
    pytest.main([__file__])
