"""Advanced MQTT topic pattern matching and processing system."""

import re
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from re import Pattern
from typing import Any

from ..utils.logging import get_logger


@dataclass
class TopicPattern:
    """Represents a configurable MQTT topic pattern with matching rules."""

    pattern: str
    description: str = ""
    priority: int = 0
    enabled: bool = True
    regex_pattern: Pattern[str] | None = None
    filters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compile regex pattern if not already compiled."""
        if self.regex_pattern is None:
            self.regex_pattern = self._compile_pattern()

    def _compile_pattern(self) -> Pattern[str]:
        """Compile the topic pattern into a regex pattern."""
        # Validate MQTT pattern format first
        if not self._validate_mqtt_pattern(self.pattern):
            raise ValueError(
                f"Invalid topic pattern '{self.pattern}': Invalid MQTT wildcard usage"
            )

        # Convert MQTT wildcards to regex patterns
        # + matches single level, # matches multiple levels
        regex_str = self.pattern

        # Handle + wildcard (single level)
        regex_str = regex_str.replace("+", "[^/]+")

        # Handle # wildcard (multi-level) - must be at the end
        if regex_str.endswith("#"):
            regex_str = regex_str[:-1] + ".*"

        # Escape regex special characters that might be in the pattern
        # but preserve our wildcard replacements
        escaped = re.escape(regex_str)

        # Restore our wildcard replacements after escaping
        # re.escape produces \[\^/\]\+ for [^/]+ and \.\* for .*
        regex_str = escaped.replace(r"\[\^/\]\+", "[^/]+")
        regex_str = regex_str.replace(r"\.\*", ".*")

        # Anchor to start and end
        regex_str = f"^{regex_str}$"

        try:
            return re.compile(regex_str, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid topic pattern '{self.pattern}': {e}")

    def _validate_mqtt_pattern(self, pattern: str) -> bool:
        """Validate MQTT topic pattern format.

        Args:
            pattern: The pattern to validate

        Returns:
            True if pattern is valid, False otherwise
        """
        if not pattern:
            return True  # Allow empty patterns to be created, but reject them when adding to manager

        # Check for invalid characters in MQTT patterns
        # MQTT allows + and # as wildcards, but not other regex special characters
        invalid_chars = ["[", "]", "{", "}", "(", ")", "\\", "^", "$", "|", "?", "*"]
        for char in invalid_chars:
            if char in pattern and not pattern.startswith("\\"):
                return False

        # Check for proper wildcard usage
        parts = pattern.split("/")
        for i, part in enumerate(parts):
            if part == "#" and i != len(parts) - 1:
                # # can only be at the end
                return False
            if part == "+" and len(part) > 1:
                # + must be alone in its level (but can be combined with other valid chars)
                # This is actually valid MQTT, so we'll allow it
                pass

        return True

    def matches(self, topic: str) -> bool:
        """Check if a topic matches this pattern."""
        if not self.enabled:
            return False

        if not self.regex_pattern:
            return False

        return bool(self.regex_pattern.match(topic))

    def extract_groups(self, topic: str) -> dict[str, str]:
        """Extract named groups from a topic based on the pattern."""
        if not self.matches(topic):
            return {}

        # Simple group extraction for common patterns
        groups: dict[str, str] = {}

        # Extract domain, entity type, and entity name from common HA patterns
        if "homeassistant" in self.pattern:
            parts = topic.split("/")
            if len(parts) >= 4:
                groups["domain"] = parts[1] if parts[1] != "+" else parts[1]
                groups["entity_type"] = parts[2] if parts[2] != "+" else parts[2]
                groups["entity_name"] = parts[3] if parts[3] != "+" else parts[3]
                if len(parts) > 4:
                    groups["attribute"] = parts[4] if parts[4] != "+" else parts[4]

        return groups


@dataclass
class TopicSubscription:
    """Represents an active topic subscription with metadata."""

    topic: str
    qos: int = 1
    callback: Callable[[str, str, Any], None] | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: __import__("time").time())
    message_count: int = 0
    last_message_time: float | None = None


class TopicPatternManager:
    """Manages MQTT topic patterns, subscriptions, and routing."""

    def __init__(self) -> None:
        """Initialize the topic pattern manager."""
        self.logger = get_logger(__name__)

        # Pattern storage
        self.patterns: list[TopicPattern] = []
        self.pattern_index: dict[str, TopicPattern] = {}

        # Active subscriptions
        self.subscriptions: dict[str, TopicSubscription] = {}
        self.subscription_patterns: dict[str, list[str]] = defaultdict(list)

        # Topic hierarchy cache for optimization
        self.topic_hierarchy: dict[str, set[str]] = defaultdict(set)
        self.hierarchy_cache: dict[str, list[str]] = {}

        # Performance optimization caches
        self._pattern_match_cache: dict[str, list[TopicPattern]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._cache_size_limit: int = 1000

        # Performance metrics
        self.metrics = {
            "pattern_matches": 0,
            "subscription_creates": 0,
            "subscription_removes": 0,
            "topic_routes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "pattern_compilation_time": 0.0,
            "matching_time": 0.0,
            "routing_time": 0.0,
        }

        # Performance monitoring
        self._performance_history: list[dict[str, Any]] = []
        self._max_history_size: int = 100

    def add_pattern(self, pattern: TopicPattern) -> bool:
        """Add a new topic pattern to the manager.

        Args:
            pattern: The topic pattern to add

        Returns:
            True if pattern was added successfully, False otherwise
        """
        try:
            # Validate pattern
            if not pattern.pattern:
                raise ValueError("Pattern cannot be empty")

            # Check for duplicates
            if pattern.pattern in self.pattern_index:
                self.logger.warning("Pattern already exists", pattern=pattern.pattern)
                return False

            # Add pattern
            self.patterns.append(pattern)
            self.pattern_index[pattern.pattern] = pattern

            # Sort patterns by priority (higher priority first)
            self.patterns.sort(key=lambda p: p.priority, reverse=True)

            # Update hierarchy cache
            self._update_hierarchy_cache(pattern.pattern)

            # Clear pattern match cache when patterns change
            self._clear_pattern_cache()

            self.logger.info(
                "Added topic pattern",
                pattern=pattern.pattern,
                priority=pattern.priority,
            )
            return True

        except Exception as e:
            self.logger.error(
                "Failed to add pattern", pattern=pattern.pattern, error=str(e)
            )
            return False

    def remove_pattern(self, pattern_str: str) -> bool:
        """Remove a topic pattern from the manager.

        Args:
            pattern_str: The pattern string to remove

        Returns:
            True if pattern was removed successfully, False otherwise
        """
        try:
            if pattern_str not in self.pattern_index:
                self.logger.warning("Pattern not found", pattern=pattern_str)
                return False

            # Remove pattern
            pattern = None
            for p in self.patterns:
                if p.pattern == pattern_str:
                    pattern = p
                    break

            if pattern:
                self.patterns.remove(pattern)
                del self.pattern_index[pattern_str]

                # Update hierarchy cache
                self._update_hierarchy_cache(pattern_str, remove=True)

                # Clear pattern match cache when patterns change
                self._clear_pattern_cache()

                self.logger.info("Removed topic pattern", pattern=pattern_str)
                return True

            return False

        except Exception as e:
            self.logger.error(
                "Failed to remove pattern", pattern=pattern_str, error=str(e)
            )
            return False

    def find_matching_patterns(self, topic: str) -> list[TopicPattern]:
        """Find all patterns that match a given topic.

        Args:
            topic: The topic to match against

        Returns:
            List of matching patterns, sorted by priority
        """
        start_time = time.time()

        # Debug logging
        self.logger.debug(f"Finding patterns for topic: {topic}")
        self.logger.debug(f"Available patterns: {[p.pattern for p in self.patterns]}")

        # Check cache first
        if topic in self._pattern_match_cache:
            self._cache_hits += 1
            self.metrics["cache_hits"] += 1
            matching_patterns = self._pattern_match_cache[topic]
            self.logger.debug(
                f"Cache hit for topic {topic}: {len(matching_patterns)} patterns"
            )
        else:
            self._cache_misses += 1
            self.metrics["cache_misses"] += 1

            # Find matching patterns
            matching_patterns = []
            for pattern in self.patterns:
                self.logger.debug(
                    f"Testing pattern '{pattern.pattern}' against topic '{topic}'"
                )
                if pattern.matches(topic):
                    matching_patterns.append(pattern)
                    self.metrics["pattern_matches"] += 1
                    self.logger.debug(
                        f"Pattern '{pattern.pattern}' matches topic '{topic}'"
                    )
                else:
                    self.logger.debug(
                        f"Pattern '{pattern.pattern}' does not match topic '{topic}'"
                    )

            # Cache the result
            self._cache_pattern_match(topic, matching_patterns)
            self.logger.debug(
                f"Cache miss for topic {topic}: found {len(matching_patterns)} patterns"
            )

        # Update performance metrics
        matching_time = time.time() - start_time
        self.metrics["matching_time"] += matching_time

        # Return patterns sorted by priority (highest first)
        return sorted(matching_patterns, key=lambda p: p.priority, reverse=True)

    def subscribe_to_pattern(
        self,
        pattern: str,
        callback: Callable | None = None,
        qos: int = 1,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """Subscribe to a topic pattern with optional callback and filters.

        Args:
            pattern: The topic pattern to subscribe to
            callback: Optional callback function for messages
            qos: Quality of service level
            filters: Optional message filters

        Returns:
            Subscription ID for management
        """
        try:
            # Create topic pattern if it doesn't exist
            if pattern not in self.pattern_index:
                topic_pattern = TopicPattern(
                    pattern=pattern,
                    description=f"Dynamic subscription to {pattern}",
                    priority=1,
                    enabled=True,
                    filters=filters or {},
                )
                self.add_pattern(topic_pattern)

            # Create subscription
            subscription_id = f"sub_{len(self.subscriptions)}_{int(time.time())}"

            subscription = TopicSubscription(
                topic=pattern, qos=qos, callback=callback, filters=filters or {}
            )

            self.subscriptions[subscription_id] = subscription

            # Initialize subscription pattern list if needed
            if pattern not in self.subscription_patterns:
                self.subscription_patterns[pattern] = []
            self.subscription_patterns[pattern].append(subscription_id)

            # Update hierarchy cache
            self._update_hierarchy_cache(pattern)

            self.metrics["subscription_creates"] += 1

            self.logger.info(
                "Created topic subscription",
                subscription_id=subscription_id,
                pattern=pattern,
                qos=qos,
            )

            return subscription_id

        except Exception as e:
            self.logger.error(
                "Failed to create subscription", pattern=pattern, error=str(e)
            )
            raise

    def unsubscribe_from_pattern(self, subscription_id: str) -> bool:
        """Unsubscribe from a topic pattern.

        Args:
            subscription_id: The subscription ID to remove

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            if subscription_id not in self.subscriptions:
                self.logger.warning(
                    "Subscription not found", subscription_id=subscription_id
                )
                return False

            subscription = self.subscriptions[subscription_id]
            pattern = subscription.topic

            # Remove subscription
            del self.subscriptions[subscription_id]

            # Remove from pattern index
            if pattern in self.subscription_patterns:
                self.subscription_patterns[pattern].remove(subscription_id)
                if not self.subscription_patterns[pattern]:
                    del self.subscription_patterns[pattern]

                    # If no more subscriptions for this pattern, remove the pattern
                    # Find and remove the pattern from patterns list
                    for i, p in enumerate(self.patterns):
                        if p.pattern == pattern:
                            del self.patterns[i]
                            break

                    # Remove from pattern index
                    if pattern in self.pattern_index:
                        del self.pattern_index[pattern]

            self.metrics["subscription_removes"] += 1

            self.logger.info(
                "Removed topic subscription",
                subscription_id=subscription_id,
                pattern=pattern,
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to remove subscription",
                subscription_id=subscription_id,
                error=str(e),
            )
            return False

    def route_message(
        self, topic: str, payload: str, **kwargs: Any
    ) -> list[tuple[str, Callable]]:
        """Route a message to all matching subscriptions.

        Args:
            topic: The message topic
            payload: The message payload
            **kwargs: Additional message metadata

        Returns:
            List of (subscription_id, callback) tuples for matching subscriptions
        """
        start_time = time.time()

        routes = []

        # Find matching patterns
        matching_patterns = self.find_matching_patterns(topic)

        for pattern in matching_patterns:
            # Find subscriptions for this pattern
            if pattern.pattern in self.subscription_patterns:
                for subscription_id in self.subscription_patterns[pattern.pattern]:
                    subscription = self.subscriptions.get(subscription_id)
                    if subscription and subscription.callback:
                        # Apply filters if any
                        if self._apply_filters(
                            subscription.filters, topic, payload, **kwargs
                        ):
                            routes.append((subscription_id, subscription.callback))

        self.metrics["topic_routes"] += len(routes)

        # Update performance metrics
        routing_time = time.time() - start_time
        self.metrics["routing_time"] += routing_time

        # Record performance data
        self._record_performance_data(topic, len(routes), routing_time)

        return routes

    def _apply_filters(
        self, filters: dict[str, Any], topic: str, payload: str, **kwargs: Any
    ) -> bool:
        """Apply subscription filters to determine if message should be processed.

        Args:
            filters: The filters to apply
            topic: The message topic
            payload: The message payload
            **kwargs: Additional message metadata

        Returns:
            True if message passes all filters, False otherwise
        """
        if not filters:
            return True

        try:
            for filter_key, filter_value in filters.items():
                if filter_key == "topic_regex" and isinstance(filter_value, str):
                    if not re.search(filter_value, topic):
                        return False
                elif filter_key == "payload_regex" and isinstance(filter_value, str):
                    if not re.search(filter_value, payload):
                        return False
                elif filter_key == "min_payload_length" and isinstance(
                    filter_value, int
                ):
                    if len(payload) < filter_value:
                        return False
                elif filter_key == "max_payload_length" and isinstance(
                    filter_value, int
                ):
                    if len(payload) > filter_value:
                        return False
                elif filter_key == "topic_prefix" and isinstance(filter_value, str):
                    if not topic.startswith(filter_value):
                        return False
                elif filter_key == "topic_suffix" and isinstance(filter_value, str):
                    if not topic.endswith(filter_value):
                        return False
                else:
                    # Unknown filter type - reject the message
                    return False

            return True

        except Exception as e:
            self.logger.error("Error applying filters", error=str(e))
            return False

    def _update_hierarchy_cache(self, pattern: str, remove: bool = False) -> None:
        """Update the topic hierarchy cache for optimization.

        Args:
            pattern: The pattern to update
            remove: Whether to remove the pattern from cache
        """
        try:
            # Clear cache when patterns change
            self.hierarchy_cache.clear()

            if remove:
                # Remove pattern from hierarchy
                for hierarchy_key in list(self.topic_hierarchy.keys()):
                    if pattern in self.topic_hierarchy[hierarchy_key]:
                        self.topic_hierarchy[hierarchy_key].remove(pattern)
                        if not self.topic_hierarchy[hierarchy_key]:
                            del self.topic_hierarchy[hierarchy_key]
            else:
                # Add pattern to hierarchy
                parts = pattern.split("/")
                for i in range(len(parts)):
                    hierarchy_key = "/".join(parts[: i + 1])
                    self.topic_hierarchy[hierarchy_key].add(pattern)

        except Exception as e:
            self.logger.error(
                "Error updating hierarchy cache", pattern=pattern, error=str(e)
            )

    def get_optimized_subscriptions(self, topics: list[str]) -> list[str]:
        """Get optimized list of subscriptions for a set of topics.

        Args:
            topics: List of topics to optimize subscriptions for

        Returns:
            Optimized list of subscription patterns
        """
        try:
            # Use hierarchy cache to find optimal subscription patterns
            optimized_patterns = set()

            for topic in topics:
                # Find the most specific pattern that covers this topic
                best_pattern = None
                best_specificity = -1

                for pattern in self.patterns:
                    if pattern.matches(topic):
                        # Calculate specificity (fewer wildcards = more specific)
                        # Lower number means more specific
                        specificity = -(
                            pattern.pattern.count("+") + pattern.pattern.count("#")
                        )
                        if specificity > best_specificity:
                            best_specificity = specificity
                            best_pattern = pattern.pattern

                if best_pattern:
                    optimized_patterns.add(best_pattern)
                else:
                    # If no pattern matches, add the topic itself
                    optimized_patterns.add(topic)

            return list(optimized_patterns)

        except Exception as e:
            self.logger.error("Error optimizing subscriptions", error=str(e))
            return topics

    def _cache_pattern_match(self, topic: str, patterns: list[TopicPattern]) -> None:
        """Cache pattern matching results for performance.

        Args:
            topic: The topic that was matched
            patterns: The matching patterns
        """
        # Implement LRU-style cache management
        if len(self._pattern_match_cache) >= self._cache_size_limit:
            # Remove oldest entries (simple FIFO for now)
            oldest_key = next(iter(self._pattern_match_cache))
            del self._pattern_match_cache[oldest_key]

        self._pattern_match_cache[topic] = patterns

    def _clear_pattern_cache(self) -> None:
        """Clear the pattern matching cache."""
        self._pattern_match_cache.clear()
        self.logger.debug("Pattern match cache cleared")

    def _record_performance_data(
        self, topic: str, route_count: int, processing_time: float
    ) -> None:
        """Record performance data for monitoring and optimization.

        Args:
            topic: The processed topic
            route_count: Number of routes created
            processing_time: Time taken to process the message
        """
        performance_data = {
            "timestamp": time.time(),
            "topic": topic,
            "route_count": route_count,
            "processing_time": processing_time,
            "total_patterns": len(self.patterns),
            "total_subscriptions": len(self.subscriptions),
            "cache_hit_rate": self._cache_hits
            / max(1, self._cache_hits + self._cache_misses),
        }

        self._performance_history.append(performance_data)

        # Limit history size
        if len(self._performance_history) > self._max_history_size:
            self._performance_history.pop(0)

    def get_performance_analysis(self) -> dict[str, Any]:
        """Get detailed performance analysis and recommendations.

        Returns:
            Dictionary containing performance analysis
        """
        if not self._performance_history:
            return {"message": "No performance data available"}

        # Calculate performance statistics
        processing_times = [
            data["processing_time"] for data in self._performance_history
        ]
        route_counts = [data["route_count"] for data in self._performance_history]

        analysis = {
            "total_messages_processed": len(self._performance_history),
            "average_processing_time": sum(processing_times) / len(processing_times),
            "max_processing_time": max(processing_times),
            "min_processing_time": min(processing_times),
            "average_routes_per_message": sum(route_counts) / len(route_counts),
            "cache_hit_rate": self._cache_hits
            / max(1, self._cache_hits + self._cache_misses),
            "performance_trends": self._analyze_performance_trends(),
            "optimization_recommendations": self._generate_optimization_recommendations(),
        }

        return analysis

    def _analyze_performance_trends(self) -> dict[str, Any]:
        """Analyze performance trends over time.

        Returns:
            Dictionary containing trend analysis
        """
        if len(self._performance_history) < 2:
            return {"message": "Insufficient data for trend analysis"}

        # Split data into recent and older periods
        mid_point = len(self._performance_history) // 2
        recent_data = self._performance_history[mid_point:]
        older_data = self._performance_history[:mid_point]

        recent_avg_time = sum(d["processing_time"] for d in recent_data) / len(
            recent_data
        )
        older_avg_time = sum(d["processing_time"] for d in older_data) / len(older_data)

        trend = "improving" if recent_avg_time < older_avg_time else "degrading"
        change_percentage = ((older_avg_time - recent_avg_time) / older_avg_time) * 100

        return {
            "trend": trend,
            "change_percentage": change_percentage,
            "recent_average_time": recent_avg_time,
            "older_average_time": older_avg_time,
        }

    def _generate_optimization_recommendations(self) -> list[str]:
        """Generate optimization recommendations based on performance data.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        # Check cache performance
        cache_hit_rate = self._cache_hits / max(
            1, self._cache_hits + self._cache_misses
        )
        if cache_hit_rate < 0.5:
            recommendations.append(
                "Consider increasing pattern match cache size for better performance"
            )

        # Check pattern complexity
        complex_patterns = [
            p for p in self.patterns if p.pattern.count("+") + p.pattern.count("#") > 3
        ]
        if complex_patterns:
            recommendations.append(
                f"Consider simplifying {len(complex_patterns)} complex patterns for better matching performance"
            )

        # Check subscription distribution
        if self.subscriptions:
            avg_subscriptions_per_pattern = len(self.subscriptions) / len(self.patterns)
            if avg_subscriptions_per_pattern > 10:
                recommendations.append(
                    "Consider consolidating subscriptions to reduce routing overhead"
                )

        # Check processing time
        if self._performance_history:
            avg_processing_time = sum(
                d["processing_time"] for d in self._performance_history
            ) / len(self._performance_history)
            if avg_processing_time > 0.001:  # 1ms threshold
                recommendations.append(
                    "Consider optimizing pattern matching algorithms for better performance"
                )

        if not recommendations:
            recommendations.append("Performance is within acceptable parameters")

        return recommendations

    def get_metrics(self) -> dict[str, Any]:
        """Get performance metrics for the topic pattern manager.

        Returns:
            Dictionary of performance metrics
        """
        return {
            **self.metrics,
            "total_patterns": len(self.patterns),
            "total_subscriptions": len(self.subscriptions),
            "hierarchy_cache_size": len(self.hierarchy_cache),
            "topic_hierarchy_size": len(self.topic_hierarchy),
            "pattern_match_cache_size": len(self._pattern_match_cache),
            "cache_hit_rate": self._cache_hits
            / max(1, self._cache_hits + self._cache_misses),
            "average_matching_time": self.metrics["matching_time"]
            / max(1, self.metrics["pattern_matches"]),
            "average_routing_time": self.metrics["routing_time"]
            / max(1, self.metrics["topic_routes"]),
        }

    def clear_metrics(self) -> None:
        """Clear performance metrics."""
        for key in self.metrics:
            self.metrics[key] = 0
        self._cache_hits = 0
        self._cache_misses = 0
        self._performance_history.clear()
        self._clear_pattern_cache()

    def optimize_performance(self) -> dict[str, Any]:
        """Perform performance optimization operations.

        Returns:
            Dictionary containing optimization results
        """
        optimization_results = {
            "cache_cleared": False,
            "patterns_reordered": False,
            "hierarchy_optimized": False,
            "recommendations": [],
        }

        # Clear caches if they're getting too large
        if len(self._pattern_match_cache) > self._cache_size_limit * 0.8:
            self._clear_pattern_cache()
            optimization_results["cache_cleared"] = True
            optimization_results["recommendations"].append(
                "Pattern match cache cleared due to size"
            )

        # Reorder patterns by priority if needed
        if self.patterns:
            original_order = [p.pattern for p in self.patterns]
            self.patterns.sort(key=lambda p: p.priority, reverse=True)
            new_order = [p.pattern for p in self.patterns]

            if original_order != new_order:
                optimization_results["patterns_reordered"] = True
                optimization_results["recommendations"].append(
                    "Patterns reordered by priority"
                )

        # Optimize hierarchy cache
        if len(self.hierarchy_cache) > 1000:
            self.hierarchy_cache.clear()
            optimization_results["hierarchy_optimized"] = True
            optimization_results["recommendations"].append(
                "Hierarchy cache cleared due to size"
            )

        return optimization_results
