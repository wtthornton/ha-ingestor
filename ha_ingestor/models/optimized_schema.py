"""Optimized InfluxDB schema models for Home Assistant data storage.

This module implements the new optimized schema design that addresses
cardinality issues, improves query performance, and reduces storage overhead.
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class SchemaOptimizationMetrics(BaseModel):
    """Metrics for tracking schema optimization performance."""

    optimization_count: int = 0
    total_storage_saved_bytes: int = 0
    average_optimization_time_ms: float = 0.0
    cardinality_reduction_percent: float = 0.0
    compression_ratio: float = 0.0
    last_optimization: Optional[datetime] = None
    optimization_history: List[Dict[str, Any]] = Field(default_factory=list)


class AdvancedTagManager:
    """Advanced tag manager with intelligent cardinality management."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize advanced tag manager."""
        self.config = config
        self.max_cardinality = config.get("max_tag_cardinality", 10000)
        self.compression_threshold = config.get("tag_compression_threshold", 1000)
        self.tag_patterns: Dict[str, Dict[str, int]] = {}
        self.cardinality_tracker: Dict[str, int] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        
    def analyze_tag_patterns(self, tags: Dict[str, str]) -> Dict[str, Any]:
        """Analyze tag patterns for optimization opportunities."""
        analysis = {
            "high_cardinality_tags": [],
            "long_value_tags": [],
            "pattern_suggestions": [],
            "optimization_potential": 0.0
        }
        
        for key, value in tags.items():
            # Check cardinality
            if key not in self.cardinality_tracker:
                self.cardinality_tracker[key] = 1
            else:
                self.cardinality_tracker[key] += 1
                
            if self.cardinality_tracker[key] > self.max_cardinality * 0.8:
                analysis["high_cardinality_tags"].append({
                    "tag": key,
                    "cardinality": self.cardinality_tracker[key],
                    "suggestion": "Consider hashing or grouping"
                })
            
            # Check value length
            if len(value) > self.compression_threshold:
                analysis["long_value_tags"].append({
                    "tag": key,
                    "length": len(value),
                    "suggestion": "Apply compression or truncation"
                })
        
        # Calculate optimization potential
        total_issues = len(analysis["high_cardinality_tags"]) + len(analysis["long_value_tags"])
        analysis["optimization_potential"] = min(1.0, total_issues / len(tags)) if tags else 0.0
        
        return analysis

    def optimize_tags_advanced(self, tags: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Advanced tag optimization with pattern recognition."""
        start_time = time.time()
        original_tags = tags.copy()
        optimized_tags = {}
        optimization_stats = {
            "original_count": len(tags),
            "optimized_count": 0,
            "compression_applied": 0,
            "hashing_applied": 0,
            "grouping_applied": 0,
            "time_ms": 0.0
        }
        
        for key, value in tags.items():
            optimized_key = key
            optimized_value = value
            
            # Apply intelligent compression based on value characteristics
            if len(value) > self.compression_threshold:
                if self._is_structured_data(value):
                    # For structured data, try to extract key information
                    optimized_value = self._extract_key_info(value)
                    optimization_stats["compression_applied"] += 1
                else:
                    # For unstructured data, apply hashing
                    optimized_value = f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"
                    optimization_stats["hashing_applied"] += 1
            
            # Apply cardinality management
            if self.cardinality_tracker.get(key, 0) > self.max_cardinality:
                optimized_key = f"{key}_grouped"
                optimized_value = self._group_similar_values(key, value)
                optimization_stats["grouping_applied"] += 1
            
            optimized_tags[optimized_key] = optimized_value
            optimization_stats["optimized_count"] += 1
        
        optimization_stats["time_ms"] = (time.time() - start_time) * 1000
        
        # Record optimization
        self.optimization_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "stats": optimization_stats,
            "original_tags": original_tags,
            "optimized_tags": optimized_tags
        })
        
        return optimized_tags, optimization_stats
    
    def _is_structured_data(self, value: str) -> bool:
        """Check if value appears to be structured data."""
        try:
            json.loads(value)
            return True
        except (json.JSONDecodeError, ValueError):
            # Check for common structured patterns
            structured_patterns = [
                r'^\d{4}-\d{2}-\d{2}',  # ISO date
                r'^\d+\.\d+\.\d+',      # Version numbers
                r'^[A-Z]{2,}_\w+',      # Prefix patterns
            ]
            import re
            return any(re.match(pattern, value) for pattern in structured_patterns)
    
    def _extract_key_info(self, value: str) -> str:
        """Extract key information from structured data."""
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                # Extract first few key-value pairs
                key_info = []
                for k, v in list(data.items())[:3]:
                    key_info.append(f"{k}:{str(v)[:20]}")
                return "|".join(key_info)
            else:
                return str(data)[:50]
        except (json.JSONDecodeError, ValueError):
            # Fallback to smart truncation
            return value[:50] + "..." if len(value) > 50 else value
    
    def _group_similar_values(self, key: str, value: str) -> str:
        """Group similar values to reduce cardinality."""
        # Simple grouping based on value characteristics
        if value.isdigit():
            # Group numeric values by ranges
            num_value = int(value)
            if num_value < 100:
                return "low"
            elif num_value < 1000:
                return "medium"
            else:
                return "high"
        elif len(value) < 10:
            return "short"
        elif len(value) < 50:
            return "medium"
        else:
            return "long"
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive tag optimization report."""
        return {
            "cardinality_tracker": self.cardinality_tracker,
            "optimization_history": self.optimization_history[-10:],  # Last 10 optimizations
            "total_optimizations": len(self.optimization_history),
            "current_cardinality": sum(self.cardinality_tracker.values()),
            "max_cardinality": self.max_cardinality
        }


class AdvancedFieldManager:
    """Advanced field manager with intelligent type optimization and compression."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize advanced field manager."""
        self.config = config
        self.compression_threshold = config.get("field_compression_threshold", 256)
        self.type_optimization_enabled = config.get("type_optimization", True)
        self.field_type_mappings: Dict[str, str] = {}
        self.compression_stats: Dict[str, int] = {
            "compressed_fields": 0,
            "type_converted_fields": 0,
            "total_optimizations": 0
        }
        self.optimization_history: List[Dict[str, Any]] = []
    
    def optimize_fields_advanced(self, fields: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Advanced field optimization with intelligent type conversion and compression."""
        start_time = time.time()
        original_fields = fields.copy()
        optimized_fields = {}
        optimization_stats = {
            "original_count": len(fields),
            "optimized_count": 0,
            "compression_applied": 0,
            "type_conversion_applied": 0,
            "time_ms": 0.0
        }
        
        for key, value in fields.items():
            optimized_key = key
            optimized_value = value
            
            # Type optimization
            if self.type_optimization_enabled:
                optimized_value = self._optimize_field_type(key, value)
                if optimized_value != value:
                    optimization_stats["type_conversion_applied"] += 1
            
            # Compression optimization
            if isinstance(optimized_value, str) and len(optimized_value) > self.compression_threshold:
                optimized_value = self._compress_field_value(optimized_value)
                optimization_stats["compression_applied"] += 1
            
            # Key optimization
            if len(key) > 64:  # InfluxDB key length limit
                optimized_key = self._optimize_field_key(key)
            
            optimized_fields[optimized_key] = optimized_value
            optimization_stats["optimized_count"] += 1
        
        optimization_stats["time_ms"] = (time.time() - start_time) * 1000
        
        # Record optimization
        self.optimization_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "stats": optimization_stats,
            "original_fields": original_fields,
            "optimized_fields": optimized_fields
        })
        
        return optimized_fields, optimization_stats
    
    def _optimize_field_type(self, key: str, value: Any) -> Any:
        """Optimize field type for better storage and query performance."""
        if isinstance(value, str):
            # Try to convert string to more efficient types
            if value.lower() in ("true", "false"):
                return value.lower() == "true"
            elif value.isdigit():
                return int(value)
            elif value.replace(".", "").replace("-", "").isdigit():
                try:
                    return float(value)
                except ValueError:
                    pass
        
        elif isinstance(value, (list, tuple)) and len(value) == 0:
            # Empty collections can be optimized
            return None
        
        return value
    
    def _compress_field_value(self, value: str) -> str:
        """Intelligently compress field values."""
        if len(value) > 1000:
            # Very long values get hashed
            return f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"
        elif len(value) > self.compression_threshold:
            # Long values get truncated with context
            return value[:self.compression_threshold//2] + "..." + value[-self.compression_threshold//4:]
        else:
            return value
    
    def _optimize_field_key(self, key: str) -> str:
        """Optimize field key to meet InfluxDB requirements."""
        # Remove invalid characters and truncate
        clean_key = "".join(c for c in key if c.isalnum() or c in "_-")
        if len(clean_key) > 64:
            # Use hash for very long keys
            return f"key_{hashlib.md5(key.encode()).hexdigest()[:16]}"
        return clean_key
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive field optimization report."""
        return {
            "compression_stats": self.compression_stats,
            "type_mappings": self.field_type_mappings,
            "optimization_history": self.optimization_history[-10:],
            "total_optimizations": len(self.optimization_history)
        }


class SchemaEvolutionManager:
    """Manages automatic schema evolution and optimization."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize schema evolution manager."""
        self.config = config
        self.evolution_enabled = config.get("auto_schema_evolution", True)
        self.analysis_interval = config.get("schema_analysis_interval", 300.0)
        self.last_analysis = None
        self.evolution_history: List[Dict[str, Any]] = []
        self.schema_patterns: Dict[str, Dict[str, Any]] = {}
    
    def should_analyze_schema(self) -> bool:
        """Check if it's time to analyze the schema."""
        if not self.evolution_enabled:
            return False
        
        if self.last_analysis is None:
            return True
        
        time_since_analysis = (datetime.utcnow() - self.last_analysis).total_seconds()
        return time_since_analysis >= self.analysis_interval
    
    def analyze_schema_patterns(self, points: List["OptimizedInfluxDBPoint"]) -> Dict[str, Any]:
        """Analyze schema patterns for evolution opportunities."""
        if not self.should_analyze_schema():
            return {"status": "skipped", "reason": "analysis_interval_not_reached"}
        
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "points_analyzed": len(points),
            "measurement_patterns": {},
            "tag_patterns": {},
            "field_patterns": {},
            "optimization_suggestions": [],
            "evolution_recommendations": []
        }
        
        # Analyze measurement patterns
        measurement_counts = {}
        for point in points:
            measurement_counts[point.measurement] = measurement_counts.get(point.measurement, 0) + 1
        
        analysis["measurement_patterns"] = measurement_counts
        
        # Analyze tag patterns
        tag_analysis = self._analyze_tag_patterns(points)
        analysis["tag_patterns"] = tag_analysis
        
        # Analyze field patterns
        field_analysis = self._analyze_field_patterns(points)
        analysis["field_patterns"] = field_analysis
        
        # Generate optimization suggestions
        analysis["optimization_suggestions"] = self._generate_optimization_suggestions(analysis)
        
        # Generate evolution recommendations
        analysis["evolution_recommendations"] = self._generate_evolution_recommendations(analysis)
        
        # Update analysis timestamp
        self.last_analysis = datetime.utcnow()
        
        # Record analysis
        self.evolution_history.append(analysis)
        
        return analysis
    
    def _analyze_tag_patterns(self, points: List["OptimizedInfluxDBPoint"]) -> Dict[str, Any]:
        """Analyze tag patterns across points."""
        tag_analysis = {}
        
        for point in points:
            for key, value in point.tags.items():
                if key not in tag_analysis:
                    tag_analysis[key] = {
                        "count": 0,
                        "unique_values": set(),
                        "value_lengths": [],
                        "cardinality": 0
                    }
                
                tag_analysis[key]["count"] += 1
                tag_analysis[key]["unique_values"].add(value)
                tag_analysis[key]["value_lengths"].append(len(value))
        
        # Convert sets to counts for JSON serialization
        for key in tag_analysis:
            tag_analysis[key]["cardinality"] = len(tag_analysis[key]["unique_values"])
            tag_analysis[key]["unique_values"] = len(tag_analysis[key]["unique_values"])
            tag_analysis[key]["avg_value_length"] = sum(tag_analysis[key]["value_lengths"]) / len(tag_analysis[key]["value_lengths"])
            del tag_analysis[key]["value_lengths"]
        
        return tag_analysis
    
    def _analyze_field_patterns(self, points: List["OptimizedInfluxDBPoint"]) -> Dict[str, Any]:
        """Analyze field patterns across points."""
        field_analysis = {}
        
        for point in points:
            for key, value in point.fields.items():
                if key not in field_analysis:
                    field_analysis[key] = {
                        "count": 0,
                        "types": {},
                        "value_lengths": [],
                        "null_count": 0
                    }
                
                field_analysis[key]["count"] += 1
                
                # Track types
                value_type = type(value).__name__
                field_analysis[key]["types"][value_type] = field_analysis[key]["types"].get(value_type, 0) + 1
                
                # Track value lengths for strings
                if isinstance(value, str):
                    field_analysis[key]["value_lengths"].append(len(value))
                elif value is None:
                    field_analysis[key]["null_count"] += 1
        
        # Calculate averages for JSON serialization
        for key in field_analysis:
            if field_analysis[key]["value_lengths"]:
                field_analysis[key]["avg_value_length"] = sum(field_analysis[key]["value_lengths"]) / len(field_analysis[key]["value_lengths"])
                field_analysis[key]["max_value_length"] = max(field_analysis[key]["value_lengths"])
                del field_analysis[key]["value_lengths"]
            else:
                field_analysis[key]["avg_value_length"] = 0
                field_analysis[key]["max_value_length"] = 0
        
        return field_analysis
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on analysis."""
        suggestions = []
        
        # Tag optimization suggestions
        for tag, stats in analysis["tag_patterns"].items():
            if stats["cardinality"] > 10000:
                suggestions.append(f"High cardinality tag '{tag}' ({stats['cardinality']}): Consider hashing or grouping")
            if stats["avg_value_length"] > 100:
                suggestions.append(f"Long tag values for '{tag}' (avg: {stats['avg_value_length']:.1f}): Consider compression")
        
        # Field optimization suggestions
        for field, stats in analysis["field_patterns"].items():
            if stats["null_count"] > stats["count"] * 0.5:
                suggestions.append(f"High null rate for field '{field}' ({stats['null_count']}/{stats['count']}): Consider sparse field optimization")
            if stats["avg_value_length"] > 256:
                suggestions.append(f"Long field values for '{field}' (avg: {stats['avg_value_length']:.1f}): Consider compression or truncation")
        
        return suggestions
    
    def _generate_evolution_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate schema evolution recommendations."""
        recommendations = []
        
        # Measurement consolidation recommendations
        if len(analysis["measurement_patterns"]) > 20:
            recommendations.append("High measurement count: Consider consolidating related measurements")
        
        # Tag optimization recommendations
        high_cardinality_tags = [tag for tag, stats in analysis["tag_patterns"].items() if stats["cardinality"] > 5000]
        if high_cardinality_tags:
            recommendations.append(f"High cardinality tags detected: {', '.join(high_cardinality_tags[:5])}")
        
        # Field optimization recommendations
        long_field_tags = [field for field, stats in analysis["field_patterns"].items() if stats["avg_value_length"] > 200]
        if long_field_tags:
            recommendations.append(f"Long field values detected: {', '.join(long_field_tags[:5])}")
        
        return recommendations
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Get comprehensive schema evolution report."""
        return {
            "evolution_enabled": self.evolution_enabled,
            "analysis_interval": self.analysis_interval,
            "last_analysis": self.last_analysis.isoformat() if self.last_analysis else None,
            "evolution_history": self.evolution_history[-5:],  # Last 5 analyses
            "total_analyses": len(self.evolution_history),
            "schema_patterns": self.schema_patterns
        }


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

        validated_fields: dict[str, Any] = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Field keys must be strings")

            # InfluxDB field key limits
            if len(key) > 64:
                raise ValueError(f"Field key '{key}' exceeds 64 character limit")

            # InfluxDB field key character restrictions
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

    def get_size_estimate(self) -> int:
        """Estimate the size of this point in bytes."""
        size = 0
        
        # Measurement size
        size += len(self.measurement.encode("utf-8"))
        
        # Tags size
        for key, value in self.tags.items():
            size += len(key.encode("utf-8")) + len(value.encode("utf-8"))
        
        # Fields size
        for key, value in self.fields.items():
            size += len(key.encode("utf-8"))
            if isinstance(value, str):
                size += len(value.encode("utf-8"))
            else:
                size += len(str(value).encode("utf-8"))
        
        # Metadata size
        for key, value in self.metadata.items():
            size += len(key.encode("utf-8"))
            if isinstance(value, str):
                size += len(value.encode("utf-8"))
            else:
                size += len(str(value).encode("utf-8"))
        
        return size

    def get_optimization_score(self) -> float:
        """Calculate optimization score (0.0 to 1.0)."""
        # Base score starts at 1.0
        score = 1.0
        
        # Penalize long tag values
        for value in self.tags.values():
            if len(value) > 64:
                score -= 0.1
            elif len(value) > 32:
                score -= 0.05
        
        # Penalize long field values
        for value in self.fields.values():
            if isinstance(value, str) and len(value) > 256:
                score -= 0.1
            elif isinstance(value, str) and len(value) > 128:
                score -= 0.05
        
        # Penalize excessive metadata
        if len(self.metadata) > 10:
            score -= 0.1
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))

    def to_influxdb_line_protocol(self) -> str:
        """Convert to InfluxDB line protocol format."""
        # Build measurement
        line = self.measurement
        
        # Add tags
        if self.tags:
            tag_pairs = []
            for key, value in sorted(self.tags.items()):
                # Escape special characters in tag keys and values
                escaped_key = key.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
                escaped_value = value.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
                tag_pairs.append(f"{escaped_key}={escaped_value}")
            line += "," + ",".join(tag_pairs)
        
        # Add fields
        field_pairs = []
        for key, value in sorted(self.fields.items()):
            escaped_key = key.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
            
            if isinstance(value, str):
                # Escape quotes and backslashes in string values
                escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
                field_pairs.append(f'{escaped_key}="{escaped_value}"')
            elif isinstance(value, bool):
                field_pairs.append(f"{escaped_key}={str(value).lower()}")
            else:
                field_pairs.append(f"{escaped_key}={value}")
        
        line += " " + ",".join(field_pairs)
        
        # Add timestamp
        timestamp_ns = int(self.timestamp.timestamp() * 1e9)
        line += f" {timestamp_ns}"
        
        return line


class OptimizedTagManager:
    """Tag manager with cardinality control and optimization."""

    def __init__(self, max_tag_cardinality: int = 10000):
        """Initialize tag manager."""
        self.max_tag_cardinality = max_tag_cardinality
        self.tag_cardinality: dict[str, int] = {}
        self.tag_patterns: dict[str, dict[str, int]] = {}
        self.optimization_stats: dict[str, int] = {
            "tags_compressed": 0,
            "tags_hashed": 0,
            "tags_grouped": 0,
        }

    def optimize_tags(self, tags: dict[str, str]) -> dict[str, str]:
        """Optimize tags to reduce cardinality and improve performance."""
        optimized_tags = {}
        
        for key, value in tags.items():
            # Check cardinality
            if key not in self.tag_cardinality:
                self.tag_cardinality[key] = 1
            else:
                self.tag_cardinality[key] += 1
            
            # Apply optimization if cardinality is too high
            if self.tag_cardinality[key] > self.max_tag_cardinality:
                optimized_value = self._optimize_high_cardinality_tag(key, value)
                self.optimization_stats["tags_grouped"] += 1
            elif len(value) > 1000:
                optimized_value = self._compress_string(value)
                self.optimization_stats["tags_compressed"] += 1
            else:
                optimized_value = value
            
            optimized_tags[key] = optimized_value
        
        return optimized_tags

    def _optimize_high_cardinality_tag(self, key: str, value: str) -> str:
        """Optimize high cardinality tags by grouping similar values."""
        # Simple grouping strategy
        if value.isdigit():
            num_value = int(value)
            if num_value < 100:
                return "low"
            elif num_value < 1000:
                return "medium"
            else:
                return "high"
        elif len(value) < 10:
            return "short"
        elif len(value) < 50:
            return "medium"
        else:
            return "long"

    def _compress_string(self, value: str) -> str:
        """Compress long string values to reduce storage."""
        # Simple compression: use hash for very long strings
        if len(value) > 1000:
            return f"hash_{hashlib.md5(value.encode()).hexdigest()[:16]}"

        # Truncate moderately long strings
        return value[:256] + "..." if len(value) > 256 else value

    def get_tag_statistics(self) -> dict[str, Any]:
        """Get statistics about tag optimization."""
        return {
            "total_tags": len(self.tag_cardinality),
            "tag_cardinality": self.tag_cardinality,
            "optimization_stats": self.optimization_stats,
        }


class OptimizedFieldManager:
    """Field manager with type optimization and compression."""

    def __init__(self):
        """Initialize field manager."""
        self.field_type_mappings: dict[str, str] = {}
        self.field_compression_stats: dict[str, int] = {
            "fields_compressed": 0,
            "fields_truncated": 0,
        }

    def optimize_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        """Optimize fields for better storage and query performance."""
        optimized_fields = {}
        
        for key, value in fields.items():
            # Track field types
            self.field_type_mappings[key] = type(value).__name__
            
            # Apply compression for long string values
            if isinstance(value, str) and len(value) > 256:
                optimized_value = self._compress_string(value)
                self.field_compression_stats["fields_compressed"] += 1
            else:
                optimized_value = value
            
            optimized_fields[key] = optimized_value
        
        return optimized_fields

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
        self.tag_manager = AdvancedTagManager(self.config)
        self.field_manager = AdvancedFieldManager(self.config)
        self.evolution_manager = SchemaEvolutionManager(self.config)
        self.optimization_stats: dict[str, Any] = {}
        self.optimization_metrics = SchemaOptimizationMetrics()
        
        # Performance tracking
        self.optimization_times: List[float] = []
        self.total_points_processed = 0
        self.total_storage_saved = 0

    def optimize_point(
        self, point: "OptimizedInfluxDBPoint"
    ) -> "OptimizedInfluxDBPoint":
        """Optimize a complete InfluxDB point with advanced features."""
        start_time = time.time()
        
        # Optimize tags with advanced manager
        optimized_tags, tag_stats = self.tag_manager.optimize_tags_advanced(point.tags)

        # Optimize fields with advanced manager
        optimized_fields, field_stats = self.field_manager.optimize_fields_advanced(point.fields)

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
                "tag_optimization_stats": tag_stats,
                "field_optimization_stats": field_stats,
            },
        )

        # Update optimization statistics
        self._update_optimization_stats(point, optimized_point, time.time() - start_time)

        return optimized_point

    def _update_optimization_stats(
        self, original: "OptimizedInfluxDBPoint", optimized: "OptimizedInfluxDBPoint", optimization_time: float
    ) -> None:
        """Update optimization statistics with performance tracking."""
        self.total_points_processed += 1
        self.optimization_times.append(optimization_time)
        
        # Calculate storage savings
        original_size = original.get_size_estimate()
        optimized_size = optimized.get_size_estimate()
        storage_saved = max(0, original_size - optimized_size)
        self.total_storage_saved += storage_saved
        
        # Update metrics
        self.optimization_metrics.optimization_count += 1
        self.optimization_metrics.total_storage_saved_bytes += storage_saved
        self.optimization_metrics.last_optimization = datetime.utcnow()
        
        # Calculate average optimization time
        if self.optimization_times:
            self.optimization_metrics.average_optimization_time_ms = (
                sum(self.optimization_times) * 1000 / len(self.optimization_times)
            )
        
        # Calculate compression ratio
        if original_size > 0:
            self.optimization_metrics.compression_ratio = 1.0 - (optimized_size / original_size)

    def analyze_schema_evolution(self, points: List["OptimizedInfluxDBPoint"]) -> Dict[str, Any]:
        """Analyze schema for evolution opportunities."""
        return self.evolution_manager.analyze_schema_patterns(points)

    def get_optimization_report(self) -> dict[str, Any]:
        """Get comprehensive optimization report with advanced metrics."""
        return {
            "optimization_stats": self.optimization_stats,
            "optimization_metrics": self.optimization_metrics.dict(),
            "tag_statistics": self.tag_manager.get_optimization_report(),
            "field_statistics": self.field_manager.get_optimization_report(),
            "evolution_report": self.evolution_manager.get_evolution_report(),
            "performance_metrics": {
                "total_points_processed": self.total_points_processed,
                "total_storage_saved_bytes": self.total_storage_saved,
                "average_optimization_time_ms": self.optimization_metrics.average_optimization_time_ms,
                "compression_ratio": self.optimization_metrics.compression_ratio,
                "optimization_times": self.optimization_times[-100:] if self.optimization_times else []
            },
            "configuration": self.config,
        }

    def reset_statistics(self) -> None:
        """Reset all optimization statistics."""
        self.optimization_stats = {
            "total_points_processed": 0,
            "total_storage_saved": 0,
            "average_optimization_score": 0.0,
        }
        self.optimization_metrics = SchemaOptimizationMetrics()
        self.optimization_times = []
        self.total_points_processed = 0
        self.total_storage_saved = 0
        
        # Reset component managers
        self.tag_manager = AdvancedTagManager(self.config)
        self.field_manager = AdvancedFieldManager(self.config)
        self.evolution_manager = SchemaEvolutionManager(self.config)
