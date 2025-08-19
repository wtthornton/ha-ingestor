"""InfluxDB point models for Home Assistant data storage."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InfluxDBPoint(BaseModel):
    """Model for InfluxDB data points."""

    measurement: str = Field(..., description="Measurement name")
    tags: dict[str, str] = Field(..., description="Point tags")
    fields: dict[str, Any] = Field(..., description="Point fields")
    timestamp: datetime = Field(..., description="Point timestamp")

    @field_validator("measurement")
    @classmethod
    def validate_measurement(cls, v: str) -> str:
        """Validate measurement name."""
        if not v or not v.strip():
            raise ValueError("Measurement name cannot be empty")

        # InfluxDB measurement names should be alphanumeric with underscores
        measurement = v.strip()
        if not measurement.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Measurement name must contain only alphanumeric characters, underscores, and hyphens"
            )

        return measurement

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate point tags."""
        if not isinstance(v, dict):
            raise ValueError("Tags must be a dictionary")

        validated_tags = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Tag keys must be strings")

            if not isinstance(value, str):
                raise ValueError("Tag values must be strings")

            # InfluxDB tag keys and values have length limits
            if len(key) > 64:
                raise ValueError(f"Tag key '{key}' exceeds 64 character limit")

            if len(value) > 64:
                raise ValueError(f"Tag value '{value}' exceeds 64 character limit")

            # InfluxDB tag keys and values cannot contain certain characters
            if any(char in key for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Tag key '{key}' contains invalid characters")

            if any(char in value for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Tag value '{value}' contains invalid characters")

            validated_tags[key] = value

        return validated_tags

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate point fields."""
        if not isinstance(v, dict):
            raise ValueError("Fields must be a dictionary")

        validated_fields = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Field keys must be strings")

            # InfluxDB field keys have length limits
            if len(key) > 64:
                raise ValueError(f"Field key '{key}' exceeds 64 character limit")

            # InfluxDB field keys cannot contain certain characters
            if any(char in key for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Field key '{key}' contains invalid characters")

            # Validate field value types
            if isinstance(value, (int, float, str, bool)):
                validated_fields[key] = value
            else:
                # Convert other types to string if possible
                try:
                    validated_fields[key] = str(value)
                except Exception:
                    raise ValueError(
                        f"Field value for '{key}' cannot be converted to supported type"
                    )

        return validated_fields

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate timestamp."""
        if not isinstance(v, datetime):
            raise ValueError("Timestamp must be a datetime object")

        return v

    def to_line_protocol(self) -> str:
        """Convert point to InfluxDB line protocol format.

        Returns:
            Line protocol string representation.
        """
        # Escape measurement name if needed
        measurement = self._escape_measurement(self.measurement)

        # Format tags
        tags_str = ""
        if self.tags:
            tag_pairs = []
            for key, value in sorted(self.tags.items()):
                escaped_key = self._escape_tag_key(key)
                escaped_value = self._escape_tag_value(value)
                tag_pairs.append(f"{escaped_key}={escaped_value}")
            tags_str = "," + ",".join(tag_pairs)

        # Format fields
        field_pairs = []
        for key, value in sorted(self.fields.items()):
            escaped_key = self._escape_field_key(key)
            if isinstance(value, str):
                escaped_value = f'"{self._escape_field_value(value)}"'
            elif isinstance(value, bool):
                escaped_value = str(value).lower()
            else:
                escaped_value = str(value)
            field_pairs.append(f"{escaped_key}={escaped_value}")

        fields_str = ",".join(field_pairs)

        # Format timestamp (nanoseconds since epoch)
        timestamp_ns = int(self.timestamp.timestamp() * 1e9)

        # Combine all parts
        line = f"{measurement}{tags_str} {fields_str} {timestamp_ns}"
        return line

    def _escape_measurement(self, measurement: str) -> str:
        """Escape measurement name for line protocol."""
        # Escape commas and spaces
        return measurement.replace(",", "\\,").replace(" ", "\\ ")

    def _escape_tag_key(self, key: str) -> str:
        """Escape tag key for line protocol."""
        # Escape commas, spaces, and equals signs
        return key.replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")

    def _escape_tag_value(self, value: str) -> str:
        """Escape tag value for line protocol."""
        # Escape commas, spaces, and equals signs
        return value.replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")

    def _escape_field_key(self, key: str) -> str:
        """Escape field key for line protocol."""
        # Escape commas and spaces
        return key.replace(",", "\\,").replace(" ", "\\ ")

    def _escape_field_value(self, value: str) -> str:
        """Escape field value for line protocol."""
        # Escape quotes
        return value.replace('"', '\\"')

    def to_dict(self) -> dict[str, Any]:
        """Convert point to dictionary for storage."""
        return {
            "measurement": self.measurement,
            "tags": self.tags,
            "fields": self.fields,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InfluxDBPoint":
        """Create InfluxDBPoint from dictionary.

        Args:
            data: Dictionary with point data

        Returns:
            InfluxDBPoint instance
        """
        # Parse timestamp if it's a string
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            measurement=data["measurement"],
            tags=data["tags"],
            fields=data["fields"],
            timestamp=timestamp,
        )

    @classmethod
    def from_event(
        cls,
        event: Any,
        measurement: str,
        tags: dict[str, str],
        fields: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> "InfluxDBPoint":
        """Create InfluxDBPoint from an event object.

        Args:
            event: Event object (MQTTEvent, WebSocketEvent, etc.)
            measurement: Measurement name
            tags: Point tags
            fields: Point fields
            timestamp: Point timestamp (defaults to event timestamp)

        Returns:
            InfluxDBPoint instance
        """
        if timestamp is None and hasattr(event, "timestamp"):
            timestamp = event.timestamp

        if timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            measurement=measurement, tags=tags, fields=fields, timestamp=timestamp
        )

    def get_size_estimate(self) -> int:
        """Get estimated size of the point in bytes.

        Returns:
            Estimated size in bytes.
        """
        # Rough estimation for line protocol size
        measurement_size = len(self.measurement)

        tags_size = sum(
            len(k) + len(v) + 2 for k, v in self.tags.items()
        )  # +2 for = and ,
        if tags_size > 0:
            tags_size += 1  # +1 for leading comma

        fields_size = sum(
            len(k) + len(str(v)) + 1 for k, v in self.fields.items()
        )  # +1 for =
        if fields_size > 0:
            fields_size -= 1  # -1 for last field (no trailing comma)

        timestamp_size = 20  # Approximate size for nanosecond timestamp

        # Add separators and spaces
        total_size = measurement_size + tags_size + 1 + fields_size + 1 + timestamp_size

        return total_size
