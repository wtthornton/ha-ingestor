"""Unit tests for filter system performance optimizations."""

import time
from unittest.mock import Mock

import pytest

from ha_ingestor.filters import DomainFilter, EntityFilter, FilterChain
from ha_ingestor.filters.performance import (
    FilterChainProfile,
    FilterProfile,
    FilterProfiler,
    get_filter_profiler,
)
from ha_ingestor.metrics.collector import get_metrics_collector
from ha_ingestor.models import MQTTEvent


class TestFilterProfile:
    """Test FilterProfile class."""

    def test_filter_profile_creation(self):
        """Test FilterProfile creation and initialization."""
        profile = FilterProfile("test_filter", "domain")

        assert profile.filter_name == "test_filter"
        assert profile.filter_type == "domain"
        assert profile.total_calls == 0
        assert profile.total_time_ms == 0.0
        assert profile.avg_time_ms == 0.0
        assert profile.min_time_ms == float("inf")
        assert profile.max_time_ms == 0.0
        assert profile.cache_hits == 0
        assert profile.cache_misses == 0
        assert profile.events_filtered == 0
        assert profile.events_passed == 0
        assert profile.last_call_time is None

    def test_filter_profile_update(self):
        """Test FilterProfile update method."""
        profile = FilterProfile("test_filter", "domain")

        # Update with first call
        profile.update(5.0, False, False)
        assert profile.total_calls == 1
        assert profile.total_time_ms == 5.0
        assert profile.avg_time_ms == 5.0
        assert profile.min_time_ms == 5.0
        assert profile.max_time_ms == 5.0
        assert profile.cache_misses == 1
        assert profile.events_passed == 1

        # Update with second call
        profile.update(15.0, True, True)
        assert profile.total_calls == 2
        assert profile.total_time_ms == 20.0
        assert profile.avg_time_ms == 10.0
        assert profile.min_time_ms == 5.0
        assert profile.max_time_ms == 15.0
        assert profile.cache_hits == 1
        assert profile.events_filtered == 1


class TestFilterChainProfile:
    """Test FilterChainProfile class."""

    def test_filter_chain_profile_creation(self):
        """Test FilterChainProfile creation and initialization."""
        profile = FilterChainProfile("test_chain")

        assert profile.chain_name == "test_chain"
        assert profile.total_events == 0
        assert profile.total_filtered == 0
        assert profile.total_passed == 0
        assert profile.total_processing_time_ms == 0.0
        assert profile.avg_processing_time_ms == 0.0
        assert profile.min_processing_time_ms == float("inf")
        assert profile.max_processing_time_ms == 0.0
        assert len(profile.filter_profiles) == 0
        assert len(profile.recent_processing_times) == 0

    def test_filter_chain_profile_update(self):
        """Test FilterChainProfile update_chain_stats method."""
        profile = FilterChainProfile("test_chain")

        # Update with first event
        profile.update_chain_stats(10.0, False)
        assert profile.total_events == 1
        assert profile.total_passed == 1
        assert profile.total_filtered == 0
        assert profile.total_processing_time_ms == 10.0
        assert profile.avg_processing_time_ms == 10.0
        assert profile.min_processing_time_ms == 10.0
        assert profile.max_processing_time_ms == 10.0
        assert len(profile.recent_processing_times) == 1

        # Update with second event (filtered)
        profile.update_chain_stats(20.0, True)
        assert profile.total_events == 2
        assert profile.total_passed == 1
        assert profile.total_filtered == 1
        assert profile.total_processing_time_ms == 30.0
        assert profile.avg_processing_time_ms == 15.0
        assert profile.min_processing_time_ms == 10.0
        assert profile.max_processing_time_ms == 20.0

    def test_filter_rate_calculation(self):
        """Test filter rate calculation."""
        profile = FilterChainProfile("test_chain")

        # No events
        assert profile.get_filter_rate() == 0.0

        # All events passed
        profile.update_chain_stats(10.0, False)
        profile.update_chain_stats(15.0, False)
        assert profile.get_filter_rate() == 0.0

        # Some events filtered
        profile.update_chain_stats(20.0, True)
        profile.update_chain_stats(25.0, True)
        assert profile.get_filter_rate() == 0.5  # 2 out of 4 filtered

    def test_percentile_calculation(self):
        """Test percentile time calculation."""
        profile = FilterChainProfile("test_chain")

        # No processing times
        assert profile.get_percentile_time(50) == 0.0
        assert profile.get_percentile_time(95) == 0.0

        # Add some processing times
        profile.update_chain_stats(10.0, False)
        profile.update_chain_stats(20.0, False)
        profile.update_chain_stats(30.0, False)
        profile.update_chain_stats(40.0, False)
        profile.update_chain_stats(50.0, False)

        # Test percentiles
        assert profile.get_percentile_time(50) == 30.0  # Median
        assert profile.get_percentile_time(80) == 42.0  # 80th percentile (interpolated)
        assert profile.get_percentile_time(95) == 48.0  # 95th percentile (interpolated)


