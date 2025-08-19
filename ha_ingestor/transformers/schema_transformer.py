"""Schema transformation logic for converting to optimized InfluxDB schema.

This module implements the transformation logic to convert existing Home Assistant
events to the new optimized schema structure, including field mapping, tag
optimization, and measurement consolidation.
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Any

from ..models.mqtt_event import MQTTEvent
from ..models.optimized_schema import OptimizedInfluxDBPoint, SchemaOptimizer
from ..models.websocket_event import WebSocketEvent
from ..transformers.base import TransformationResult, Transformer


class SchemaTransformer(Transformer):
    """Transforms Home Assistant events to optimized InfluxDB schema."""

    def __init__(
        self,
        name: str,
        config: dict[str, Any] | None = None,
        measurement_consolidation: bool = True,
        tag_optimization: bool = True,
        field_optimization: bool = True,
        compression_enabled: bool = True,
    ):
        """Initialize schema transformer.

        Args:
            name: Transformer name
            config: Configuration dictionary
            measurement_consolidation: Enable measurement consolidation
            tag_optimization: Enable tag optimization
            field_optimization: Enable field optimization
            compression_enabled: Enable data compression
        """
        super().__init__(name, config or {})
        self.measurement_consolidation = measurement_consolidation
        self.tag_optimization = tag_optimization
        self.field_optimization = field_optimization
        self.compression_enabled = compression_enabled

        # Initialize schema optimizer
        self.schema_optimizer = SchemaOptimizer(config)

        # Measurement mapping for consolidation
        self.measurement_mapping = {
            # Entity state changes
            "state_changed": "ha_entities",
            "state_update": "ha_entities",
            # Service calls
            "call_service": "ha_services",
            "service_executed": "ha_services",
            # Automations
            "automation_triggered": "ha_automations",
            "automation_executed": "ha_automations",
            # Device events
            "device_registered": "ha_devices",
            "device_updated": "ha_devices",
            # System events
            "system_started": "ha_system",
            "system_stopped": "ha_system",
            "config_changed": "ha_system",
        }

        # Tag optimization rules
        self.tag_optimization_rules = {
            "entity_id": {
                "max_length": 64,
                "hash_threshold": 1000,
                "group_by_pattern": True,
            },
            "context_id": {
                "max_length": 64,
                "hash_threshold": 500,
                "group_by_pattern": False,
            },
            "user_id": {
                "max_length": 64,
                "hash_threshold": 100,
                "group_by_pattern": False,
            },
        }

        # Field optimization rules
        self.field_optimization_rules = {
            "state": {
                "type": "string",
                "max_length": 256,
                "compress_long": True,
            },
            "payload": {
                "type": "json",
                "max_length": 512,
                "compress_long": True,
            },
            "attributes": {
                "type": "json",
                "max_length": 1024,
                "compress_long": True,
            },
        }

    def transform(self, data: Any) -> TransformationResult:
        """Transform event data to optimized schema.

        Args:
            data: Event data to transform

        Returns:
            Transformation result with optimized data
        """
        try:
            if isinstance(data, (MQTTEvent, WebSocketEvent)):
                optimized_point = self._transform_event(data)
                return TransformationResult(
                    success=True,
                    data=optimized_point,
                    metadata={
                        "transformer": self.name,
                        "original_type": type(data).__name__,
                        "optimization_score": optimized_point.get_optimization_score(),
                        "storage_saved_bytes": self._calculate_storage_savings(
                            data, optimized_point
                        ),
                    },
                )
            else:
                return TransformationResult(
                    success=False,
                    data=data,
                    errors=[f"Unsupported data type: {type(data).__name__}"],
                    metadata={"transformer": self.name},
                )

        except Exception as e:
            return TransformationResult(
                success=False,
                data=data,
                errors=[f"Transformation failed: {str(e)}"],
                metadata={"transformer": self.name, "error": str(e)},
            )

    def _transform_event(
        self, event: MQTTEvent | WebSocketEvent
    ) -> OptimizedInfluxDBPoint:
        """Transform a single event to optimized schema.

        Args:
            event: Event to transform

        Returns:
            Optimized InfluxDB point
        """
        # Determine measurement name
        measurement = self._get_optimized_measurement(event)

        # Generate optimized tags
        tags = self._generate_optimized_tags(event)

        # Generate optimized fields
        fields = self._generate_optimized_fields(event)

        # Create optimized point
        optimized_point = OptimizedInfluxDBPoint(
            measurement=measurement,
            timestamp=event.timestamp,
            tags=tags,
            fields=fields,
            metadata={
                "original_event_type": self._get_event_type(event),
                "transformation_timestamp": datetime.utcnow().isoformat(),
                "optimization_enabled": {
                    "measurement_consolidation": self.measurement_consolidation,
                    "tag_optimization": self.tag_optimization,
                    "field_optimization": self.field_optimization,
                    "compression_enabled": self.compression_enabled,
                },
            },
        )

        # Apply schema optimization if enabled
        if self.tag_optimization or self.field_optimization:
            optimized_point = self.schema_optimizer.optimize_point(optimized_point)

        return optimized_point

    def _get_optimized_measurement(
        self, event: MQTTEvent | WebSocketEvent
    ) -> str:
        """Get optimized measurement name for the event.

        Args:
            event: Event to get measurement for

        Returns:
            Optimized measurement name
        """
        if isinstance(event, MQTTEvent):
            # For MQTT events, use consolidated measurement based on domain
            if self.measurement_consolidation:
                return "ha_entities"
            else:
                return f"ha_{event.domain}"

        elif isinstance(event, WebSocketEvent):
            # For WebSocket events, use consolidated measurement based on event type
            if self.measurement_consolidation:
                event_type = event.event_type
                return self.measurement_mapping.get(event_type, "ha_events")
            else:
                return f"ha_{event.event_type}"

        return "ha_events"

    def _generate_optimized_tags(
        self, event: MQTTEvent | WebSocketEvent
    ) -> dict[str, str]:
        """Generate optimized tags for the event.

        Args:
            event: Event to generate tags for

        Returns:
            Optimized tags dictionary
        """
        tags = {}

        if isinstance(event, MQTTEvent):
            # Core tags
            tags.update(
                {
                    "domain": event.domain or "unknown",
                    "entity_type": "device",
                    "source": "mqtt",
                    "event_category": "state_change",
                }
            )

            # Entity grouping
            if event.entity_id:
                entity_group = self._extract_entity_group(event.entity_id)
                if entity_group:
                    tags["entity_group"] = entity_group

                # Apply tag optimization rules
                if self.tag_optimization:
                    tags["entity_id"] = self._optimize_tag_value(
                        "entity_id", event.entity_id
                    )
                else:
                    tags["entity_id"] = event.entity_id

            # Device classification
            if event.attributes:
                device_class = event.attributes.get("device_class")
                if device_class:
                    tags["device_class"] = str(device_class)

                manufacturer = event.attributes.get("manufacturer")
                if manufacturer:
                    tags["manufacturer"] = str(manufacturer)

                model = event.attributes.get("model")
                if model:
                    tags["model"] = str(model)

        elif isinstance(event, WebSocketEvent):
            # Core tags
            tags.update(
                {
                    "event_type": event.event_type,
                    "source": "websocket",
                    "event_category": self._categorize_websocket_event(
                        event.event_type
                    ),
                }
            )

            # Entity information
            if event.entity_id:
                entity_group = self._extract_entity_group(event.entity_id)
                if entity_group:
                    tags["entity_group"] = entity_group

                if self.tag_optimization:
                    tags["entity_id"] = self._optimize_tag_value(
                        "entity_id", event.entity_id
                    )
                else:
                    tags["entity_id"] = event.entity_id

            if event.domain:
                tags["domain"] = event.domain

            # Context information
            if event.data:
                context_id = event.data.get("context_id")
                if context_id:
                    if self.tag_optimization:
                        tags["context_id"] = self._optimize_tag_value(
                            "context_id", str(context_id)
                        )
                    else:
                        tags["context_id"] = str(context_id)

                user_id = event.data.get("context_user_id")
                if user_id:
                    if self.tag_optimization:
                        tags["user_id"] = self._optimize_tag_value(
                            "user_id", str(user_id)
                        )
                    else:
                        tags["user_id"] = str(user_id)

        return tags

    def _generate_optimized_fields(
        self, event: MQTTEvent | WebSocketEvent
    ) -> dict[str, Any]:
        """Generate optimized fields for the event.

        Args:
            event: Event to generate fields for

        Returns:
            Optimized fields dictionary
        """
        fields = {}

        if isinstance(event, MQTTEvent):
            # Core state information
            fields["state"] = event.state
            fields["state_numeric"] = self._convert_state_to_numeric(event.state)

            # Structured attributes
            if event.attributes:
                fields["attributes"] = self._optimize_attributes(event.attributes)
                fields["attributes_common"] = self._extract_common_attributes(
                    event.attributes
                )
                fields["attributes_custom"] = self._extract_custom_attributes(
                    event.attributes
                )

            # Metadata
            fields["payload_size"] = len(str(event.payload))
            fields["topic"] = event.topic

        elif isinstance(event, WebSocketEvent):
            # Core event information
            fields["event_type"] = event.event_type
            fields["event_id"] = self._generate_event_id(event)

            # Event-specific data
            if event.data:
                fields["event_data"] = self._optimize_event_data(event.data)

                # Extract specific information based on event type
                if event.event_type == "state_changed":
                    state_info = event.get_state_change_info()
                    if state_info:
                        fields["state_change"] = state_info

                elif event.event_type == "call_service":
                    service_info = event.get_service_call_info()
                    if service_info:
                        fields["service_call"] = service_info

                elif event.event_type == "automation_triggered":
                    automation_info = event.get_automation_info()
                    if automation_info:
                        fields["automation"] = automation_info

            # Metadata
            fields["payload_size"] = len(str(event.data)) if event.data else 0

        # Common metadata
        fields["processing_timestamp"] = datetime.utcnow().isoformat()
        fields["original_timestamp"] = event.timestamp.isoformat()

        return fields

    def _extract_entity_group(self, entity_id: str) -> str | None:
        """Extract entity group from entity ID.

        Args:
            entity_id: Entity ID to extract group from

        Returns:
            Entity group name or None
        """
        # Common entity group patterns
        patterns = [
            r"^(\w+)_",  # living_room_light -> living_room
            r"_(\w+)_",  # sensor_living_room_temperature -> living_room
            r"^(\w+)$",  # kitchen -> kitchen
        ]

        for pattern in patterns:
            match = re.match(pattern, entity_id)
            if match:
                group = match.group(1)
                # Validate group name
                if len(group) <= 32 and group.replace("_", "").isalnum():
                    return group

        return None

    def _categorize_websocket_event(self, event_type: str) -> str:
        """Categorize WebSocket event type.

        Args:
            event_type: Event type to categorize

        Returns:
            Event category
        """
        if event_type in ["state_changed", "state_update"]:
            return "state_change"
        elif event_type in ["call_service", "service_executed"]:
            return "service_call"
        elif event_type in ["automation_triggered", "automation_executed"]:
            return "automation"
        elif event_type in ["device_registered", "device_updated"]:
            return "device"
        elif event_type in ["system_started", "system_stopped", "config_changed"]:
            return "system"
        else:
            return "other"

    def _optimize_tag_value(self, tag_key: str, tag_value: str) -> str:
        """Optimize tag value based on optimization rules.

        Args:
            tag_key: Tag key
            tag_value: Tag value to optimize

        Returns:
            Optimized tag value
        """
        if tag_key not in self.tag_optimization_rules:
            return tag_value

        rules = self.tag_optimization_rules[tag_key]

        # Check length limit
        if len(tag_value) > rules["max_length"]:
            if rules["hash_threshold"] > 0:
                # Hash long values
                return f"hash_{hashlib.md5(tag_value.encode()).hexdigest()[:16]}"
            else:
                # Truncate
                return tag_value[: rules["max_length"]]

        return tag_value

    def _convert_state_to_numeric(self, state: Any) -> int | float | None:
        """Convert state value to numeric representation.

        Args:
            state: State value to convert

        Returns:
            Numeric value or None
        """
        if isinstance(state, (int, float)):
            return state

        if isinstance(state, str):
            # Try to convert common state values
            state_lower = state.lower()

            # Boolean states
            if state_lower in ["on", "true", "yes", "1"]:
                return 1
            elif state_lower in ["off", "false", "no", "0"]:
                return 0

            # Try numeric conversion
            try:
                return float(state)
            except ValueError:
                pass

        return None

    def _optimize_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Optimize attributes for storage.

        Args:
            attributes: Attributes to optimize

        Returns:
            Optimized attributes
        """
        if not self.field_optimization:
            return attributes

        optimized = {}
        for key, value in attributes.items():
            if isinstance(value, (int, float, bool)):
                optimized[key] = value
            elif isinstance(value, str):
                if len(value) <= 256:
                    optimized[key] = value
                else:
                    optimized[key] = (
                        f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"
                    )
            else:
                # Convert to JSON string
                try:
                    json_str = json.dumps(value)
                    if len(json_str) <= 512:
                        optimized[key] = json_str
                    else:
                        optimized[key] = (
                            f"hash_{hashlib.md5(json_str.encode()).hexdigest()[:16]}"
                        )
                except Exception:
                    optimized[key] = str(value)[:256]

        return optimized

    def _extract_common_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Extract common attributes for structured storage.

        Args:
            attributes: All attributes

        Returns:
            Common attributes dictionary
        """
        common_keys = [
            "friendly_name",
            "unit_of_measurement",
            "device_class",
            "icon",
            "assumed_state",
            "supported_features",
        ]

        common_attrs = {}
        for key in common_keys:
            if key in attributes:
                value = attributes[key]
                if isinstance(value, (str, int, float, bool)):
                    common_attrs[key] = value

        return common_attrs

    def _extract_custom_attributes(self, attributes: dict[str, Any]) -> dict[str, Any]:
        """Extract custom attributes for flexible storage.

        Args:
            attributes: All attributes

        Returns:
            Custom attributes dictionary
        """
        common_keys = {
            "friendly_name",
            "unit_of_measurement",
            "device_class",
            "icon",
            "assumed_state",
            "supported_features",
        }

        custom_attrs = {}
        for key, value in attributes.items():
            if key not in common_keys:
                custom_attrs[key] = value

        return custom_attrs

    def _optimize_event_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Optimize event data for storage.

        Args:
            data: Event data to optimize

        Returns:
            Optimized event data
        """
        if not self.field_optimization:
            return data

        optimized = {}
        for key, value in data.items():
            if isinstance(value, (int, float, bool)):
                optimized[key] = value
            elif isinstance(value, str):
                if len(value) <= 256:
                    optimized[key] = value
                else:
                    optimized[key] = (
                        f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"
                    )
            elif isinstance(value, (list, dict)):
                try:
                    json_str = json.dumps(value)
                    if len(json_str) <= 512:
                        optimized[key] = json_str
                    else:
                        optimized[key] = (
                            f"hash_{hashlib.md5(json_str.encode()).hexdigest()[:16]}"
                        )
                except Exception:
                    optimized[key] = str(value)[:256]
            else:
                optimized[key] = str(value)[:256]

        return optimized

    def _generate_event_id(self, event: WebSocketEvent) -> str:
        """Generate unique event ID.

        Args:
            event: Event to generate ID for

        Returns:
            Unique event ID
        """
        # Create unique identifier from event data
        identifier_parts = [
            event.event_type,
            str(event.timestamp.timestamp()),
            str(event.data) if event.data else "",
        ]

        identifier = "|".join(identifier_parts)
        return hashlib.md5(identifier.encode()).hexdigest()[:16]

    def _get_event_type(self, event: MQTTEvent | WebSocketEvent) -> str:
        """Get event type identifier.

        Args:
            event: Event to get type for

        Returns:
            Event type string
        """
        if isinstance(event, MQTTEvent):
            return "mqtt"
        elif isinstance(event, WebSocketEvent):
            return "websocket"
        else:
            return "unknown"

    def _calculate_storage_savings(
        self,
        original: MQTTEvent | WebSocketEvent,
        optimized: OptimizedInfluxDBPoint,
    ) -> int:
        """Calculate storage savings from optimization.

        Args:
            original: Original event
            optimized: Optimized point

        Returns:
            Storage savings in bytes
        """
        # Estimate original size
        original_size = len(str(original))

        # Get optimized size
        optimized_size = optimized.get_size_estimate()

        return max(0, original_size - optimized_size)

    def get_transformation_stats(self) -> dict[str, Any]:
        """Get transformation statistics.

        Returns:
            Dictionary with transformation statistics
        """
        return {
            "transformer_name": self.name,
            "measurement_consolidation": self.measurement_consolidation,
            "tag_optimization": self.tag_optimization,
            "field_optimization": self.field_optimization,
            "compression_enabled": self.compression_enabled,
            "schema_optimization": self.schema_optimizer.get_optimization_report(),
        }
