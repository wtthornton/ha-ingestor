"""Tests for the retention system components."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from ha_ingestor.retention.archival_manager import (
    ArchivalLocation,
    ArchivalManager,
)
from ha_ingestor.retention.cleanup_engine import (
    CleanupEngine,
)
from ha_ingestor.retention.monitoring import (
    RetentionAlert,
    RetentionHealthCheck,
    RetentionMonitor,
)
from ha_ingestor.retention.policy_manager import RetentionPolicyManager
from ha_ingestor.retention.retention_policies import (
    ArchivalStrategy,
    CompressionLevel,
    DataType,
    RetentionPeriod,
    RetentionPolicy,
)


class TestRetentionPolicies:
    """Test retention policy data models."""

    def test_retention_period_to_timedelta(self):
        """Test retention period conversion to timedelta."""
        assert RetentionPeriod.ONE_DAY.to_timedelta() == timedelta(days=1)
        assert RetentionPeriod.ONE_WEEK.to_timedelta() == timedelta(weeks=1)
        assert RetentionPeriod.ONE_MONTH.to_timedelta() == timedelta(days=30)
        assert RetentionPeriod.ONE_YEAR.to_timedelta() == timedelta(days=365)
        assert RetentionPeriod.INDEFINITE.to_timedelta() == timedelta.max

    def test_compression_level_ratio(self):
        """Test compression level ratio calculation."""
        assert CompressionLevel.NONE.get_compression_ratio() == 1.0
        assert CompressionLevel.LOW.get_compression_ratio() == 0.8
        assert CompressionLevel.HIGH.get_compression_ratio() == 0.4
        assert CompressionLevel.MAXIMUM.get_compression_ratio() == 0.2

    def test_retention_policy_validation(self):
        """Test retention policy validation."""
        # Valid policy
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.COMPRESS,
        )
        assert policy.name == "test_policy"
        assert policy.data_type == DataType.HA_EVENTS

        # Test invalid sampling rate
        with pytest.raises(
            ValueError, match="sampling_rate must be between 0.0 and 1.0"
        ):
            RetentionPolicy(
                name="invalid_policy",
                data_type=DataType.HA_EVENTS,
                retention_period=RetentionPeriod.ONE_MONTH,
                archival_strategy=ArchivalStrategy.SAMPLE,
                sampling_rate=1.5,
            )

        # Test invalid alert threshold
        with pytest.raises(
            ValueError, match="alert_threshold must be between 0.0 and 1.0"
        ):
            RetentionPolicy(
                name="invalid_policy",
                data_type=DataType.HA_EVENTS,
                retention_period=RetentionPeriod.ONE_MONTH,
                archival_strategy=ArchivalStrategy.COMPRESS,
                alert_threshold=1.5,
            )

    def test_retention_policy_methods(self):
        """Test retention policy utility methods."""
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.COMPRESS,
        )

        assert policy.get_retention_days() == 30
        assert policy.should_archive(timedelta(days=31)) is True
        assert policy.should_archive(timedelta(days=29)) is False
        assert policy.should_alert(timedelta(days=27)) is True  # 90% of 30 days

        # Test storage savings estimation
        savings = policy.get_estimated_storage_savings(100.0)
        assert savings == 40.0  # 100 * (1 - 0.4) for HIGH compression


class TestRetentionPolicyManager:
    """Test retention policy manager."""

    @pytest.fixture
    def manager(self):
        """Create a policy manager instance."""
        return RetentionPolicyManager()

    def test_initialization(self, manager):
        """Test policy manager initialization."""
        assert len(manager.policies) > 0  # Should have default policies
        assert manager.default_retention_days == 90
        assert manager.cleanup_interval == 3600
        assert not manager.is_running

    def test_default_policies(self, manager):
        """Test default policy creation."""
        default_policies = [
            "ha_events_default",
            "system_metrics_default",
            "performance_metrics_default",
            "alert_history_default",
            "connection_logs_default",
            "error_logs_default",
        ]

        for policy_name in default_policies:
            assert policy_name in manager.policies
            policy = manager.policies[policy_name]
            assert policy.enabled is True
            assert "default" in policy.tags

    def test_add_policy(self, manager):
        """Test adding a new policy."""
        policy = RetentionPolicy(
            name="custom_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_WEEK,
            archival_strategy=ArchivalStrategy.DELETE,
        )

        assert manager.add_policy(policy) is True
        assert "custom_policy" in manager.policies
        assert manager.policies["custom_policy"].created_at is not None

    def test_update_policy(self, manager):
        """Test updating an existing policy."""
        # First add a policy
        policy = RetentionPolicy(
            name="update_test",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_WEEK,
            archival_strategy=ArchivalStrategy.DELETE,
        )
        manager.add_policy(policy)

        # Update it
        updated_policy = RetentionPolicy(
            name="update_test",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.COMPRESS,
        )

        assert manager.update_policy("update_test", updated_policy) is True
        assert (
            manager.policies["update_test"].retention_period
            == RetentionPeriod.ONE_MONTH
        )

    def test_remove_policy(self, manager):
        """Test removing a policy."""
        # Add a custom policy
        policy = RetentionPolicy(
            name="remove_test",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_WEEK,
            archival_strategy=ArchivalStrategy.DELETE,
        )
        manager.add_policy(policy)

        # Remove it
        assert manager.remove_policy("remove_test") is True
        assert "remove_test" not in manager.policies

        # Try to remove default policy
        assert manager.remove_policy("ha_events_default") is False

    def test_get_policies_by_type(self, manager):
        """Test getting policies by data type."""
        ha_event_policies = manager.get_policies_by_type(DataType.HA_EVENTS)
        assert len(ha_event_policies) > 0
        assert all(p.data_type == DataType.HA_EVENTS for p in ha_event_policies)

    def test_get_active_policies(self, manager):
        """Test getting active policies."""
        active_policies = manager.get_active_policies()
        assert len(active_policies) > 0
        assert all(p.enabled for p in active_policies)

    def test_get_retention_statistics(self, manager):
        """Test getting retention statistics."""
        stats = manager.get_retention_statistics()
        assert stats.total_policies > 0
        assert stats.active_policies > 0
        assert stats.system_status in ["healthy", "warning", "error"]

    def test_validate_policy(self, manager):
        """Test policy validation."""
        # Valid policy
        valid_policy = RetentionPolicy(
            name="valid",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.COMPRESS,
        )
        errors = manager.validate_policy(valid_policy)
        assert len(errors) == 0

        # Invalid policy
        invalid_policy = RetentionPolicy(
            name="", data_type=None, retention_period=None, archival_strategy=None
        )
        errors = manager.validate_policy(invalid_policy)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        """Test starting and stopping the manager."""
        await manager.start()
        assert manager.is_running is True
        assert manager.cleanup_task is not None

        await manager.stop()
        assert manager.is_running is False
        assert manager.cleanup_task is None


class TestCleanupEngine:
    """Test cleanup engine."""

    @pytest.fixture
    def engine(self):
        """Create a cleanup engine instance."""
        return CleanupEngine()

    def test_initialization(self, engine):
        """Test cleanup engine initialization."""
        assert engine.max_concurrent_jobs == 3
        assert engine.job_timeout == 300
        assert engine.batch_size == 1000
        assert not engine.is_running
        assert len(engine.jobs) == 0

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """Test starting and stopping the engine."""
        await engine.start()
        assert engine.is_running is True
        assert len(engine.worker_tasks) == 3

        await engine.stop()
        assert engine.is_running is False
        assert len(engine.worker_tasks) == 0

    @pytest.mark.asyncio
    async def test_submit_cleanup_job(self, engine):
        """Test submitting a cleanup job."""
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.DELETE,
        )

        job_id = await engine.submit_cleanup_job(policy)
        assert job_id in engine.jobs
        assert engine.jobs[job_id].status == "pending"

    @pytest.mark.asyncio
    async def test_get_job_status(self, engine):
        """Test getting job status."""
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.DELETE,
        )

        job_id = await engine.submit_cleanup_job(policy)
        job = await engine.get_job_status(job_id)
        assert job is not None
        assert job.id == job_id

    @pytest.mark.asyncio
    async def test_cancel_job(self, engine):
        """Test cancelling a job."""
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.DELETE,
        )

        job_id = await engine.submit_cleanup_job(policy)

        # Job is pending, can't cancel running job
        assert await engine.cancel_job(job_id) is False

        # Start the job to make it running
        job = engine.jobs[job_id]
        job.status = "running"
        engine.running_jobs[job_id] = job

        assert await engine.cancel_job(job_id) is True
        assert job.status == "cancelled"

    def test_get_statistics(self, engine):
        """Test getting engine statistics."""
        stats = engine.get_statistics()
        assert "total_jobs_processed" in stats
        assert "active_jobs" in stats
        assert "is_running" in stats
        assert stats["is_running"] is False


class TestArchivalManager:
    """Test archival manager."""

    @pytest.fixture
    def manager(self):
        """Create an archival manager instance."""
        return ArchivalManager()

    def test_initialization(self, manager):
        """Test archival manager initialization."""
        assert manager.max_concurrent_jobs == 2
        assert manager.job_timeout == 600
        assert manager.batch_size == 5000
        assert not manager.is_running
        assert len(manager.locations) > 0  # Should have default location

    def test_default_locations(self, manager):
        """Test default location creation."""
        assert "default_local" in manager.locations
        default_loc = manager.locations["default_local"]
        assert default_loc.type == "local"
        assert default_loc.compression is True
        assert default_loc.retention_days == 365 * 5

    def test_add_location(self, manager):
        """Test adding a new location."""
        location = ArchivalLocation(
            name="test_location", type="local", path="./test_archives", compression=True
        )

        assert manager.add_location(location) is True
        assert "test_location" in manager.locations

    def test_remove_location(self, manager):
        """Test removing a location."""
        # Add a custom location
        location = ArchivalLocation(
            name="remove_test", type="local", path="./test_archives", compression=True
        )
        manager.add_location(location)

        # Remove it
        assert manager.remove_location("remove_test") is True
        assert "remove_test" not in manager.locations

        # Try to remove default location
        assert manager.remove_location("default_local") is False

    @pytest.mark.asyncio
    async def test_start_stop(self, manager):
        """Test starting and stopping the manager."""
        await manager.start()
        assert manager.is_running is True
        assert len(manager.worker_tasks) == 2

        await manager.stop()
        assert manager.is_running is False
        assert len(manager.worker_tasks) == 0

    @pytest.mark.asyncio
    async def test_submit_archival_job(self, manager):
        """Test submitting an archival job."""
        policy = RetentionPolicy(
            name="test_policy",
            data_type=DataType.HA_EVENTS,
            retention_period=RetentionPeriod.ONE_MONTH,
            archival_strategy=ArchivalStrategy.ARCHIVE,
        )

        job_id = await manager.submit_archival_job(policy, "default_local")
        assert job_id in manager.jobs
        assert manager.jobs[job_id].status == "pending"

    @pytest.mark.asyncio
    async def test_list_archives(self, manager):
        """Test listing archives."""
        archives = await manager.list_archives("default_local")
        assert isinstance(archives, list)

    @pytest.mark.asyncio
    async def test_cleanup_old_archives(self, manager):
        """Test cleaning up old archives."""
        result = await manager.cleanup_old_archives("default_local")
        assert "success" in result

    def test_get_statistics(self, manager):
        """Test getting manager statistics."""
        stats = manager.get_statistics()
        assert "total_jobs_processed" in stats
        assert "locations" in stats
        assert "is_running" in stats


class TestRetentionMonitor:
    """Test retention monitor."""

    @pytest.fixture
    def monitor(self):
        """Create a retention monitor instance."""
        return RetentionMonitor()

    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor.health_check_interval == 300
        assert monitor.storage_warning_threshold == 80.0
        assert monitor.storage_critical_threshold == 95.0
        assert not monitor.is_running
        assert len(monitor.health_history) == 0

    def test_set_components(self, monitor):
        """Test setting component references."""
        mock_policy_manager = MagicMock()
        mock_cleanup_engine = MagicMock()
        mock_archival_manager = MagicMock()

        monitor.set_components(
            mock_policy_manager, mock_cleanup_engine, mock_archival_manager
        )

        assert monitor.policy_manager == mock_policy_manager
        assert monitor.cleanup_engine == mock_cleanup_engine
        assert monitor.archival_manager == mock_archival_manager

    @pytest.mark.asyncio
    async def test_start_stop(self, monitor):
        """Test starting and stopping the monitor."""
        await monitor.start()
        assert monitor.is_running is True
        assert monitor.monitoring_task is not None

        await monitor.stop()
        assert monitor.is_running is False
        assert monitor.monitoring_task is None

    @pytest.mark.asyncio
    async def test_perform_health_check(self, monitor):
        """Test performing a health check."""
        # Mock components
        mock_policy_manager = MagicMock()
        mock_cleanup_engine = MagicMock()
        mock_archival_manager = MagicMock()

        # Mock policy manager stats
        mock_stats = MagicMock()
        mock_stats.total_policies = 5
        mock_stats.active_policies = 4
        mock_stats.last_cleanup_run = "2024-01-01T00:00:00"
        mock_stats.next_scheduled_cleanup = "2024-01-01T01:00:00"
        mock_stats.system_status = "healthy"

        mock_policy_manager.get_retention_statistics.return_value = mock_stats
        mock_policy_manager.get_all_policy_summaries.return_value = []

        # Mock cleanup engine stats
        mock_cleanup_engine.get_statistics.return_value = {
            "is_running": True,
            "active_jobs": 0,
            "queued_jobs": 0,
            "total_jobs_processed": 10,
            "worker_count": 3,
        }

        # Mock archival manager stats
        mock_archival_manager.get_statistics.return_value = {
            "is_running": True,
            "active_jobs": 0,
            "queued_jobs": 0,
            "total_jobs_processed": 5,
            "locations": 1,
            "worker_count": 2,
        }

        monitor.set_components(
            mock_policy_manager, mock_cleanup_engine, mock_archival_manager
        )

        # Perform health check
        await monitor._perform_health_check()

        assert len(monitor.health_history) == 1
        health_check = monitor.health_history[0]
        assert health_check.overall_status == "healthy"
        assert health_check.policy_count == 5
        assert health_check.active_policy_count == 4

    @pytest.mark.asyncio
    async def test_acknowledge_resolve_alert(self, monitor):
        """Test acknowledging and resolving alerts."""
        # Create a test alert
        alert = RetentionAlert(
            id="test_alert",
            severity="warning",
            category="test",
            message="Test alert",
            timestamp=datetime.utcnow().isoformat(),
        )

        monitor.active_alerts["test_alert"] = alert
        monitor.alert_history.append(alert)

        # Acknowledge alert
        assert await monitor.acknowledge_alert("test_alert") is True
        assert alert.acknowledged is True

        # Resolve alert
        assert await monitor.resolve_alert("test_alert") is True
        assert "test_alert" not in monitor.active_alerts
        assert alert.resolved is True

    def test_get_health_summary(self, monitor):
        """Test getting health summary."""
        # No health checks yet
        summary = monitor.get_health_summary()
        assert summary["status"] == "unknown"

        # Add a health check
        health_check = RetentionHealthCheck(
            timestamp=datetime.utcnow().isoformat(),
            overall_status="healthy",
            policy_count=5,
            active_policy_count=4,
            policies_with_errors=0,
            cleanup_engine_status="idle",
            archival_manager_status="idle",
            storage_utilization_percent=50.0,
        )

        monitor.health_history.append(health_check)

        summary = monitor.get_health_summary()
        assert summary["overall_status"] == "healthy"
        assert summary["policy_count"] == 5

    def test_get_statistics(self, monitor):
        """Test getting monitor statistics."""
        stats = monitor.get_statistics()
        assert "total_health_checks" in stats
        assert "total_alerts_generated" in stats
        assert "active_alerts" in stats
        assert "is_running" in stats


class TestRetentionSystemIntegration:
    """Integration tests for the retention system."""

    @pytest_asyncio.fixture
    async def retention_system(self):
        """Create a complete retention system."""
        policy_manager = RetentionPolicyManager()
        cleanup_engine = CleanupEngine()
        archival_manager = ArchivalManager()
        monitor = RetentionMonitor()

        # Set up component references
        monitor.set_components(policy_manager, cleanup_engine, archival_manager)

        # Start all components
        await policy_manager.start()
        await cleanup_engine.start()
        await archival_manager.start()
        await monitor.start()

        system = {
            "policy_manager": policy_manager,
            "cleanup_engine": cleanup_engine,
            "archival_manager": archival_manager,
            "monitor": monitor,
        }

        yield system

        # Cleanup
        await monitor.stop()
        await archival_manager.stop()
        await cleanup_engine.stop()
        await policy_manager.stop()

    @pytest.mark.asyncio
    async def test_full_retention_workflow(self, retention_system):
        """Test a complete retention workflow."""
        policy_manager = retention_system["policy_manager"]
        cleanup_engine = retention_system["cleanup_engine"]
        archival_manager = retention_system["archival_manager"]
        monitor = retention_system["monitor"]

        # Wait for initial health check
        await asyncio.sleep(0.1)

        # Check system health
        health_summary = monitor.get_health_summary()
        assert health_summary["overall_status"] != "unknown"

        # Submit cleanup job
        policy = policy_manager.get_policy("ha_events_default")
        assert policy is not None

        job_id = await cleanup_engine.submit_cleanup_job(policy)
        assert job_id in cleanup_engine.jobs

        # Submit archival job
        archival_job_id = await archival_manager.submit_archival_job(
            policy, "default_local"
        )
        assert archival_job_id in archival_manager.jobs

        # Wait for jobs to process
        await asyncio.sleep(0.1)

        # Check job statuses
        cleanup_job = await cleanup_engine.get_job_status(job_id)
        archival_job = await archival_manager.get_job_status(archival_job_id)

        assert cleanup_job is not None
        assert archival_job is not None

        # Check system statistics
        policy_stats = policy_manager.get_retention_statistics()
        cleanup_stats = cleanup_engine.get_statistics()
        archival_stats = archival_manager.get_statistics()
        monitor_stats = monitor.get_statistics()

        assert policy_stats.total_policies > 0
        assert cleanup_stats["is_running"] is True
        assert archival_stats["is_running"] is True
        assert monitor_stats["is_running"] is True
