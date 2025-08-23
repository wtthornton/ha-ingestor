"""Tests for enhanced MQTT client with topic pattern support."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ha_ingestor.mqtt.client import MQTTClient
from ha_ingestor.mqtt.topic_patterns import TopicPattern


class TestEnhancedMQTTClient:
    """Test enhanced MQTT client functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock()
        config.ha_mqtt_host = "localhost"
        config.ha_mqtt_port = 1883
        config.ha_mqtt_client_id = "test-client"
        config.ha_mqtt_username = None
        config.ha_mqtt_password = None
        config.ha_mqtt_keepalive = 60
        config.mqtt_enable_pattern_matching = True
        config.mqtt_max_patterns = 100
        config.mqtt_pattern_cache_size = 1000
        config.mqtt_enable_dynamic_subscriptions = True
        config.mqtt_subscription_timeout = 300
        config.mqtt_enable_topic_optimization = True
        config.mqtt_topic_optimization_interval = 60
        config.mqtt_max_reconnect_attempts = 10
        config.mqtt_initial_reconnect_delay = 1.0
        config.mqtt_max_reconnect_delay = 300.0
        config.mqtt_reconnect_backoff_multiplier = 2.0
        config.mqtt_reconnect_jitter = 0.1
        return config

    @pytest.fixture
    def mqtt_client(self, mock_config):
        """Create an MQTT client instance for testing."""
        return MQTTClient(config=mock_config)

    def test_enhanced_mqtt_client_initialization(self, mqtt_client):
        """Test enhanced MQTT client initialization."""
        assert mqtt_client._topic_pattern_manager is not None
        assert mqtt_client._dynamic_subscriptions == {}
        assert mqtt_client._subscription_callbacks == {}
        assert mqtt_client._metrics is not None
        assert "messages_received" in mqtt_client._metrics
        assert "pattern_matches" in mqtt_client._metrics

    @pytest.mark.asyncio
    async def test_subscribe_with_pattern(self, mqtt_client):
        """Test subscribing to a topic pattern."""
        callback = Mock()
        filters = {"topic_regex": ".*temperature.*"}

        # Mock the subscribe method to avoid actual MQTT operations
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(
            mqtt_client, "subscribe", new_callable=AsyncMock
        ) as mock_subscribe:
            subscription_id = await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=callback, qos=2, filters=filters
            )

        # Check that subscription was created
        assert subscription_id in mqtt_client._subscription_callbacks
        assert mqtt_client._subscription_callbacks[subscription_id] == callback

        # Check that pattern was added to manager
        patterns = mqtt_client.get_topic_patterns()
        assert len(patterns) == 1
        assert patterns[0].pattern == "homeassistant/+/+/state"
        assert patterns[0].filters == filters

        # Check metrics
        assert mqtt_client._metrics["subscription_creates"] == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_from_pattern(self, mqtt_client):
        """Test unsubscribing from a topic pattern."""
        callback = Mock()

        # Create a subscription first
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            subscription_id = await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=callback
            )

        # Now unsubscribe
        result = await mqtt_client.unsubscribe_from_pattern(subscription_id)

        assert result is True
        assert subscription_id not in mqtt_client._subscription_callbacks

        # Check metrics
        assert mqtt_client._metrics["subscription_removes"] == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_pattern(self, mqtt_client):
        """Test unsubscribing from a non-existent pattern."""
        result = await mqtt_client.unsubscribe_from_pattern("nonexistent_sub")

        assert result is False

    def test_add_topic_pattern(self, mqtt_client):
        """Test adding a custom topic pattern."""
        pattern = TopicPattern(
            pattern="custom/sensor/+/state",
            description="Custom sensor pattern",
            priority=10,
        )

        result = mqtt_client.add_topic_pattern(pattern)

        assert result is True
        patterns = mqtt_client.get_topic_patterns()
        assert len(patterns) == 1
        assert patterns[0].pattern == "custom/sensor/+/state"
        assert patterns[0].priority == 10

    def test_remove_topic_pattern(self, mqtt_client):
        """Test removing a topic pattern."""
        pattern = TopicPattern(pattern="custom/sensor/+/state")
        mqtt_client.add_topic_pattern(pattern)

        result = mqtt_client.remove_topic_pattern("custom/sensor/+/state")

        assert result is True
        patterns = mqtt_client.get_topic_patterns()
        assert len(patterns) == 0

    def test_get_optimized_subscriptions(self, mqtt_client):
        """Test getting optimized subscriptions."""
        # Add some patterns
        mqtt_client.add_topic_pattern(TopicPattern("homeassistant/+/+/state"))
        mqtt_client.add_topic_pattern(TopicPattern("homeassistant/sensor/+/state"))

        topics = [
            "homeassistant/sensor/temperature/state",
            "homeassistant/sensor/humidity/state",
        ]

        optimized = mqtt_client.get_optimized_subscriptions(topics)

        # Should return optimized patterns
        assert len(optimized) > 0
        assert all(isinstance(pattern, str) for pattern in optimized)

    @pytest.mark.asyncio
    async def test_handle_message_with_patterns(self, mqtt_client):
        """Test handling messages with pattern matching."""
        callback1 = Mock()
        callback2 = Mock()

        # Create subscriptions with different patterns
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            sub1_id = await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=callback1
            )
            sub2_id = await mqtt_client.subscribe_with_pattern(
                "homeassistant/sensor/+/state", callback=callback2
            )

        # Handle a message that matches both patterns
        topic = "homeassistant/sensor/temperature/state"
        payload = "25.5"
        timestamp = datetime.now()

        await mqtt_client._handle_message(topic, payload, timestamp)

        # Check that both callbacks were called
        assert callback1.called
        assert callback2.called

        # Check metrics
        assert mqtt_client._metrics["messages_received"] == 1
        assert mqtt_client._metrics["messages_processed"] == 1
        assert mqtt_client._metrics["pattern_matches"] >= 2

    @pytest.mark.asyncio
    async def test_handle_message_with_filters(self, mqtt_client):
        """Test handling messages with subscription filters."""
        callback = Mock()
        filters = {"topic_regex": ".*temperature.*"}

        # Create subscription with filters
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=callback, filters=filters
            )

        # Handle a message that should match the filter
        topic = "homeassistant/sensor/temperature/state"
        payload = "25.5"
        timestamp = datetime.now()

        await mqtt_client._handle_message(topic, payload, timestamp)

        # Callback should be called
        assert callback.called

        # Handle a message that should not match the filter
        callback.reset_mock()
        topic = "homeassistant/sensor/humidity/state"
        payload = "60.0"

        await mqtt_client._handle_message(topic, payload, timestamp)

        # Callback should not be called
        assert not callback.called

    @pytest.mark.asyncio
    async def test_handle_message_with_main_handler(self, mqtt_client):
        """Test handling messages with main message handler."""
        main_handler = Mock()
        mqtt_client.set_message_handler(main_handler)

        # Create a pattern subscription
        callback = Mock()
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=callback
            )

        # Handle a message
        topic = "homeassistant/sensor/temperature/state"
        payload = "25.5"
        timestamp = datetime.now()

        await mqtt_client._handle_message(topic, payload, timestamp)

        # Both callbacks should be called
        assert callback.called
        assert main_handler.called

    def test_get_metrics(self, mqtt_client):
        """Test getting performance metrics."""
        metrics = mqtt_client.get_metrics()

        # Check that all expected metrics are present
        expected_metrics = [
            "messages_received",
            "messages_processed",
            "pattern_matches",
            "subscription_creates",
            "subscription_removes",
            "total_patterns",
            "total_subscriptions",
            "subscribed_topics",
            "dynamic_subscriptions",
            "pattern_subscriptions",
        ]

        for metric in expected_metrics:
            assert metric in metrics

    def test_clear_metrics(self, mqtt_client):
        """Test clearing performance metrics."""
        # Set some metrics
        mqtt_client._metrics["messages_received"] = 10
        mqtt_client._metrics["pattern_matches"] = 5

        # Clear metrics
        mqtt_client.clear_metrics()

        # Check that metrics are cleared
        assert mqtt_client._metrics["messages_received"] == 0
        assert mqtt_client._metrics["pattern_matches"] == 0

    @pytest.mark.asyncio
    async def test_pattern_subscription_error_handling(self, mqtt_client):
        """Test error handling in pattern subscriptions."""
        # Test with invalid pattern
        with pytest.raises(ValueError):
            await mqtt_client.subscribe_with_pattern("invalid[pattern")

        # Test with invalid callback
        with pytest.raises(Exception):
            await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback="not_a_callable"
            )

    @pytest.mark.asyncio
    async def test_message_handling_error_recovery(self, mqtt_client):
        """Test error recovery in message handling."""

        # Create a subscription with a callback that raises an exception
        def error_callback(topic, payload, timestamp):
            raise Exception("Test error")

        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            await mqtt_client.subscribe_with_pattern(
                "homeassistant/+/+/state", callback=error_callback
            )

        # Handle a message - should not crash
        topic = "homeassistant/sensor/temperature/state"
        payload = "25.5"
        timestamp = datetime.now()

        # Should handle the error gracefully
        await mqtt_client._handle_message(topic, payload, timestamp)

        # Message should still be processed
        assert mqtt_client._metrics["messages_received"] == 1
        assert mqtt_client._metrics["messages_processed"] == 1


