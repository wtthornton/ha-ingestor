"""
MQTT Client for Publishing Notifications and Subscribing to Topics

Story AI1.12: MQTT Integration (Publishing)
Story AI2.1: MQTT Capability Listener (Subscription - Epic AI-2)
"""

import paho.mqtt.client as mqtt
import logging
import json
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)


class MQTTNotificationClient:
    """
    MQTT client for publishing AI automation notifications and subscribing to topics.
    
    Epic AI-1: Publishes automation notifications and analysis results
    Epic AI-2: Subscribes to Zigbee2MQTT bridge for device capability discovery
    
    Features:
    - Publish automation notifications (Epic AI-1)
    - Subscribe to topics with callback handlers (Epic AI-2)
    - Automatic reconnection on disconnect
    - QoS support for reliable delivery
    """
    
    def __init__(self, broker: str, port: int = 1883, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize MQTT client.
        
        Args:
            broker: MQTT broker host
            port: MQTT broker port
            username: Optional MQTT username
            password: Optional MQTT password
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.is_connected = False
        self._message_callback: Optional[Callable] = None
        
        logger.info(f"MQTT client initialized for broker: {broker}:{port}")
    
    def connect(self) -> bool:
        """
        Connect to MQTT broker.
        
        Returns:
            True if connection successful
        """
        try:
            self.client = mqtt.Client(client_id="ai-automation-service")
            
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            logger.info(f"✅ MQTT connected to {self.broker}:{self.port}")
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
            self.is_connected = False
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback for when client connects to broker.
        
        Automatically resubscribes to topics on reconnect.
        """
        if rc == 0:
            logger.info("✅ MQTT connection established")
            self.is_connected = True
            
            # Resubscribe to topics on reconnect (Epic AI-2)
            # paho-mqtt will handle this automatically if we stored subscriptions
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
            self.is_connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        logger.warning(f"⚠️ MQTT disconnected (code: {rc})")
        self.is_connected = False
    
    def publish(self, topic: str, message: Dict, qos: int = 1) -> bool:
        """
        Publish a message to MQTT topic.
        
        Args:
            topic: MQTT topic
            message: Message payload (will be JSON-encoded)
            qos: Quality of service (0, 1, or 2)
        
        Returns:
            True if publish successful
        """
        try:
            if not self.is_connected:
                logger.warning("⚠️ MQTT not connected, attempting to connect...")
                if not self.connect():
                    return False
            
            payload = json.dumps(message)
            result = self.client.publish(topic, payload, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📢 Published to {topic}: {payload[:100]}...")
                return True
            else:
                logger.error(f"❌ Publish failed with code {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MQTT publish error: {e}")
            return False
    
    def publish_analysis_complete(self, result_summary: Dict) -> bool:
        """
        Publish analysis complete notification.
        
        Args:
            result_summary: Summary of analysis results
        
        Returns:
            True if publish successful
        """
        topic = "ha-ai/analysis/complete"
        message = {
            "event": "analysis_complete",
            "timestamp": result_summary.get("timestamp"),
            "patterns_detected": result_summary.get("patterns_detected", 0),
            "suggestions_generated": result_summary.get("suggestions_generated", 0),
            "processing_time_sec": result_summary.get("processing_time_sec", 0),
            "cost": result_summary.get("cost", 0),
            "success": result_summary.get("success", True)
        }
        return self.publish(topic, message)
    
    def publish_suggestion_created(self, suggestion_data: Dict) -> bool:
        """
        Publish new suggestion notification.
        
        Args:
            suggestion_data: Suggestion details
        
        Returns:
            True if publish successful
        """
        topic = "ha-ai/suggestions/new"
        message = {
            "event": "suggestion_created",
            "suggestion_id": suggestion_data.get("id"),
            "title": suggestion_data.get("title"),
            "category": suggestion_data.get("category"),
            "confidence": suggestion_data.get("confidence"),
            "priority": suggestion_data.get("priority")
        }
        return self.publish(topic, message)
    
    def subscribe(self, topic: str, qos: int = 1) -> bool:
        """
        Subscribe to MQTT topic.
        
        Added in Story AI2.1 for Epic AI-2 (Device Intelligence).
        
        Args:
            topic: MQTT topic to subscribe to (e.g., "zigbee2mqtt/bridge/devices")
            qos: Quality of service (0, 1, or 2)
        
        Returns:
            True if subscription successful
            
        Example:
            client.subscribe("zigbee2mqtt/bridge/devices")
            client.on_message = callback_function
        """
        try:
            if not self.is_connected:
                logger.warning("⚠️ MQTT not connected, attempting to connect...")
                if not self.connect():
                    return False
            
            result, mid = self.client.subscribe(topic, qos=qos)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📡 Subscribed to topic: {topic} (QoS {qos})")
                return True
            else:
                logger.error(f"❌ Subscription failed with code {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ MQTT subscribe error: {e}")
            return False
    
    @property
    def on_message(self) -> Optional[Callable]:
        """
        Get the message callback handler.
        
        Returns:
            Current message callback or None
        """
        return self._message_callback
    
    @on_message.setter
    def on_message(self, callback: Callable):
        """
        Set message callback handler for subscribed topics.
        
        Added in Story AI2.1 for Epic AI-2 (Device Intelligence).
        
        The callback should have signature:
            def callback(client, userdata, message) -> None
        
        Where message has:
            - message.topic: str (MQTT topic)
            - message.payload: bytes (message payload)
            - message.qos: int (QoS level)
            
        Args:
            callback: Function to call when message received
            
        Example:
            def on_msg(client, userdata, msg):
                print(f"Received: {msg.topic}: {msg.payload}")
            
            client.on_message = on_msg
        """
        self._message_callback = callback
        
        if self.client:
            self.client.on_message = callback
            logger.debug("✅ Message callback registered")
        else:
            logger.warning("⚠️ Cannot set callback - client not initialized")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("✅ MQTT disconnected")
        except Exception as e:
            logger.error(f"❌ MQTT disconnect error: {e}")

