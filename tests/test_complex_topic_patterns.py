"""Tests for complex MQTT topic patterns and edge cases."""

import time
from unittest.mock import Mock

import pytest

from ha_ingestor.mqtt.topic_patterns import (
    TopicPattern,
    TopicPatternManager,
)


class TestComplexTopicPatterns:
    """Test complex and edge case topic patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_nested_wildcard_patterns(self):
        """Test deeply nested wildcard patterns."""
        # Test complex nested patterns
        patterns = [
            TopicPattern(
                "homeassistant/+/+/+/state", priority=1
            ),  # 5 levels: homeassistant + 3 wildcards + state
            TopicPattern(
                "homeassistant/+/+/+/+/attributes", priority=2
            ),  # 6 levels: homeassistant + 4 wildcards + attributes
            TopicPattern(
                "homeassistant/+/+/+/+/+/config", priority=3
            ),  # 7 levels: homeassistant + 5 wildcards + config
        ]

        for pattern in patterns:
            self.manager.add_pattern(pattern)

        # Test matching with various depths - corrected to match pattern specifications
        test_topics = [
            "homeassistant/sensor/temperature/living_room/state",  # 5 levels - should match pattern 1 (5 levels)
            "homeassistant/sensor/temperature/living_room/attributes",  # 5 levels - should NOT match pattern 2 (6 levels)
            "homeassistant/sensor/temperature/living_room/config",  # 5 levels - should NOT match pattern 3 (7 levels)
            "homeassistant/light/ceiling/living_room/attributes",  # 5 levels - should NOT match pattern 2 (6 levels)
            "homeassistant/switch/garage/door/security/config",  # 6 levels - should NOT match pattern 3 (7 levels)
        ]

        # Test specific matches
        # Pattern 1: homeassistant/+/+/+/state (5 levels)
        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/sensor/temperature/living_room/state"
        )
        assert len(matching_patterns) > 0, "Pattern 1 should match 5-level topics"
        assert matching_patterns[0].pattern == "homeassistant/+/+/+/state"

        # Pattern 2: homeassistant/+/+/+/+/attributes (6 levels)
        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/sensor/temperature/living_room/kitchen/attributes"
        )
        assert len(matching_patterns) > 0, "Pattern 2 should match 6-level topics"
        assert matching_patterns[0].pattern == "homeassistant/+/+/+/+/attributes"

        # Pattern 3: homeassistant/+/+/+/+/+/config (7 levels)
        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/switch/garage/door/security/access/config"
        )
        assert len(matching_patterns) > 0, "Pattern 3 should match 7-level topics"
        assert matching_patterns[0].pattern == "homeassistant/+/+/+/+/+/config"

        # Test that patterns don't match incorrect depths
        # 5-level topic should NOT match 6-level pattern
        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/sensor/temperature/living_room/attributes"
        )
        assert (
            len(matching_patterns) == 0
        ), "5-level topic should not match 6-level pattern"

        # 5-level topic should NOT match 7-level pattern
        matching_patterns = self.manager.find_matching_patterns(
            "homeassistant/sensor/temperature/living_room/config"
        )
        assert (
            len(matching_patterns) == 0
        ), "5-level topic should not match 7-level pattern"

    def test_mixed_wildcard_patterns(self):
        """Test patterns with mixed + and # wildcards."""
        patterns = [
            TopicPattern("homeassistant/+/sensor/#", priority=1),
            TopicPattern("homeassistant/+/+/+/state", priority=2),
            TopicPattern("homeassistant/+/+/+/+/#", priority=3),
        ]

        for pattern in patterns:
            self.manager.add_pattern(pattern)

        # Test various topic combinations
        test_cases = [
            (
                "homeassistant/domain/sensor/temperature/state",
                2,
            ),  # Matches patterns 1 and 2
            (
                "homeassistant/domain/sensor/temperature/attributes",
                1,
            ),  # Matches pattern 1 only
            (
                "homeassistant/domain/light/living_room/state",
                1,
            ),  # Matches pattern 2 only (not sensor)
            (
                "homeassistant/domain/switch/garage/door/status",
                1,
            ),  # Matches pattern 3 only (5+ levels)
        ]

        for topic, expected_matches in test_cases:
            matching_patterns = self.manager.find_matching_patterns(topic)
            assert (
                len(matching_patterns) == expected_matches
            ), f"Expected {expected_matches} matches for {topic}, got {len(matching_patterns)}"

    def test_edge_case_patterns(self):
        """Test edge cases and boundary conditions."""
        # Test empty and single-level patterns
        edge_patterns = [
            TopicPattern("", priority=1),  # Empty pattern
            TopicPattern("+", priority=2),  # Single wildcard
            TopicPattern("#", priority=3),  # Multi-level wildcard only
            TopicPattern("homeassistant", priority=4),  # No wildcards
        ]

        for pattern in edge_patterns:
            if pattern.pattern:  # Skip empty pattern validation
                self.manager.add_pattern(pattern)

        # Test edge case topics
        edge_topics = [
            "",  # Empty topic
            "single",  # Single level
            "homeassistant",  # Exact match
            "homeassistant/",  # Trailing slash
            "/homeassistant",  # Leading slash
        ]

        for topic in edge_topics:
            if topic:  # Skip empty topic
                matching_patterns = self.manager.find_matching_patterns(topic)
                # Should find at least some patterns for valid topics
                if topic == "homeassistant":
                    assert len(matching_patterns) > 0, f"No patterns match: {topic}"

    def test_special_character_patterns(self):
        """Test patterns with special characters and escaping."""
        # Test patterns that might have special regex characters
        special_patterns = [
            TopicPattern("homeassistant/sensor/temp-1/state", priority=1),
            TopicPattern("homeassistant/light/living_room_1/state", priority=2),
            TopicPattern("homeassistant/switch/garage-door/state", priority=3),
            TopicPattern("homeassistant/sensor/temp.1/state", priority=4),
        ]

        for pattern in special_patterns:
            self.manager.add_pattern(pattern)

        # Test matching with special characters
        test_topics = [
            "homeassistant/sensor/temp-1/state",
            "homeassistant/light/living_room_1/state",
            "homeassistant/switch/garage-door/state",
            "homeassistant/sensor/temp.1/state",
        ]

        for topic in test_topics:
            matching_patterns = self.manager.find_matching_patterns(topic)
            assert len(matching_patterns) > 0, f"No patterns match: {topic}"

    def test_very_long_patterns(self):
        """Test very long topic patterns."""
        # Create a very long pattern
        long_domain = "very_long_domain_name_that_exceeds_normal_length"
        long_entity = "very_long_entity_name_with_many_characters"
        long_pattern = f"homeassistant/{long_domain}/{long_entity}/state"

        pattern = TopicPattern(long_pattern, priority=1)
        self.manager.add_pattern(pattern)

        # Test matching
        matching_patterns = self.manager.find_matching_patterns(long_pattern)
        assert len(matching_patterns) == 1
        assert matching_patterns[0].pattern == long_pattern

    def test_pattern_priority_ordering(self):
        """Test complex priority ordering scenarios."""
        # Create patterns with various priorities
        patterns = [
            TopicPattern("homeassistant/+/+/state", priority=1),
            TopicPattern("homeassistant/sensor/+/state", priority=5),
            TopicPattern("homeassistant/sensor/temperature/state", priority=10),
            TopicPattern("homeassistant/+/+/+/state", priority=2),
            TopicPattern("homeassistant/+/+/+/+/state", priority=3),
        ]

        for pattern in patterns:
            self.manager.add_pattern(pattern)

        # Test that patterns are properly ordered by priority
        topic = "homeassistant/sensor/temperature/state"
        matching_patterns = self.manager.find_matching_patterns(topic)

        # Should return patterns in priority order (highest first)
        priorities = [p.priority for p in matching_patterns]
        assert priorities == sorted(
            priorities, reverse=True
        ), f"Patterns not in priority order: {priorities}"

    def test_pattern_conflicts(self):
        """Test patterns that might conflict or overlap."""
        # Create potentially conflicting patterns
        conflicting_patterns = [
            TopicPattern("homeassistant/+/+/state", priority=1),
            TopicPattern(
                "homeassistant/+/+/state", priority=2
            ),  # Same pattern, different priority
            TopicPattern(
                "homeassistant/+/+/state", priority=3
            ),  # Same pattern, different priority
        ]

        # Only the first should be added (duplicate prevention)
        for pattern in conflicting_patterns:
            result = self.manager.add_pattern(pattern)
            if pattern == conflicting_patterns[0]:
                assert result is True
            else:
                assert result is False

        # Should only have one pattern
        assert len(self.manager.patterns) == 1
        assert self.manager.patterns[0].priority == 1