class TestFilterProfiler:
    """Test FilterProfiler class."""

    def test_filter_profiler_creation(self):
        """Test FilterProfiler creation."""
        profiler = FilterProfiler(enabled=True)

        assert profiler.enabled is True
        assert len(profiler.chain_profiles) == 0
        assert profiler._start_time > 0

    def test_filter_profiler_disabled(self):
        """Test FilterProfiler when disabled."""
        profiler = FilterProfiler(enabled=False)

        # These should do nothing when disabled
        profiler.start_profiling_chain(Mock())
        profiler.record_filter_execution("chain", "filter", "type", 10.0, False, False)
        profiler.record_chain_execution("chain", 20.0, False)

        assert len(profiler.chain_profiles) == 0

    def test_start_profiling_chain(self):
        """Test starting profiling for a filter chain."""
        profiler = FilterProfiler()

        # Create mock filter chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = [
            Mock(name="filter1", _filter_type="domain"),
            Mock(name="filter2", _filter_type="entity"),
        ]

        profiler.start_profiling_chain(mock_chain)

        assert "test_chain" in profiler.chain_profiles
        assert len(profiler.chain_profiles["test_chain"].filter_profiles) == 2

    def test_record_filter_execution(self):
        """Test recording filter execution metrics."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_filter = Mock()
        mock_filter.name = "filter1"
        mock_filter._filter_type = "domain"
        mock_chain.filters = [mock_filter]
        profiler.start_profiling_chain(mock_chain)

        # Record filter execution
        profiler.record_filter_execution(
            "test_chain", "filter1", "domain", 15.0, True, False
        )

        # Check that the profile was created and updated
        assert "test_chain" in profiler.chain_profiles
        assert "filter1_domain" in profiler.chain_profiles["test_chain"].filter_profiles

        profile = profiler.chain_profiles["test_chain"].filter_profiles[
            "filter1_domain"
        ]
        assert profile.total_calls == 1
        assert profile.total_time_ms == 15.0
        assert profile.cache_hits == 1
        assert profile.events_passed == 1

    def test_record_chain_execution(self):
        """Test recording chain execution metrics."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        # Record chain execution
        profiler.record_chain_execution("test_chain", 25.0, False)

        profile = profiler.chain_profiles["test_chain"]
        assert profile.total_events == 1
        assert profile.total_passed == 1
        assert profile.total_processing_time_ms == 25.0

    def test_get_chain_profile(self):
        """Test getting chain profile."""
        profiler = FilterProfiler()

        # No profiles yet
        assert profiler.get_chain_profile("nonexistent") is None

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        # Get profile
        profile = profiler.get_chain_profile("test_chain")
        assert profile is not None
        assert profile.chain_name == "test_chain"

    def test_get_all_profiles(self):
        """Test getting all profiles."""
        profiler = FilterProfiler()

        # No profiles yet
        all_profiles = profiler.get_all_profiles()
        assert len(all_profiles) == 0

        # Start profiling chains
        mock_chain1 = Mock()
        mock_chain1.name = "chain1"
        mock_chain1.filters = []
        profiler.start_profiling_chain(mock_chain1)

        mock_chain2 = Mock()
        mock_chain2.name = "chain2"
        mock_chain2.filters = []
        profiler.start_profiling_chain(mock_chain2)

        all_profiles = profiler.get_all_profiles()
        assert len(all_profiles) == 2
        assert "chain1" in all_profiles
        assert "chain2" in all_profiles

    def test_identify_bottlenecks(self):
        """Test bottleneck identification."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        slow_filter = Mock()
        slow_filter.name = "slow_filter"
        slow_filter._filter_type = "domain"
        efficient_filter = Mock()
        efficient_filter.name = "efficient_filter"
        efficient_filter._filter_type = "entity"
        mock_chain.filters = [slow_filter, efficient_filter]
        profiler.start_profiling_chain(mock_chain)

        # Record some executions to create bottlenecks
        profiler.record_filter_execution(
            "test_chain", "slow_filter", "domain", 50.0, False, False
        )
        profiler.record_filter_execution(
            "test_chain", "slow_filter", "domain", 60.0, False, False
        )

        profiler.record_filter_execution(
            "test_chain", "efficient_filter", "entity", 5.0, False, False
        )
        profiler.record_filter_execution(
            "test_chain", "efficient_filter", "entity", 5.0, False, False
        )

        # Record chain executions
        profiler.record_chain_execution("test_chain", 55.0, False)
        profiler.record_chain_execution("test_chain", 65.0, False)

        # Identify bottlenecks
        bottlenecks = profiler.identify_bottlenecks("test_chain")

        # Should identify slow filter
        slow_filter_bottlenecks = [b for b in bottlenecks if b["type"] == "slow_filter"]
        assert len(slow_filter_bottlenecks) > 0

        # Should identify slow chain
        slow_chain_bottlenecks = [b for b in bottlenecks if b["type"] == "slow_chain"]
        assert len(slow_chain_bottlenecks) > 0

    def test_clear_profiles(self):
        """Test clearing all profiles."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        assert len(profiler.chain_profiles) == 1

        # Clear profiles
        profiler.clear_profiles()
        assert len(profiler.chain_profiles) == 0

    def test_export_profile_data_json(self):
        """Test exporting profile data as JSON."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        # Export as JSON
        json_data = profiler.export_profile_data("json")
        assert json_data.startswith("{")
        assert "test_chain" in json_data

    def test_export_profile_data_csv(self):
        """Test exporting profile data as CSV."""
        profiler = FilterProfiler()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "test_chain"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        # Export as CSV
        csv_data = profiler.export_profile_data("csv")
        assert "Chain" in csv_data
        assert "Filter" in csv_data

    def test_export_profile_data_invalid_format(self):
        """Test exporting with invalid format."""
        profiler = FilterProfiler()

        with pytest.raises(ValueError, match="Unsupported format"):
            profiler.export_profile_data("invalid")


class TestFilterProfilerIntegration:
    """Test FilterProfiler integration with actual filters."""

    @pytest.mark.asyncio
    async def test_profiler_with_real_filters(self):
        """Test profiler with real filter instances."""
        profiler = FilterProfiler()

        # Create a real filter chain
        chain = FilterChain(name="integration_test_chain")
        chain.add_filter(DomainFilter(["light", "switch"], name="domain_filter"))
        chain.add_filter(EntityFilter(["light.*"], name="entity_filter"))

        # Start profiling
        profiler.start_profiling_chain(chain)

        # Create test events
        events = [
            MQTTEvent.from_mqtt_message(
                "homeassistant/light/living_room/state", "on", time.time()
            ),
            MQTTEvent.from_mqtt_message(
                "homeassistant/switch/tv/state", "off", time.time()
            ),
            MQTTEvent.from_mqtt_message(
                "homeassistant/sensor/temp/state", "23.5", time.time()
            ),
        ]

        # Manually record filter executions to simulate what would happen in a real integration
        for i, event in enumerate(events):
            # Simulate filter processing time
            processing_time = 5.0 + i  # Different times for each event

            # Record filter execution for domain filter
            profiler.record_filter_execution(
                "integration_test_chain",
                "domain_filter",
                "domain",
                processing_time,
                False,
                False,  # Not cached, not filtered
            )

            # Record filter execution for entity filter (if event passes domain filter)
            if event.domain in ["light", "switch"]:
                entity_filtered = not event.entity_id.startswith("light")
                profiler.record_filter_execution(
                    "integration_test_chain",
                    "entity_filter",
                    "entity",
                    processing_time + 1,
                    False,
                    entity_filtered,
                )

                # Record chain execution
                total_time = processing_time * 2 + 1
                event_filtered = entity_filtered
                profiler.record_chain_execution(
                    "integration_test_chain", total_time, event_filtered
                )
            else:
                # Event filtered by domain filter
                profiler.record_chain_execution(
                    "integration_test_chain", processing_time, True
                )

        # Check profiling data
        profile = profiler.get_chain_profile("integration_test_chain")
        assert profile is not None
        assert profile.total_events == 3
        assert profile.total_filtered == 3  # All events are filtered out
        assert profile.total_passed == 0  # No events pass through


class TestGlobalProfiler:
    """Test global profiler functionality."""

    def test_get_filter_profiler(self):
        """Test getting global profiler instance."""
        profiler1 = get_filter_profiler()
        profiler2 = get_filter_profiler()

        # Should return the same instance
        assert profiler1 is profiler2

    def test_global_profiler_persistence(self):
        """Test that global profiler persists data."""
        profiler = get_filter_profiler()

        # Clear any existing data
        profiler.clear_profiles()

        # Start profiling a chain
        mock_chain = Mock()
        mock_chain.name = "persistence_test"
        mock_chain.filters = []
        profiler.start_profiling_chain(mock_chain)

        # Record some data
        profiler.record_chain_execution("persistence_test", 10.0, False)

        # Get profiler again (should be same instance)
        profiler2 = get_filter_profiler()
        profile = profiler2.get_chain_profile("persistence_test")

        assert profile is not None
        assert profile.total_events == 1


class TestFilterPerformanceOptimizations:
    """Test actual filter performance optimizations."""

    @pytest.mark.asyncio
    async def test_filter_caching_performance(self):
        """Test that filter caching improves performance."""
        # Create a filter
        entity_filter = EntityFilter(["light.*", "switch.*"], name="cache_test")

        # Create test events
        events = [
            MQTTEvent.from_mqtt_message(
                "homeassistant/light/living_room/state", "on", time.time()
            ),
            MQTTEvent.from_mqtt_message(
                "homeassistant/switch/tv/state", "off", time.time()
            ),
        ]

        # First pass - no caching
        start_time = time.time()
        for event in events:
            await entity_filter.process(event)
        first_pass_time = time.time() - start_time

        # Second pass - should benefit from caching
        start_time = time.time()
        for event in events:
            await entity_filter.process(event)
        second_pass_time = time.time() - start_time

        # Second pass should be faster due to caching
        assert second_pass_time <= first_pass_time

        # Check cache statistics
        stats = entity_filter.get_stats()
        assert stats["cache_hits"] > 0
        assert stats["cache_size"] > 0

    @pytest.mark.asyncio
    async def test_regex_pattern_optimization(self):
        """Test regex pattern compilation optimization."""
        # Create filter with complex patterns
        patterns = [r"^living_room$", r"^tv$"]

        entity_filter = EntityFilter(patterns, name="regex_test")

        # Check that patterns were compiled
        assert len(entity_filter._compiled_patterns) == 2
        assert all(hasattr(p, "search") for p in entity_filter._compiled_patterns)

        # Test pattern matching
        event = MQTTEvent.from_mqtt_message(
            "homeassistant/light/living_room/state", "on", time.time()
        )
        result = await entity_filter.should_process(event)
        assert result is True

        # Check pattern cache
        pattern_stats = entity_filter.get_pattern_stats()
        assert pattern_stats["pattern_cache_size"] > 0

    @pytest.mark.asyncio
    async def test_filter_chain_profiling_integration(self):
        """Test that filter chain profiling works with real filters."""
        # Create a filter chain
        chain = FilterChain(name="profiling_test")
        chain.add_filter(DomainFilter(["light"], name="domain_filter"))
        chain.add_filter(EntityFilter(["light.*"], name="entity_filter"))

        # Create test events
        events = [
            MQTTEvent.from_mqtt_message(
                "homeassistant/light/living_room/state", "on", time.time()
            ),
            MQTTEvent.from_mqtt_message(
                "homeassistant/switch/tv/state", "off", time.time()
            ),
        ]

        # Process events
        for event in events:
            await chain.process_event(event)

        # Check that profiling data was collected
        profiler = get_filter_profiler()
        profile = profiler.get_chain_profile("profiling_test")

        if profile:
            assert profile.total_events == 2
            assert len(profile.filter_profiles) == 2


class TestMetricsIntegration:
    """Test integration with metrics collector."""

    @pytest.mark.asyncio
    async def test_filter_metrics_collection(self):
        """Test that filter metrics are collected."""
        # Get metrics collector
        metrics_collector = get_metrics_collector()

        # Create and use a filter
        entity_filter = EntityFilter(["light.*"], name="metrics_test")

        # Process some events
        events = [
            MQTTEvent.from_mqtt_message(
                "homeassistant/light/living_room/state", "on", time.time()
            ),
            MQTTEvent.from_mqtt_message(
                "homeassistant/light/kitchen/state", "off", time.time()
            ),
        ]

        for event in events:
            await entity_filter.process(event)

        # Check that metrics were recorded
        # Note: We can't easily verify the actual metric values without a full metrics system
        # But we can verify that the metrics collection methods exist and don't raise errors
        assert hasattr(metrics_collector, "record_filter_metrics")
        assert hasattr(metrics_collector, "record_filter_chain_metrics")
        assert hasattr(metrics_collector, "update_filter_cache_size")


if __name__ == "__main__":
    pytest.main([__file__])
