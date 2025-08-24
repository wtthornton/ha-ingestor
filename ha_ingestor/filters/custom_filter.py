"""Custom filter for user-defined filtering functions."""

from collections.abc import Callable
from typing import Any

from ..models.events import Event
from .base import Filter


class CustomFilter(Filter):
    """Filter that uses user-defined functions for filtering logic."""

    def __init__(
        self,
        filter_func: Callable,
        transform_func: Callable | None = None,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ):
        """Initialize custom filter.

        Args:
            filter_func: Function that takes an Event and returns bool
            transform_func: Optional function that takes an Event and returns transformed Event
            name: Optional name for the filter
            config: Optional configuration dictionary passed to filter functions
        """
        super().__init__(name or "custom_filter")

        if not callable(filter_func):
            raise ValueError("filter_func must be callable")

        self.filter_func = filter_func
        self.transform_func = transform_func
        self.config = config or {}

        self.logger.info(
            "Custom filter initialized",
            filter_func=filter_func.__name__,
            has_transform=transform_func is not None,
            config_keys=list(self.config.keys()),
        )

    async def should_process(self, event: Event) -> bool:
        """Use custom function to determine if event should be processed.

        Args:
            event: The event to check

        Returns:
            Result of custom filter function
        """
        try:
            # Call the custom filter function
            if self.config:
                result = self.filter_func(event, **self.config)
            else:
                result = self.filter_func(event)

            # Ensure result is boolean
            if not isinstance(result, bool):
                self.logger.warning(
                    "Custom filter function returned non-boolean, converting",
                    result=result,
                    filter_func=self.filter_func.__name__,
                )
                result = bool(result)

            if result:
                self.logger.debug(
                    "Custom filter allowed event",
                    filter_func=self.filter_func.__name__,
                    event_entity_id=event.entity_id,
                )
            else:
                self.logger.debug(
                    "Custom filter blocked event",
                    filter_func=self.filter_func.__name__,
                    event_entity_id=event.entity_id,
                )

            return result

        except Exception as e:
            self.logger.error(
                "Error in custom filter function",
                filter_func=self.filter_func.__name__,
                error=str(e),
                event_entity_id=event.entity_id,
            )
            # On error, allow the event to pass through
            return True

    async def transform(self, event: Event) -> Event:
        """Use custom function to transform the event.

        Args:
            event: The event to transform

        Returns:
            Transformed event or original event if no transform function
        """
        if not self.transform_func:
            return event

        try:
            # Call the custom transform function
            if self.config:
                transformed_event = self.transform_func(event, **self.config)
            else:
                transformed_event = self.transform_func(event)

            # Ensure result is an Event
            if not isinstance(transformed_event, Event):
                self.logger.warning(
                    "Custom transform function returned non-Event, using original",
                    result_type=type(transformed_event),
                    transform_func=self.transform_func.__name__,
                )
                return event

            self.logger.debug(
                "Event transformed by custom function",
                transform_func=self.transform_func.__name__,
                event_entity_id=event.entity_id,
            )
            return transformed_event

        except Exception as e:
            self.logger.error(
                "Error in custom transform function",
                transform_func=self.transform_func.__name__,
                error=str(e),
                event_entity_id=event.entity_id,
            )
            # On error, return original event
            return event

    def update_filter_function(self, filter_func: Callable) -> None:
        """Update the filter function.

        Args:
            filter_func: New filter function
        """
        if not callable(filter_func):
            raise ValueError("filter_func must be callable")

        old_func = self.filter_func.__name__
        self.filter_func = filter_func

        self.logger.info(
            "Updated filter function", old_func=old_func, new_func=filter_func.__name__
        )

    def update_transform_function(self, transform_func: Callable | None) -> None:
        """Update the transform function.

        Args:
            transform_func: New transform function or None to disable
        """
        if transform_func is not None and not callable(transform_func):
            raise ValueError("transform_func must be callable or None")

        old_func = self.transform_func.__name__ if self.transform_func else None
        self.transform_func = transform_func

        self.logger.info(
            "Updated transform function",
            old_func=old_func,
            new_func=transform_func.__name__ if transform_func else None,
        )

    def update_config(self, config: dict[str, Any]) -> None:
        """Update the configuration dictionary.

        Args:
            config: New configuration dictionary
        """
        old_config = self.config.copy()
        self.config = config or {}

        self.logger.info(
            "Updated filter configuration",
            old_keys=list(old_config.keys()),
            new_keys=list(self.config.keys()),
        )

    def get_filter_config(self) -> dict[str, Any]:
        """Get current filter configuration.

        Returns:
            Dictionary with filter configuration
        """
        return {
            "filter_func": self.filter_func.__name__,
            "transform_func": (
                self.transform_func.__name__ if self.transform_func else None
            ),
            "config": self.config.copy(),
        }


# Example custom filter functions
def example_high_value_filter(event: Event, min_value: float = 100.0) -> bool:
    """Example filter that only allows events with high numeric values.

    Args:
        event: The event to check
        min_value: Minimum value threshold

    Returns:
        True if event has high value, False otherwise
    """
    if not event.attributes:
        return False

    # Look for numeric attributes
    for _key, value in event.attributes.items():
        try:
            if isinstance(value, int | float) and value >= min_value:
                return True
        except (TypeError, ValueError):
            continue

    return False


def example_priority_filter(
    event: Event, priority_entities: list[Any] | None = None
) -> bool:
    """Example filter that prioritizes certain entities.

    Args:
        event: The event to check
        priority_entities: List of priority entity IDs

    Returns:
        True if event is from priority entity, False otherwise
    """
    if not priority_entities:
        priority_entities = ["light.living_room", "switch.main_power"]

    return event.entity_id in priority_entities


def example_event_transformer(event: Event, add_metadata: bool = True) -> Event:
    """Example transform function that adds metadata to events.

    Args:
        event: The event to transform
        add_metadata: Whether to add metadata

    Returns:
        Transformed event
    """
    if not add_metadata:
        return event

    # Create new event with additional metadata
    new_attributes = event.attributes.copy() if event.attributes else {}
    new_attributes["_filtered_by"] = "custom_filter"
    new_attributes["_filter_timestamp"] = event.timestamp

    # Create new event (assuming Event class supports this)
    # This is a simplified example - actual implementation depends on Event class
    return event
