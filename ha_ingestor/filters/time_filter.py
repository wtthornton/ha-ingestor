"""Time-based filter for Home Assistant events."""

from datetime import datetime, time
from typing import Any

from ..models.events import Event
from .base import Filter


class TimeFilter(Filter):
    """Filter events based on time-based criteria."""

    def __init__(
        self,
        time_ranges: list[tuple[time, time]] | None = None,
        days_of_week: list[int] | None = None,
        business_hours: bool = False,
        name: str | None = None,
    ):
        """Initialize time filter.

        Args:
            time_ranges: List of (start_time, end_time) tuples in 24-hour format
            days_of_week: List of days (0=Monday, 6=Sunday) to allow
            business_hours: Whether to use business hours (9 AM - 5 PM, Mon-Fri)
            name: Optional name for the filter
        """
        super().__init__(name or "time_filter")

        self.time_ranges = time_ranges or []
        self.days_of_week = days_of_week or []
        self.business_hours = business_hours

        # Set up business hours if requested
        if business_hours:
            self._setup_business_hours()

        # Validate inputs
        self._validate_config()

        self.logger.info(
            "Time filter initialized",
            time_ranges=self.time_ranges,
            days_of_week=self.days_of_week,
            business_hours=business_hours,
        )

    def _setup_business_hours(self) -> None:
        """Set up business hours (9 AM - 5 PM, Monday-Friday)."""
        if not self.time_ranges:
            self.time_ranges = [(time(9, 0), time(17, 0))]  # 9 AM - 5 PM

        if not self.days_of_week:
            self.days_of_week = [0, 1, 2, 3, 4]  # Monday to Friday

        self.logger.info(
            "Business hours configured",
            time_ranges=self.time_ranges,
            days_of_week=self.days_of_week,
        )

    def _validate_config(self) -> None:
        """Validate filter configuration."""
        # Validate time ranges
        for start_time, end_time in self.time_ranges:
            if not isinstance(start_time, time) or not isinstance(end_time, time):
                raise ValueError("Time ranges must contain time objects")

        # Validate days of week
        for day in self.days_of_week:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise ValueError(
                    "Days of week must be integers 0-6 (Monday=0, Sunday=6)"
                )

    async def should_process(self, event: Event) -> bool:
        """Check if event timestamp falls within allowed time ranges.

        Args:
            event: The event to check

        Returns:
            True if event time is allowed, False otherwise
        """
        if not event.timestamp:
            self.logger.debug(
                "Event has no timestamp, filtering out", event_entity_id=event.entity_id
            )
            return False

        # Convert timestamp to datetime if needed
        event_time = self._normalize_timestamp(event.timestamp)

        # Check day of week
        if self.days_of_week and event_time.weekday() not in self.days_of_week:
            self.logger.debug(
                "Event day not allowed",
                event_time=event_time,
                day_of_week=event_time.weekday(),
                allowed_days=self.days_of_week,
            )
            return False

        # Check time ranges
        event_time_of_day = event_time.time()
        time_allowed = False

        for start_time, end_time in self.time_ranges:
            if self._is_time_in_range(event_time_of_day, start_time, end_time):
                time_allowed = True
                break

        if not time_allowed:
            self.logger.debug(
                "Event time not allowed",
                event_time=event_time,
                time_of_day=event_time_of_day,
                time_ranges=self.time_ranges,
            )
            return False

        self.logger.debug(
            "Event time allowed", event_time=event_time, time_of_day=event_time_of_day
        )
        return True

    def _normalize_timestamp(self, timestamp: Any) -> datetime:
        """Normalize timestamp to datetime object.

        Args:
            timestamp: Timestamp to normalize

        Returns:
            Normalized datetime object
        """
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, int | float):  # noqa: B007
            # Assume Unix timestamp
            return datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, str):
            # Try to parse ISO format
            try:
                return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:  # noqa: B904 - Intentionally not chaining exception
                # Try other common formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        return datetime.strptime(timestamp, fmt)
                    except (
                        ValueError
                    ):  # noqa: B904 - Intentionally not chaining exception
                        continue
                raise ValueError(f"Unable to parse timestamp: {timestamp}") from None
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

    def _is_time_in_range(
        self, event_time: time, start_time: time, end_time: time
    ) -> bool:
        """Check if event time falls within a time range.

        Args:
            event_time: Time of the event
            start_time: Start of allowed time range
            end_time: End of allowed time range

        Returns:
            True if time is in range, False otherwise
        """
        if start_time <= end_time:
            # Same day range (e.g., 9 AM to 5 PM)
            return start_time <= event_time <= end_time
        else:
            # Overnight range (e.g., 10 PM to 6 AM)
            return event_time >= start_time or event_time <= end_time

    def add_time_range(self, start_time: time, end_time: time) -> None:
        """Add a time range to the filter.

        Args:
            start_time: Start time
            end_time: End time
        """
        if not isinstance(start_time, time) or not isinstance(end_time, time):
            raise ValueError("Start and end times must be time objects")

        self.time_ranges.append((start_time, end_time))
        self.logger.info(
            "Added time range",
            start_time=start_time,
            end_time=end_time,
            total_ranges=len(self.time_ranges),
        )

    def remove_time_range(self, start_time: time, end_time: time) -> bool:
        """Remove a time range from the filter.

        Args:
            start_time: Start time to remove
            end_time: End time to remove

        Returns:
            True if range was removed, False if not found
        """
        try:
            self.time_ranges.remove((start_time, end_time))
            self.logger.info(
                "Removed time range",
                start_time=start_time,
                end_time=end_time,
                total_ranges=len(self.time_ranges),
            )
            return True
        except ValueError:  # noqa: B904 - Intentionally not chaining exception
            return False

    def add_day_of_week(self, day: int) -> None:
        """Add a day of the week to the filter.

        Args:
            day: Day of week (0=Monday, 6=Sunday)
        """
        if not isinstance(day, int) or day < 0 or day > 6:
            raise ValueError("Day must be integer 0-6 (Monday=0, Sunday=6)")

        if day not in self.days_of_week:
            self.days_of_week.append(day)
            self.logger.info(
                "Added day of week", day=day, total_days=len(self.days_of_week)
            )

    def remove_day_of_week(self, day: int) -> bool:
        """Remove a day of the week from the filter.

        Args:
            day: Day of week to remove

        Returns:
            True if day was removed, False if not found
        """
        if day in self.days_of_week:
            self.days_of_week.remove(day)
            self.logger.info(
                "Removed day of week", day=day, total_days=len(self.days_of_week)
            )
            return True
        return False

    def set_business_hours(self, enabled: bool) -> None:
        """Enable or disable business hours mode.

        Args:
            enabled: Whether to enable business hours
        """
        if enabled and not self.business_hours:
            self._setup_business_hours()
        elif not enabled and self.business_hours:
            # Reset to empty configuration
            self.time_ranges = []
            self.days_of_week = []
            self.business_hours = False

        self.logger.info("Business hours mode updated", enabled=enabled)

    def get_filter_config(self) -> dict:
        """Get current filter configuration.

        Returns:
            Dictionary with filter configuration
        """
        return {
            "time_ranges": [(str(start), str(end)) for start, end in self.time_ranges],
            "days_of_week": self.days_of_week,
            "business_hours": self.business_hours,
        }
