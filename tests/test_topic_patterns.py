"""Tests for MQTT topic pattern matching and management system."""

import time
from unittest.mock import Mock

import pytest

from ha_ingestor.mqtt.topic_patterns import (
    TopicPattern,
    TopicPatternManager,
    TopicSubscription,
)


class TestTopicPattern:
    """Test TopicPattern class functionality."""

    def test_topic_pattern_creation(self):
        """Test creating a basic topic pattern."""
        pattern = TopicPattern(
            pattern="homeassistant/+/+/state", description="Test pattern", priority=5
        )

        assert pattern.pattern == "homeassistant/+/+/state"
        assert pattern.description == "Test pattern"
        assert pattern.priority == 5
        assert pattern.enabled is True
        assert pattern.regex_pattern is not None

    def test_topic_pattern_regex_compilation(self):
        """Test regex pattern compilation from MQTT wildcards."""
        pattern = TopicPattern(pattern="homeassistant/+/+/state")

        # Test that regex pattern is compiled correctly
        assert pattern.regex_pattern is not None

        # Test MQTT wildcard conversion
        assert pattern.matches("homeassistant/sensor/temperature/state")
        assert pattern.matches("homeassistant/light/living_room/state")
        assert not pattern.matches("homeassistant/sensor/temperature/attributes")

    def test_topic_pattern_multi_level_wildcard(self):
        """Test multi-level wildcard (#) handling."""
        pattern = TopicPattern(pattern="homeassistant/sensor/#")

        assert pattern.matches("homeassistant/sensor/temperature")
        assert pattern.matches("homeassistant/sensor/temperature/state")
        assert pattern.matches("homeassistant/sensor/temperature/attributes")
        assert not pattern.matches("homeassistant/light/living_room")

    def test_topic_pattern_priority_sorting(self):
        """Test pattern priority ordering."""
        pattern1 = TopicPattern(pattern="homeassistant/+/+/state", priority=1)
        pattern2 = TopicPattern(pattern="homeassistant/sensor/+/state", priority=5)
        pattern3 = TopicPattern(
            pattern="homeassistant/sensor/temperature/state", priority=10
        )

        patterns = [pattern1, pattern2, pattern3]
        patterns.sort(key=lambda p: p.priority, reverse=True)

        assert patterns[0].priority == 10
        assert patterns[1].priority == 5
        assert patterns[2].priority == 1

    def test_topic_pattern_extract_groups(self):
        """Test extracting named groups from topics."""
        pattern = TopicPattern(pattern="homeassistant/+/+/state")

        groups = pattern.extract_groups("homeassistant/sensor/temperature/state")
        assert groups["domain"] == "sensor"
        assert groups["entity_type"] == "temperature"
        assert groups["entity_name"] == "state"

    def test_topic_pattern_disabled(self):
        """Test disabled pattern behavior."""
        pattern = TopicPattern(pattern="homeassistant/+/+/state", enabled=False)

        assert not pattern.matches("homeassistant/sensor/temperature/state")

    def test_invalid_topic_pattern(self):
        """Test handling of invalid topic patterns."""
        with pytest.raises(ValueError, match="Invalid topic pattern"):
            TopicPattern(pattern="homeassistant/[invalid/+/state")


class TestTopicSubscription:
    """Test TopicSubscription class functionality."""

    def test_topic_subscription_creation(self):
        """Test creating a topic subscription."""
        callback = Mock()
        filters = {"topic_regex": ".*temperature.*"}

        subscription = TopicSubscription(
            topic="homeassistant/sensor/+/state",
            qos=2,
            callback=callback,
            filters=filters,
        )

        assert subscription.topic == "homeassistant/sensor/+/state"
        assert subscription.qos == 2
        assert subscription.callback == callback
        assert subscription.filters == filters
        assert subscription.message_count == 0
        assert subscription.created_at > 0

    def test_topic_subscription_defaults(self):
        """Test topic subscription with default values."""
        subscription = TopicSubscription(topic="test/topic")

        assert subscription.topic == "test/topic"
        assert subscription.qos == 1
        assert subscription.callback is None
        assert subscription.filters == {}
        assert subscription.message_count == 0


