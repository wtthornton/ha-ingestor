"""Tests for MQTT client implementation."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ha_ingestor.mqtt.client import MQTTClient
from ha_ingestor.config import get_settings


class TestMQTTClient:
    """Test cases for MQTTClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        config = Mock()
        config.ha_mqtt_host = "localhost"
        config.ha_mqtt_port = 1883
        config.ha_mqtt_client_id = "test-client"
        config.ha_mqtt_keepalive = 60
        config.is_mqtt_authenticated.return_value = False
        config.get_mqtt_auth_dict.return_value = None
        return config

    @pytest.fixture
    def mqtt_client(self, mock_config):
        """Create MQTTClient instance for testing."""
        return MQTTClient(config=mock_config)

    @pytest.fixture
    def mock_mqtt_client(self):
        """Create mock MQTT client."""
        mock_client = Mock()
        mock_client.subscribe.return_value = (0, 1)  # MQTT_ERR_SUCCESS
        mock_client.unsubscribe.return_value = (0, 1)
        mock_client.loop_start.return_value = None
        mock_client.loop_stop.return_value = None
        mock_client.disconnect.return_value = None
        return mock_client

    def test_init(self, mock_config):
        """Test MQTTClient initialization."""
        client = MQTTClient(config=mock_config)
        
        assert client.config == mock_config
        assert client.client is None
        assert not client._connected
        assert not client._connecting
        assert not client._disconnecting
        assert client._reconnect_attempts == 0
        assert client._subscribed_topics == []
        assert client._message_handler is None

    def test_init_without_config(self):
        """Test MQTTClient initialization without config."""
        with patch('ha_ingestor.mqtt.client.get_settings') as mock_get_settings:
            mock_config = Mock()
            mock_get_settings.return_value = mock_config
            
            client = MQTTClient()
            assert client.config == mock_config

    @pytest.mark.asyncio
    async def test_connect_success(self, mqtt_client, mock_mqtt_client):
        """Test successful connection to MQTT broker."""
        with patch('ha_ingestor.mqtt.client.mqtt.Client') as mock_mqtt_class:
            mock_mqtt_class.return_value = mock_mqtt_client
            
            # Mock the connection callback
            def mock_on_connect(client, userdata, flags, reason_code, properties=None):
                mqtt_client._connected = True
            
            mock_mqtt_client.on_connect = mock_on_connect
            
            # Mock event loop time
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.time.return_value = 0
                
                result = await mqtt_client.connect()
                
                assert result is True
                assert mqtt_client._connected
                assert mqtt_client.client == mock_mqtt_client
                mock_mqtt_client.connect.assert_called_once_with(
                    "localhost", 1883, keepalive=60
                )
                mock_mqtt_client.loop_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, mqtt_client):
        """Test connection when already connected."""
        mqtt_client._connected = True
        
        result = await mqtt_client.connect()
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_timeout(self, mqtt_client, mock_mqtt_client):
        """Test connection timeout."""
        with patch('ha_ingestor.mqtt.client.mqtt.Client') as mock_mqtt_class:
            mock_mqtt_class.return_value = mock_mqtt_client
            
            # Mock event loop time to simulate timeout
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.time.side_effect = [0, 11]  # Timeout after 11 seconds
                
                result = await mqtt_client.connect()
                
                assert result is False
                assert not mqtt_client._connected

    @pytest.mark.asyncio
    async def test_connect_with_authentication(self, mock_config, mock_mqtt_client):
        """Test connection with MQTT authentication."""
        mock_config.is_mqtt_authenticated.return_value = True
        mock_config.get_mqtt_auth_dict.return_value = {
            "username": "testuser",
            "password": "testpass"
        }
        
        client = MQTTClient(config=mock_config)
        
        with patch('ha_ingestor.mqtt.client.mqtt.Client') as mock_mqtt_class:
            mock_mqtt_class.return_value = mock_mqtt_client
            
            # Mock the connection callback
            def mock_on_connect(client, userdata, flags, reason_code, properties=None):
                client._connected = True
            
            mock_mqtt_client.on_connect = mock_on_connect
            
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.time.return_value = 0
                
                await client.connect()
                
                mock_mqtt_client.username_pw_set.assert_called_once_with(
                    "testuser", "testpass"
                )

    @pytest.mark.asyncio
    async def test_disconnect(self, mqtt_client, mock_mqtt_client):
        """Test disconnection from MQTT broker."""
        mqtt_client._connected = True
        mqtt_client.client = mock_mqtt_client
        mqtt_client._subscribed_topics = ["test/topic"]
        
        await mqtt_client.disconnect()
        
        assert not mqtt_client._connected
        assert mqtt_client.client is None
        assert mqtt_client._subscribed_topics == []
        mock_mqtt_client.loop_stop.assert_called_once()
        mock_mqtt_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_success(self, mqtt_client, mock_mqtt_client):
        """Test successful topic subscription."""
        mqtt_client._connected = True
        mqtt_client.client = mock_mqtt_client
        
        topics = ["test/topic1", "test/topic2"]
        result = await mqtt_client.subscribe(topics)
        
        assert result is True
        assert mqtt_client._subscribed_topics == topics
        assert mock_mqtt_client.subscribe.call_count == 2

    @pytest.mark.asyncio
    async def test_subscribe_not_connected(self, mqtt_client):
        """Test subscription when not connected."""
        result = await mqtt_client.subscribe(["test/topic"])
        assert result is False

    @pytest.mark.asyncio
    async def test_subscribe_duplicate_topics(self, mqtt_client, mock_mqtt_client):
        """Test subscription to already subscribed topics."""
        mqtt_client._connected = True
        mqtt_client.client = mock_mqtt_client
        mqtt_client._subscribed_topics = ["test/topic"]
        
        result = await mqtt_client.subscribe(["test/topic"])
        
        assert result is True
        # Should not call subscribe again for duplicate topic
        mock_mqtt_client.subscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_listening(self, mqtt_client, mock_mqtt_client):
        """Test starting to listen for MQTT messages."""
        mqtt_client._connected = True
        mqtt_client.client = mock_mqtt_client
        
        with patch.object(mqtt_client, 'subscribe') as mock_subscribe:
            mock_subscribe.return_value = True
            
            await mqtt_client.start_listening()
            
            # Should subscribe to default Home Assistant topics
            expected_topics = [
                "homeassistant/+/+/state",
                "homeassistant/sensor/+/state",
                "homeassistant/binary_sensor/+/state",
                "homeassistant/switch/+/state",
                "homeassistant/light/+/state",
                "homeassistant/climate/+/state"
            ]
            mock_subscribe.assert_called_once_with(expected_topics)

    @pytest.mark.asyncio
    async def test_stop_listening(self, mqtt_client, mock_mqtt_client):
        """Test stopping MQTT message listening."""
        mqtt_client._connected = True
        mqtt_client.client = mock_mqtt_client
        mqtt_client._subscribed_topics = ["test/topic1", "test/topic2"]
        
        await mqtt_client.stop_listening()
        
        assert mock_mqtt_client.unsubscribe.call_count == 2
        assert mqtt_client._subscribed_topics == []

    def test_is_connected(self, mqtt_client):
        """Test connection status check."""
        assert not mqtt_client.is_connected()
        
        mqtt_client._connected = True
        assert mqtt_client.is_connected()

    def test_set_message_handler(self, mqtt_client):
        """Test setting message handler callback."""
        def mock_handler(topic, payload, timestamp):
            pass
        
        mqtt_client.set_message_handler(mock_handler)
        assert mqtt_client._message_handler == mock_handler

    @pytest.mark.asyncio
    async def test_handle_message_with_handler(self, mqtt_client):
        """Test message handling with callback handler."""
        handler_called = False
        handler_args = None
        
        def mock_handler(topic, payload, timestamp):
            nonlocal handler_called, handler_args
            handler_called = True
            handler_args = (topic, payload, timestamp)
        
        mqtt_client.set_message_handler(mock_handler)
        
        topic = "test/topic"
        payload = "test payload"
        timestamp = datetime.utcnow()
        
        await mqtt_client._handle_message(topic, payload, timestamp)
        
        assert handler_called
        assert handler_args == (topic, payload, timestamp)

    @pytest.mark.asyncio
    async def test_handle_message_without_handler(self, mqtt_client):
        """Test message handling without callback handler."""
        topic = "test/topic"
        payload = "test payload"
        timestamp = datetime.utcnow()
        
        # Should not raise any exceptions
        await mqtt_client._handle_message(topic, payload, timestamp)

    @pytest.mark.asyncio
    async def test_handle_message_with_async_handler(self, mqtt_client):
        """Test message handling with async callback handler."""
        handler_called = False
        handler_args = None
        
        async def mock_async_handler(topic, payload, timestamp):
            nonlocal handler_called, handler_args
            handler_called = True
            handler_args = (topic, payload, timestamp)
        
        mqtt_client.set_message_handler(mock_async_handler)
        
        topic = "test/topic"
        payload = "test payload"
        timestamp = datetime.utcnow()
        
        await mqtt_client._handle_message(topic, payload, timestamp)
        
        assert handler_called
        assert handler_args == (topic, payload, timestamp)

    @pytest.mark.asyncio
    async def test_reconnect_success(self, mqtt_client):
        """Test successful reconnection."""
        mqtt_client._reconnect_attempts = 1
        
        with patch.object(mqtt_client, 'connect') as mock_connect:
            mock_connect.return_value = True
            
            await mqtt_client._reconnect()
            
            assert mqtt_client._reconnect_attempts == 2
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_reconnect_max_attempts(self, mqtt_client):
        """Test reconnection with max attempts reached."""
        mqtt_client._reconnect_attempts = 5
        mqtt_client._max_reconnect_attempts = 5
        
        with patch.object(mqtt_client, 'connect') as mock_connect:
            await mqtt_client._reconnect()
            
            # Should not attempt reconnection
            mock_connect.assert_not_called()

    def test_mqtt_callbacks(self, mqtt_client):
        """Test MQTT callback methods."""
        # Test on_connect success
        mqtt_client._on_connect(None, None, None, 0)
        assert mqtt_client._connected
        
        # Test on_connect failure
        mqtt_client._connected = False
        mqtt_client._on_connect(None, None, None, 1)
        assert not mqtt_client._connected
        
        # Test on_disconnect
        mqtt_client._connected = True
        mqtt_client._on_disconnect(None, None, 1)
        assert not mqtt_client._connected
        
        # Test on_subscribe
        mqtt_client._on_subscribe(None, None, 1, [1])
        
        # Test on_log
        mqtt_client._on_log(None, None, 0, "test log")
        mqtt_client._on_log(None, None, 1, "test warning")
        mqtt_client._on_log(None, None, 2, "test error")

    @pytest.mark.asyncio
    async def test_mqtt_on_message(self, mqtt_client):
        """Test MQTT on_message callback."""
        message_received = False
        message_data = None
        
        def mock_handler(topic, payload, timestamp):
            nonlocal message_received, message_data
            message_received = True
            message_data = (topic, payload, timestamp)
        
        mqtt_client.set_message_handler(mock_handler)
        
        # Create mock message
        mock_msg = Mock()
        mock_msg.topic = "test/topic"
        mock_msg.payload = b"test payload"
        mock_msg.qos = 1
        
        with patch('asyncio.create_task') as mock_create_task:
            mqtt_client._on_message(None, None, mock_msg)
            
            # Should create task for async message handling
            mock_create_task.assert_called_once()
            
            # Extract and execute the task
            task = mock_create_task.call_args[0][0]
            await task
            
            assert message_received
            assert message_data == ("test/topic", "test payload", message_data[2])


if __name__ == "__main__":
    pytest.main([__file__])
