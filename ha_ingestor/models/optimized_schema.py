"""Optimized InfluxDB schema models for Home Assistant data storage.

This module implements the new optimized schema design that addresses
cardinality issues, improves query performance, and reduces storage overhead.
"""

import hashlib
import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class OptimizedInfluxDBPoint(BaseModel):
    """Optimized InfluxDB data point with improved tag and field structure."""

    # Core measurement and timestamp
    measurement: str = Field(..., description="Optimized measurement name")
    timestamp: datetime = Field(..., description="Point timestamp")

    # Optimized tag structure with cardinality management
    tags: dict[str, str] = Field(..., description="Optimized point tags")

    # Structured field structure for better performance
    fields: dict[str, Any] = Field(..., description="Optimized point fields")

    # Metadata for tracking and optimization
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Point metadata for optimization tracking"
    )

    @field_validator("measurement")
    @classmethod
    def validate_measurement(cls, v: str) -> str:
        """Validate optimized measurement name."""
        if not v or not v.strip():
            raise ValueError("Measurement name cannot be empty")

        # Optimized measurements use consistent naming
        measurement = v.strip()
        if not measurement.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Measurement name must contain only alphanumeric characters, underscores, and hyphens"
            )

        return measurement

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate optimized point tags with cardinality management."""
        if not isinstance(v, dict):
            raise ValueError("Tags must be a dictionary")

        validated_tags = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Tag keys must be strings")

            if not isinstance(value, str):
                raise ValueError("Tag values must be strings")

            # InfluxDB tag limits
            if len(key) > 64:
                raise ValueError(f"Tag key '{key}' exceeds 64 character limit")

            if len(value) > 64:
                raise ValueError(f"Tag value '{value}' exceeds 64 character limit")

            # InfluxDB tag character restrictions
            if any(char in key for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Tag key '{key}' contains invalid characters")

            if any(char in value for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Tag value '{value}' contains invalid characters")

            validated_tags[key] = value

        return validated_tags

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate optimized point fields with type standardization."""
        if not isinstance(v, dict):
            raise ValueError("Fields must be a dictionary")

        validated_fields = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Field keys must be strings")

            # InfluxDB field key limits
            if len(key) > 64:
                raise ValueError(f"Field key '{key}' exceeds 64 character limit")

            # InfluxDB field key character restrictions
            if any(char in key for char in ["=", " ", ",", "\n", "\r", "\t"]):
                raise ValueError(f"Field key '{key}' contains invalid characters")

            # Optimize field value types for better performance
            if isinstance(value, (int, float, bool)):
                validated_fields[key] = value
            elif isinstance(value, str):
                # Limit string field length for performance
                if len(value) <= 256:
                    validated_fields[key] = value
                else:
                    # Hash long strings to reduce cardinality
                    validated_fields[key] = (
                        f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"
                    )
            else:
                # Convert other types to JSON string
                try:
                    json_str = json.dumps(value)
                    if len(json_str) <= 256:
                        validated_fields[key] = json_str
                    else:
                        # Hash long JSON strings
                        validated_fields[key] = (
                            f"hash_{hashlib.md5(json_str.encode()).hexdigest()[:16]}"
                        )
                except Exception:
                    # Fallback to string conversion
                    str_value = str(value)
                    if len(str_value) <= 256:
                        validated_fields[key] = str_value
                    else:
                        validated_fields[key] = (
                            f"hash_{hashlib.md5(str_value.encode()).hexdigest()[:16]}"
                        )

        return validated_fields

    def to_line_protocol(self) -> str:
        """Convert optimized point to InfluxDB line protocol format."""
        # Escape measurement name
        measurement = self._escape_measurement(self.measurement)

        # Format optimized tags
        tags_str = ""
        if self.tags:
            tag_pairs = []
            for key, value in sorted(self.tags.items()):
                escaped_key = self._escape_tag_key(key)
                escaped_value = self._escape_tag_value(value)
                tag_pairs.append(f"{escaped_key}={escaped_value}")
            tags_str = "," + ",".join(tag_pairs)

        # Format optimized fields
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
        return measurement.replace(",", "\\,").replace(" ", "\\ ")

    def _escape_tag_key(self, key: str) -> str:
        """Escape tag key for line protocol."""
        return key.replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")

    def _escape_tag_value(self, value: str) -> str:
        """Escape tag value for line protocol."""
        return value.replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")

    def _escape_field_key(self, key: str) -> str:
        """Escape field key for line protocol."""
        return key.replace(",", "\\,").replace(" ", "\\ ")

    def _escape_field_value(self, value: str) -> str:
        """Escape field value for line protocol."""
        return value.replace('"', '\\"')

    def get_size_estimate(self) -> int:
        """Get estimated size of the optimized point in bytes."""
        # Rough estimation for line protocol size
        measurement_size = len(self.measurement)

        tags_size = sum(len(k) + len(v) + 2 for k, v in self.tags.items())
        if tags_size > 0:
            tags_size += 1

        fields_size = sum(len(k) + len(str(v)) + 1 for k, v in self.fields.items())
        if fields_size > 0:
            fields_size -= 1

        timestamp_size = 20
        metadata_size = len(json.dumps(self.metadata)) if self.metadata else 0

        total_size = (
            measurement_size
            + tags_size
            + 1
            + fields_size
            + 1
            + timestamp_size
            + metadata_size
        )
        return total_size

    def get_optimization_score(self) -> float:
        """Calculate optimization score based on schema efficiency."""
        score = 100.0

        # Penalize high cardinality tags
        high_cardinality_tags = ["entity_id", "context_id", "user_id"]
        for tag in high_cardinality_tags:
            if tag in self.tags:
                score -= 10.0

        # Penalize long string fields
        for value in self.fields.values():
            if isinstance(value, str) and len(value) > 100:
                score -= 5.0

        # Penalize too many tags
        if len(self.tags) > 8:
            score -= (len(self.tags) - 8) * 2.0

        # Penalize too many fields
        if len(self.fields) > 15:
            score -= (len(self.fields) - 15) * 1.0

        return max(0.0, score)