class TestComplexSubscriptionScenarios:
    """Test complex subscription scenarios and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_multiple_subscriptions_same_pattern(self):
        """Test multiple subscriptions to the same pattern."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        # Subscribe multiple callbacks to the same pattern
        sub1_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback1
        )
        sub2_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback2
        )
        sub3_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback3
        )

        # All subscriptions should be created
        assert sub1_id in self.manager.subscriptions
        assert sub2_id in self.manager.subscriptions
        assert sub3_id in self.manager.subscriptions

        # Test message routing
        topic = "homeassistant/sensor/temperature/state"
        payload = "25.5"
        routes = self.manager.route_message(topic, payload)

        # Should route to all three subscriptions
        assert len(routes) == 3

        # Execute callbacks
        for subscription_id, callback in routes:
            callback(topic, payload)

        # All callbacks should be called
        assert callback1.called
        assert callback2.called
        assert callback3.called

    def test_subscription_with_complex_filters(self):
        """Test subscriptions with complex filter combinations."""
        callback = Mock()

        # Create subscription with multiple filters
        filters = {
            "topic_regex": r".*temperature.*",
            "payload_regex": r"^\d+\.?\d*$",  # Numeric values
            "min_payload_length": 3,
            "max_payload_length": 10,
            "topic_prefix": "homeassistant",
            "topic_suffix": "state",
        }

        sub_id = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/state", callback=callback, filters=filters
        )

        # Test messages that should match
        valid_messages = [
            ("homeassistant/sensor/temperature/state", "25.5"),
            ("homeassistant/sensor/temperature/state", "100.0"),
        ]

        for topic, payload in valid_messages:
            routes = self.manager.route_message(topic, payload)
            assert len(routes) == 1, f"Message should match: {topic} = {payload}"

        # Test messages that should not match
        invalid_messages = [
            (
                "homeassistant/sensor/humidity/state",
                "60.0",
            ),  # No "temperature" in topic
            ("homeassistant/sensor/temperature/state", "abc"),  # Non-numeric payload
            ("homeassistant/sensor/temperature/state", "1"),  # Too short
            ("homeassistant/sensor/temperature/state", "12345678901"),  # Too long
            ("other/sensor/temperature/state", "25.5"),  # Wrong prefix
            ("homeassistant/sensor/temperature/status", "25.5"),  # Wrong suffix
        ]

        for topic, payload in invalid_messages:
            routes = self.manager.route_message(topic, payload)
            assert len(routes) == 0, f"Message should not match: {topic} = {payload}"

    def test_subscription_cleanup(self):
        """Test proper cleanup when subscriptions are removed."""
        callback1 = Mock()
        callback2 = Mock()

        # Create two subscriptions to the SAME pattern
        sub1_id = self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state", callback1
        )
        sub2_id = self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state", callback2
        )

        # Verify subscriptions exist
        assert len(self.manager.subscriptions) == 2
        assert len(self.manager.patterns) == 1  # Same pattern, so only 1 pattern object

        # Remove first subscription
        result = self.manager.unsubscribe_from_pattern(sub1_id)
        assert result is True

        # Check that subscription is removed
        assert sub1_id not in self.manager.subscriptions
        assert len(self.manager.subscriptions) == 1

        # Check that pattern is still there (used by other subscription)
        assert (
            len(self.manager.patterns) == 1
        )  # Pattern should remain since sub2 still uses it

        # Remove second subscription
        result = self.manager.unsubscribe_from_pattern(sub2_id)
        assert result is True

        # Check that both subscription and pattern are removed
        assert sub2_id not in self.manager.subscriptions
        assert len(self.manager.subscriptions) == 0
        assert len(self.manager.patterns) == 0

    def test_subscription_performance_under_load(self):
        """Test subscription performance with many patterns and subscriptions."""
        # Create many patterns
        for i in range(100):
            pattern = TopicPattern(f"homeassistant/sensor{i}/+/state", priority=i % 10)
            self.manager.add_pattern(pattern)

        # Create many subscriptions
        callbacks = []
        for i in range(200):
            callback = Mock()
            callbacks.append(callback)
            self.manager.subscribe_to_pattern(
                f"homeassistant/sensor{i % 100}/+/state", callback
            )

        # Test performance with many messages
        start_time = time.time()

        for i in range(1000):
            topic = f"homeassistant/sensor{i % 100}/temperature/state"
            payload = f"value_{i}"
            routes = self.manager.route_message(topic, payload)

            # Execute callbacks
            for subscription_id, callback in routes:
                callback(topic, payload)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 1000 messages in reasonable time (< 5 seconds)
        assert (
            processing_time < 5.0
        ), f"Processing took too long: {processing_time:.2f}s"

        # Check metrics
        metrics = self.manager.get_metrics()
        assert metrics["total_patterns"] == 100
        assert metrics["total_subscriptions"] == 200
        assert metrics["pattern_matches"] >= 100  # At least one match per unique topic
        assert metrics["topic_routes"] >= 100  # At least one route per unique topic