class TestTopicPatternManager:
    """Test TopicPatternManager class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_add_pattern(self):
        """Test adding a topic pattern."""
        pattern = TopicPattern(pattern="homeassistant/+/+/state")

        result = self.manager.add_pattern(pattern)

        assert result is True
        assert len(self.manager.patterns) == 1
        assert pattern in self.manager.patterns
        assert pattern.pattern in self.manager.pattern_index

    def test_add_duplicate_pattern(self):
        """Test adding a duplicate pattern."""
        pattern1 = TopicPattern(pattern="homeassistant/+/+/state")
        pattern2 = TopicPattern(pattern="homeassistant/+/+/state")

        self.manager.add_pattern(pattern1)
        result = self.manager.add_pattern(pattern2)

        assert result is False
        assert len(self.manager.patterns) == 1

    def test_remove_pattern(self):
        """Test removing a topic pattern."""
        pattern = TopicPattern(pattern="homeassistant/+/+/state")
        self.manager.add_pattern(pattern)

        result = self.manager.remove_pattern("homeassistant/+/+/state")

        assert result is True
        assert len(self.manager.patterns) == 0
        assert "homeassistant/+/+/state" not in self.manager.pattern_index

    def test_remove_nonexistent_pattern(self):
        """Test removing a pattern that doesn't exist."""
        result = self.manager.remove_pattern("nonexistent/pattern")

        assert result is False

    def test_find_matching_patterns(self):
        """Test finding patterns that match a topic."""
        pattern1 = TopicPattern(pattern="homeassistant/+/+/state", priority=1)
        pattern2 = TopicPattern(pattern="homeassistant/sensor/+/state", priority=5)
        pattern3 = TopicPattern(
            pattern="homeassistant/sensor/temperature/state", priority=10
        )

        self.manager.add_pattern(pattern1)
        self.manager.add_pattern(pattern2)
        self.manager.add_pattern(pattern3)

        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/sensor/temperature/state"
        )

        # Should return 3 patterns, sorted by priority (highest first)
        assert len(matching_patterns) == 3
        assert matching_patterns[0].priority == 10
        assert matching_patterns[1].priority == 5
        assert matching_patterns[2].priority == 1

    def test_subscribe_to_pattern(self):
        """Test subscribing to a topic pattern."""
        callback = Mock()
        filters = {"topic_regex": ".*temperature.*"}

        subscription_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback=callback, qos=2, filters=filters
        )

        assert subscription_id in self.manager.subscriptions
        subscription = self.manager.subscriptions[subscription_id]
        assert subscription.topic == "homeassistant/+/+/state"
        assert subscription.callback == callback
        assert subscription.qos == 2
        assert subscription.filters == filters

    def test_unsubscribe_from_pattern(self):
        """Test unsubscribing from a topic pattern."""
        callback = Mock()
        subscription_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback=callback
        )

        result = self.manager.unsubscribe_from_pattern(subscription_id)

        assert result is True
        assert subscription_id not in self.manager.subscriptions

    def test_unsubscribe_nonexistent_subscription(self):
        """Test unsubscribing from a subscription that doesn't exist."""
        result = self.manager.unsubscribe_from_pattern("nonexistent_sub")

        assert result is False

    def test_route_message(self):
        """Test routing messages to matching subscriptions."""
        callback1 = Mock()
        callback2 = Mock()

        # Create subscriptions with different patterns
        sub1_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback=callback1
        )
        sub2_id = self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state", callback=callback2
        )

        # Route a message that matches both patterns
        routes = self.manager.route_message(
            "homeassistant/sensor/temperature/state", "25.5"
        )

        # Should have 2 routes
        assert len(routes) == 2

        # Check that both callbacks are included
        route_ids = [route[0] for route in routes]
        assert sub1_id in route_ids
        assert sub2_id in route_ids

    def test_apply_filters(self):
        """Test applying subscription filters."""
        filters = {
            "topic_regex": ".*temperature.*",
            "min_payload_length": 3,
            "topic_prefix": "homeassistant",
        }

        # Test topic regex filter
        assert self.manager._apply_filters(
            {"topic_regex": ".*temperature.*"},
            "homeassistant/sensor/temperature/state",
            "25.5",
        )
        assert not self.manager._apply_filters(
            {"topic_regex": ".*temperature.*"},
            "homeassistant/sensor/humidity/state",
            "60.0",
        )

        # Test payload length filter
        assert self.manager._apply_filters(
            {"min_payload_length": 3}, "test/topic", "123"
        )
        assert not self.manager._apply_filters(
            {"min_payload_length": 3}, "test/topic", "12"
        )

        # Test topic prefix filter
        assert self.manager._apply_filters(
            {"topic_prefix": "homeassistant"},
            "homeassistant/sensor/temperature/state",
            "25.5",
        )
        assert not self.manager._apply_filters(
            {"topic_prefix": "homeassistant"}, "other/sensor/temperature/state", "25.5"
        )

    def test_get_optimized_subscriptions(self):
        """Test subscription optimization."""
        # Add patterns with different specificity
        self.manager.add_pattern(TopicPattern(pattern="homeassistant/+/+/state"))
        self.manager.add_pattern(TopicPattern(pattern="homeassistant/sensor/+/state"))
        self.manager.add_pattern(
            TopicPattern(pattern="homeassistant/sensor/temperature/state")
        )

        topics = [
            "homeassistant/sensor/temperature/state",
            "homeassistant/sensor/humidity/state",
            "homeassistant/light/living_room/state",
        ]

        optimized = self.manager.get_optimized_subscriptions(topics)

        # Should return the most specific patterns that cover all topics
        assert "homeassistant/sensor/temperature/state" in optimized
        assert "homeassistant/sensor/humidity/state" in optimized
        assert "homeassistant/light/living_room/state" in optimized

    def test_get_metrics(self):
        """Test getting performance metrics."""
        # Add some patterns and subscriptions
        pattern = TopicPattern(pattern="homeassistant/+/+/state")
        self.manager.add_pattern(pattern)

        callback = Mock()
        self.manager.subscribe_to_pattern("homeassistant/+/+/state", callback=callback)

        # Route a message to update metrics
        self.manager.route_message("homeassistant/sensor/temperature/state", "25.5")

        metrics = self.manager.get_metrics()

        assert metrics["total_patterns"] == 1
        assert metrics["total_subscriptions"] == 1
        assert metrics["pattern_matches"] >= 1
        assert metrics["topic_routes"] >= 1

    def test_clear_metrics(self):
        """Test clearing performance metrics."""
        # Add a pattern and route a message
        pattern = TopicPattern(pattern="homeassistant/+/+/state")
        self.manager.add_pattern(pattern)
        self.manager.route_message("homeassistant/sensor/temperature/state", "25.5")

        # Clear metrics
        self.manager.clear_metrics()

        metrics = self.manager.get_metrics()
        assert metrics["pattern_matches"] == 0
        assert metrics["topic_routes"] == 0

    def test_hierarchy_cache_management(self):
        """Test topic hierarchy cache management."""
        pattern = TopicPattern(pattern="homeassistant/sensor/+/state")
        self.manager.add_pattern(pattern)

        # Check that hierarchy is updated
        assert "homeassistant" in self.manager.topic_hierarchy
        assert "homeassistant/sensor" in self.manager.topic_hierarchy
        assert "homeassistant/sensor/+" in self.manager.topic_hierarchy

        # Remove pattern and check hierarchy cleanup
        self.manager.remove_pattern("homeassistant/sensor/+/state")
        assert "homeassistant/sensor/+" not in self.manager.topic_hierarchy