class OptimizedTagManager:
    """Manages tag cardinality and optimization for the new schema."""

    def __init__(self, max_tag_cardinality: int = 10000):
        """Initialize tag manager with cardinality limits."""
        self.max_tag_cardinality = max_tag_cardinality
        self.tag_cardinality_counts: dict[str, dict[str, int]] = {}
        self.tag_value_hashes: dict[str, dict[str, str]] = {}

    def optimize_tags(self, tags: dict[str, str]) -> dict[str, str]:
        """Optimize tags to reduce cardinality and improve performance."""
        optimized_tags = {}

        for key, value in tags.items():
            # Check if tag value exceeds cardinality limit
            if self._should_hash_tag_value(key, value):
                hashed_value = self._hash_tag_value(key, value)
                optimized_tags[f"{key}_hash"] = hashed_value
            else:
                optimized_tags[key] = value

            # Track cardinality
            self._track_tag_cardinality(key, value)

        return optimized_tags

    def _should_hash_tag_value(self, tag_key: str, tag_value: str) -> bool:
        """Determine if tag value should be hashed due to high cardinality."""
        if tag_key not in self.tag_cardinality_counts:
            return False

        # Check if the tag key has too many unique values
        unique_values_count = len(self.tag_cardinality_counts[tag_key])
        return unique_values_count > self.max_tag_cardinality

    def _hash_tag_value(self, tag_key: str, tag_value: str) -> str:
        """Hash tag value to reduce cardinality."""
        if tag_key not in self.tag_value_hashes:
            self.tag_value_hashes[tag_key] = {}

        if tag_value not in self.tag_value_hashes[tag_key]:
            # Create a shorter hash for better performance
            hash_value = hashlib.md5(tag_value.encode()).hexdigest()[:16]
            self.tag_value_hashes[tag_key][tag_value] = hash_value

        return self.tag_value_hashes[tag_key][tag_value]

    def _track_tag_cardinality(self, tag_key: str, tag_value: str) -> None:
        """Track tag cardinality for optimization decisions."""
        if tag_key not in self.tag_cardinality_counts:
            self.tag_cardinality_counts[tag_key] = {}

        if tag_value not in self.tag_cardinality_counts[tag_key]:
            self.tag_cardinality_counts[tag_key][tag_value] = 0

        self.tag_cardinality_counts[tag_key][tag_value] += 1

    def get_tag_statistics(self) -> dict[str, Any]:
        """Get statistics about tag usage and cardinality."""
        stats = {
            "total_tags": len(self.tag_cardinality_counts),
            "high_cardinality_tags": [],
            "tag_value_counts": {},
        }

        for tag_key, values in self.tag_cardinality_counts.items():
            total_values = len(values)
            stats["tag_value_counts"][tag_key] = total_values

            if total_values > self.max_tag_cardinality:
                stats["high_cardinality_tags"].append(
                    {
                        "tag": tag_key,
                        "cardinality": total_values,
                        "limit": self.max_tag_cardinality,
                    }
                )

        return stats