class TestRealWorldMQTTScenarios:
    """Test with realistic MQTT scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_home_assistant_automation_scenario(self):
        """Test realistic Home Assistant automation scenario."""
        # Set up patterns for a typical HA setup
        patterns = [
            TopicPattern("homeassistant/+/+/state", priority=1),
            TopicPattern("homeassistant/sensor/+/state", priority=2),
            TopicPattern("homeassistant/binary_sensor/+/state", priority=2),
            TopicPattern("homeassistant/light/+/state", priority=2),
            TopicPattern("homeassistant/switch/+/state", priority=2),
            TopicPattern("homeassistant/climate/+/state", priority=2),
            TopicPattern("homeassistant/+/+/attributes", priority=1),
            TopicPattern("homeassistant/+/+/+/config", priority=3),
        ]

        for pattern in patterns:
            self.manager.add_pattern(pattern)

        # Create realistic subscriptions
        def temperature_handler(topic, payload, **kwargs):
            temp = float(payload)
            if temp > 30:
                print(f"High temperature alert: {temp}°C")
            elif temp < 10:
                print(f"Low temperature alert: {temp}°C")

        def motion_handler(topic, payload, **kwargs):
            if payload == "on":
                print(f"Motion detected: {topic}")
            else:
                print(f"Motion cleared: {topic}")

        def light_handler(topic, payload, **kwargs):
            if payload == "on":
                print(f"Light turned on: {topic}")
            else:
                print(f"Light turned off: {topic}")

        # Subscribe to patterns
        temp_sub = self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state",
            callback=temperature_handler,
            filters={"topic_regex": r".*temperature.*"},
        )

        motion_sub = self.manager.subscribe_to_pattern(
            "homeassistant/binary_sensor/+/state", callback=motion_handler
        )

        light_sub = self.manager.subscribe_to_pattern(
            "homeassistant/light/+/state", callback=light_handler
        )

        # Simulate realistic MQTT messages
        realistic_messages = [
            ("homeassistant/sensor/living_room_temperature/state", "25.5"),
            ("homeassistant/sensor/outdoor_temperature/state", "32.1"),
            ("homeassistant/binary_sensor/front_door_motion/state", "on"),
            ("homeassistant/light/living_room_ceiling/state", "on"),
            ("homeassistant/binary_sensor/front_door_motion/state", "off"),
            ("homeassistant/light/living_room_ceiling/state", "off"),
            ("homeassistant/sensor/basement_temperature/state", "8.3"),
            ("homeassistant/switch/garage_door/state", "on"),
        ]

        # Process messages
        for topic, payload in realistic_messages:
            routes = self.manager.route_message(topic, payload)

            # Execute callbacks
            for subscription_id, callback in routes:
                try:
                    callback(topic, payload)
                except Exception as e:
                    print(f"Error in callback {subscription_id}: {e}")

        # Verify processing
        metrics = self.manager.get_metrics()
        assert metrics["total_patterns"] == 8
        assert metrics["total_subscriptions"] == 3
        assert metrics["pattern_matches"] >= len(realistic_messages)

    def test_multi_tenant_scenario(self):
        """Test multi-tenant MQTT scenario."""
        # Set up patterns for multiple tenants
        tenant_patterns = [
            TopicPattern("tenant1/+/+/state", priority=1),
            TopicPattern("tenant2/+/+/state", priority=1),
            TopicPattern("tenant1/sensor/+/state", priority=2),
            TopicPattern("tenant2/sensor/+/state", priority=2),
            TopicPattern("tenant1/+/+/+/config", priority=3),
            TopicPattern("tenant2/+/+/+/config", priority=3),
        ]

        for pattern in tenant_patterns:
            self.manager.add_pattern(pattern)

        # Create tenant-specific handlers
        def tenant1_handler(topic, payload, **kwargs):
            print(f"Tenant1: {topic} = {payload}")

        def tenant2_handler(topic, payload, **kwargs):
            print(f"Tenant2: {topic} = {payload}")

        # Subscribe to tenant patterns
        t1_sub = self.manager.subscribe_to_pattern("tenant1/+/+/state", tenant1_handler)
        t2_sub = self.manager.subscribe_to_pattern("tenant2/+/+/state", tenant2_handler)

        # Test tenant isolation
        tenant1_messages = [
            ("tenant1/sensor/temperature/state", "25.5"),
            ("tenant1/light/living_room/state", "on"),
        ]

        tenant2_messages = [
            ("tenant2/sensor/temperature/state", "22.0"),
            ("tenant2/switch/garage/state", "off"),
        ]

        # Process tenant1 messages
        for topic, payload in tenant1_messages:
            routes = self.manager.route_message(topic, payload)
            assert len(routes) == 1, "Tenant1 message should only match tenant1 pattern"

        # Process tenant2 messages
        for topic, payload in tenant2_messages:
            routes = self.manager.route_message(topic, payload)
            assert len(routes) == 1, "Tenant2 message should only match tenant2 pattern"

        # Verify no cross-tenant routing
        cross_tenant_topic = "tenant1/sensor/temperature/state"
        cross_tenant_routes = self.manager.route_message(cross_tenant_topic, "25.5")

        for subscription_id, callback in cross_tenant_routes:
            assert (
                "tenant1" in self.manager.subscriptions[subscription_id].topic
            ), "Should not route tenant1 message to tenant2 handler"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