class TestTopicPatternManagerIntegration:
    """Integration tests for TopicPatternManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_complex_pattern_scenario(self):
        """Test a complex real-world pattern scenario."""
        # Add various Home Assistant patterns
        patterns = [
            TopicPattern("homeassistant/+/+/state", priority=1),
            TopicPattern("homeassistant/sensor/+/state", priority=2),
            TopicPattern("homeassistant/sensor/temperature/state", priority=3),
            TopicPattern("homeassistant/light/+/state", priority=2),
            TopicPattern("homeassistant/switch/+/state", priority=2),
            TopicPattern("homeassistant/climate/+/state", priority=2),
        ]

        for pattern in patterns:
            self.manager.add_pattern(pattern)

        # Create subscriptions with different priorities
        temp_callback = Mock()
        sensor_callback = Mock()
        general_callback = Mock()

        self.manager.subscribe_to_pattern(
            "homeassistant/sensor/temperature/state", temp_callback
        )
        self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state", sensor_callback
        )
        self.manager.subscribe_to_pattern("homeassistant/+/+/state", general_callback)

        # Test message routing for temperature sensor
        routes = self.manager.route_message(
            "homeassistant/sensor/temperature/state", "25.5"
        )

        # Should route to all three subscriptions
        assert len(routes) == 3

        # Check that callbacks are called in priority order
        route_callbacks = [route[1] for route in routes]
        assert temp_callback in route_callbacks
        assert sensor_callback in route_callbacks
        assert general_callback in route_callbacks

    def test_performance_under_load(self):
        """Test performance with many patterns and subscriptions."""
        # Add many patterns
        for i in range(50):
            pattern = TopicPattern(f"homeassistant/sensor{i}/+/state", priority=i % 5)
            self.manager.add_pattern(pattern)

        # Create many subscriptions
        callbacks = []
        for i in range(100):
            callback = Mock()
            callbacks.append(callback)
            self.manager.subscribe_to_pattern(
                f"homeassistant/sensor{i % 50}/+/state", callback
            )

        # Route many messages
        start_time = time.time()
        for i in range(1000):
            topic = f"homeassistant/sensor{i % 50}/temperature/state"
            self.manager.route_message(topic, f"value_{i}")

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 1000 messages in reasonable time (< 1 second)
        assert processing_time < 1.0

        # Check metrics
        metrics = self.manager.get_metrics()
        assert metrics["total_patterns"] == 50
        assert metrics["total_subscriptions"] == 100
        assert metrics["pattern_matches"] >= 1000
        assert metrics["topic_routes"] >= 1000

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test invalid pattern
        with pytest.raises(ValueError):
            TopicPattern("homeassistant/[invalid/+/state")

        # Test pattern with invalid regex
        with pytest.raises(ValueError):
            TopicPattern("homeassistant/+/+/state[")

        # Test adding empty pattern
        empty_pattern = TopicPattern("")
        assert not self.manager.add_pattern(empty_pattern)

        # Test routing with invalid data
        routes = self.manager.route_message("", "")
        assert routes == []

        # Test filter application with invalid data
        assert not self.manager._apply_filters(
            {"invalid_filter": "value"}, "test/topic", "test/payload"
        )