class OptimizedFieldManager:
    """Manages field optimization and type standardization."""

    def __init__(self):
        """Initialize field manager."""
        self.field_type_mappings: dict[str, str] = {}
        self.field_compression_stats: dict[str, int] = {}

    def optimize_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Optimize fields for better performance and storage efficiency."""
        optimized_fields = {}

        for key, value in fields.items():
            optimized_key = self._optimize_field_key(key)
            optimized_value = self._optimize_field_value(value)

            if optimized_value is not None:
                optimized_fields[optimized_key] = optimized_value

                # Track field type mappings
                self.field_type_mappings[optimized_key] = type(optimized_value).__name__

        return optimized_fields

    def _optimize_field_key(self, key: str) -> str:
        """Optimize field key for consistency and performance."""
        # Normalize field key naming
        normalized_key = key.lower().replace(" ", "_").replace("-", "_")

        # Remove common prefixes for consistency
        prefixes_to_remove = ["attr_", "data_", "event_"]
        for prefix in prefixes_to_remove:
            if normalized_key.startswith(prefix):
                normalized_key = normalized_key[len(prefix) :]
                break

        return normalized_key

    def _optimize_field_value(self, value: Any) -> Any:
        """Optimize field value for storage efficiency."""
        if isinstance(value, (int, float, bool)):
            return value

        if isinstance(value, str):
            # Compress long strings
            if len(value) > 256:
                compressed_value = self._compress_string(value)
                self.field_compression_stats["string_compression"] = (
                    self.field_compression_stats.get("string_compression", 0) + 1
                )
                return compressed_value
            return value

        if isinstance(value, (list, dict)):
            # Convert complex types to JSON strings
            try:
                json_str = json.dumps(value)
                if len(json_str) > 256:
                    compressed_value = self._compress_string(json_str)
                    self.field_compression_stats["json_compression"] = (
                        self.field_compression_stats.get("json_compression", 0) + 1
                    )
                    return compressed_value
                return json_str
            except Exception:
                # Fallback to string representation
                str_value = str(value)
                if len(str_value) > 256:
                    return self._compress_string(str_value)
                return str_value

        # Convert other types to string
        str_value = str(value)
        if len(str_value) > 256:
            return self._compress_string(str_value)
        return str_value

    def _compress_string(self, value: str) -> str:
        """Compress long string values to reduce storage."""
        # Simple compression: use hash for very long strings
        if len(value) > 1000:
            return f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"

        # Truncate moderately long strings
        return value[:256] + "..." if len(value) > 256 else value

    def get_field_statistics(self) -> dict[str, Any]:
        """Get statistics about field optimization."""
        return {
            "total_fields": len(self.field_type_mappings),
            "field_types": self.field_type_mappings,
            "compression_stats": self.field_compression_stats,
        }


class SchemaOptimizer:
    """Main schema optimizer that coordinates tag and field optimization."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize schema optimizer with configuration."""
        self.config = config or {}
        self.tag_manager = OptimizedTagManager(
            max_tag_cardinality=self.config.get("max_tag_cardinality", 10000)
        )
        self.field_manager = OptimizedFieldManager()
        self.optimization_stats: dict[str, Any] = {}

    def optimize_point(
        self, point: "OptimizedInfluxDBPoint"
    ) -> "OptimizedInfluxDBPoint":
        """Optimize a complete InfluxDB point."""
        # Optimize tags
        optimized_tags = self.tag_manager.optimize_tags(point.tags)

        # Optimize fields
        optimized_fields = self.field_manager.optimize_fields(point.fields)

        # Create optimized point
        optimized_point = OptimizedInfluxDBPoint(
            measurement=point.measurement,
            timestamp=point.timestamp,
            tags=optimized_tags,
            fields=optimized_fields,
            metadata={
                "original_tags_count": len(point.tags),
                "original_fields_count": len(point.fields),
                "optimized_tags_count": len(optimized_tags),
                "optimized_fields_count": len(optimized_fields),
                "optimization_score": point.get_optimization_score(),
                "optimization_timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Update optimization statistics
        self._update_optimization_stats(point, optimized_point)

        return optimized_point

    def _update_optimization_stats(
        self, original: "OptimizedInfluxDBPoint", optimized: "OptimizedInfluxDBPoint"
    ) -> None:
        """Update optimization statistics."""
        if "total_points_processed" not in self.optimization_stats:
            self.optimization_stats["total_points_processed"] = 0
            self.optimization_stats["total_storage_saved"] = 0
            self.optimization_stats["average_optimization_score"] = 0.0

        self.optimization_stats["total_points_processed"] += 1

        # Calculate storage savings
        original_size = original.get_size_estimate()
        optimized_size = optimized.get_size_estimate()
        storage_saved = max(0, original_size - optimized_size)
        self.optimization_stats["total_storage_saved"] += storage_saved

        # Update average optimization score
        current_avg = self.optimization_stats["average_optimization_score"]
        total_points = self.optimization_stats["total_points_processed"]
        new_score = optimized.get_optimization_score()
        self.optimization_stats["average_optimization_score"] = (
            current_avg * (total_points - 1) + new_score
        ) / total_points

    def get_optimization_report(self) -> dict[str, Any]:
        """Get comprehensive optimization report."""
        return {
            "optimization_stats": self.optimization_stats,
            "tag_statistics": self.tag_manager.get_tag_statistics(),
            "field_statistics": self.field_manager.get_field_statistics(),
            "configuration": self.config,
        }

    def reset_statistics(self) -> None:
        """Reset all optimization statistics."""
        self.optimization_stats = {
            "total_points_processed": 0,
            "total_storage_saved": 0,
            "average_optimization_score": 0.0,
        }
        self.tag_manager = OptimizedTagManager(
            max_tag_cardinality=self.config.get("max_tag_cardinality", 10000)
        )
        self.field_manager = OptimizedFieldManager()