class TestEnhancedMQTTClientIntegration:
    """Integration tests for enhanced MQTT client."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock()
        config.ha_mqtt_host = "localhost"
        config.ha_mqtt_port = 1883
        config.ha_mqtt_client_id = "test-client"
        config.ha_mqtt_username = None
        config.ha_mqtt_password = None
        config.ha_mqtt_keepalive = 60
        config.mqtt_enable_pattern_matching = True
        config.mqtt_max_patterns = 100
        config.mqtt_pattern_cache_size = 1000
        config.mqtt_enable_dynamic_subscriptions = True
        config.mqtt_subscription_timeout = 300
        config.mqtt_enable_topic_optimization = True
        config.mqtt_topic_optimization_interval = 60
        config.mqtt_max_reconnect_attempts = 10
        config.mqtt_initial_reconnect_delay = 1.0
        config.mqtt_max_reconnect_delay = 300.0
        config.mqtt_reconnect_backoff_multiplier = 2.0
        config.mqtt_reconnect_jitter = 0.1
        return config

    @pytest.fixture
    def mqtt_client(self, mock_config):
        """Create an MQTT client instance for testing."""
        return MQTTClient(config=mock_config)

    @pytest.mark.asyncio
    async def test_complex_pattern_scenario(self, mqtt_client):
        """Test a complex real-world pattern scenario."""
        callbacks = {}
        message_counts = {}

        # Create multiple subscriptions with different patterns
        patterns = [
            ("homeassistant/+/+/state", "general"),
            ("homeassistant/sensor/+/state", "sensor"),
            ("homeassistant/sensor/temperature/state", "temp_sensor"),
            ("homeassistant/light/+/state", "light"),
            ("homeassistant/switch/+/state", "switch"),
        ]

        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            for pattern, name in patterns:
                callback = Mock()
                callbacks[name] = callback
                message_counts[name] = 0

                await mqtt_client.subscribe_with_pattern(pattern, callback=callback)

        # Send various messages
        test_messages = [
            ("homeassistant/sensor/temperature/state", "25.5"),
            ("homeassistant/sensor/humidity/state", "60.0"),
            ("homeassistant/light/living_room/state", "on"),
            ("homeassistant/switch/garage/state", "off"),
            ("homeassistant/climate/thermostat/state", "heat"),
        ]

        for topic, payload in test_messages:
            timestamp = datetime.now()
            await mqtt_client._handle_message(topic, payload, timestamp)

            # Update expected message counts
            if "sensor" in topic:
                message_counts["sensor"] += 1
                if "temperature" in topic:
                    message_counts["temp_sensor"] += 1
            elif "light" in topic:
                message_counts["light"] += 1
            elif "switch" in topic:
                message_counts["switch"] += 1

            message_counts["general"] += 1

        # Verify callback calls
        for name, callback in callbacks.items():
            expected_count = message_counts[name]
            assert (
                callback.call_count == expected_count
            ), f"Callback {name} called {callback.call_count} times, expected {expected_count}"

    @pytest.mark.asyncio
    async def test_performance_under_load(self, mqtt_client):
        """Test performance with many patterns and messages."""
        # Create many patterns and subscriptions
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        callbacks = []
        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            for i in range(50):
                callback = Mock()
                callbacks.append(callback)

                pattern = f"homeassistant/sensor{i}/+/state"
                await mqtt_client.subscribe_with_pattern(pattern, callback=callback)

        # Send many messages
        start_time = asyncio.get_event_loop().time()

        for i in range(1000):
            topic = f"homeassistant/sensor{i % 50}/temperature/state"
            payload = f"value_{i}"
            timestamp = datetime.now()

            await mqtt_client._handle_message(topic, payload, timestamp)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        # Should process 1000 messages in reasonable time (< 2 seconds)
        assert processing_time < 2.0

        # Check metrics
        metrics = mqtt_client.get_metrics()
        assert metrics["total_patterns"] == 50
        assert metrics["total_subscriptions"] == 50
        assert metrics["messages_received"] == 1000
        assert metrics["messages_processed"] == 1000
        assert metrics["pattern_matches"] >= 1000

    @pytest.mark.asyncio
    async def test_dynamic_subscription_management(self, mqtt_client):
        """Test dynamic subscription creation and removal."""
        mqtt_client._connected = True
        mqtt_client._subscribed_topics = []

        # Create subscriptions dynamically
        subscription_ids = []
        with patch.object(mqtt_client, "subscribe", new_callable=AsyncMock):
            for i in range(10):
                callback = Mock()
                sub_id = await mqtt_client.subscribe_with_pattern(
                    f"test/topic{i}/+/state", callback=callback
                )
                subscription_ids.append(sub_id)

        # Verify all subscriptions were created
        assert len(mqtt_client._subscription_callbacks) == 10
        assert len(mqtt_client.get_topic_patterns()) == 10

        # Remove some subscriptions
        for i in range(5):
            await mqtt_client.unsubscribe_from_pattern(subscription_ids[i])

        # Verify subscriptions were removed
        assert len(mqtt_client._subscription_callbacks) == 5
        assert len(mqtt_client.get_topic_patterns()) == 5

        # Check metrics
        metrics = mqtt_client.get_metrics()
        assert metrics["subscription_creates"] == 10
        assert metrics["subscription_removes"] == 5
