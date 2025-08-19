"""Event processing pipeline for Home Assistant data ingestion."""

import asyncio
import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from .metrics import get_metrics_collector
from .models import InfluxDBPoint, MQTTEvent, WebSocketEvent
from .utils.logging import get_logger


@dataclass
class PipelineStats:
    """Statistics for the event processing pipeline."""

    events_processed: int = 0
    events_deduplicated: int = 0
    events_transformed: int = 0
    events_stored: int = 0
    events_failed: int = 0
    processing_time_avg: float = 0.0
    last_event_time: datetime | None = None

    def update_processing_time(self, processing_time: float) -> None:
        """Update average processing time."""
        if self.events_processed == 0:
            self.processing_time_avg = processing_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.processing_time_avg = (
                alpha * processing_time + (1 - alpha) * self.processing_time_avg
            )


class EventProcessor:
    """Event processing pipeline for Home Assistant events."""

    def __init__(self, config: Any = None) -> None:
        """Initialize event processor.

        Args:
            config: Configuration settings. If None, uses global settings.
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Event deduplication
        self._dedup_window = getattr(config, "pipeline_dedup_window", 5.0)  # seconds
        self._recent_events: dict[str, datetime] = {}
        self._dedup_cache_size = getattr(config, "pipeline_dedup_cache_size", 10000)

        # Event transformation
        self._transformers: dict[str, Callable] = {}
        self._filters: dict[str, Callable] = {}

        # Storage handlers
        self._storage_handlers: list[Callable] = []

        # Processing queue
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: asyncio.Task | None = None

        # Statistics
        self._stats = PipelineStats()

        # Event routing
        self._event_routes: dict[str, list[str]] = {
            "mqtt": ["influxdb"],
            "websocket": ["influxdb"],
        }

        # Performance monitoring
        self._max_processing_time = getattr(
            config, "pipeline_max_processing_time", 1.0
        )  # seconds
        self._batch_size = getattr(config, "pipeline_batch_size", 50)

        # Initialize default transformers and filters
        self._setup_default_components()

    async def start(self) -> None:
        """Start the event processing pipeline."""
        if self._processing_task:
            self.logger.warning("Pipeline already running")
            return

        self.logger.info("Starting event processing pipeline")
        self._processing_task = asyncio.create_task(self._processing_loop())

    async def stop(self) -> None:
        """Stop the event processing pipeline."""
        if not self._processing_task:
            return

        self.logger.info("Stopping event processing pipeline")

        # Cancel processing task
        self._processing_task.cancel()

        try:
            await self._processing_task
        except asyncio.CancelledError:
            pass

        self._processing_task = None

        # Process remaining events
        await self._process_remaining_events()

        self.logger.info("Event processing pipeline stopped")

    def is_running(self) -> bool:
        """Check if pipeline is running.

        Returns:
            True if running, False otherwise.
        """
        return self._processing_task is not None and not self._processing_task.done()

    async def process_event(self, event: MQTTEvent | WebSocketEvent) -> bool:
        """Process a single event through the pipeline.

        Args:
            event: Event to process (MQTTEvent or WebSocketEvent)

        Returns:
            True if event was queued successfully, False otherwise.
        """
        try:
            # Add event to processing queue
            await self._processing_queue.put(event)
            return True

        except Exception as e:
            self.logger.error("Error queuing event for processing", error=str(e))
            self._stats.events_failed += 1
            return False

    async def process_events(self, events: list[MQTTEvent | WebSocketEvent]) -> bool:
        """Process multiple events through the pipeline.

        Args:
            events: List of events to process

        Returns:
            True if all events were queued successfully, False otherwise.
        """
        try:
            success_count = 0
            for event in events:
                if await self.process_event(event):
                    success_count += 1

            self.logger.debug(
                "Queued events for processing",
                total=len(events),
                successful=success_count,
            )

            return success_count == len(events)

        except Exception as e:
            self.logger.error("Error queuing events for processing", error=str(e))
            return False

    def add_storage_handler(self, handler: Callable) -> None:
        """Add a storage handler to the pipeline.

        Args:
            handler: Function to handle event storage
        """
        self._storage_handlers.append(handler)
        self.logger.debug("Added storage handler", handler=handler.__name__)

    def add_transformer(self, event_type: str, transformer: Callable) -> None:
        """Add a transformer for a specific event type.

        Args:
            event_type: Type of event to transform
            transformer: Function to transform the event
        """
        self._transformers[event_type] = transformer
        self.logger.debug("Added transformer", event_type=event_type)

    def add_filter(self, event_type: str, filter_func: Callable) -> None:
        """Add a filter for a specific event type.

        Args:
            event_type: Type of event to filter
            filter_func: Function to filter the event
        """
        self._filters[event_type] = filter_func
        self.logger.debug("Added filter", event_type=event_type)

    def get_stats(self) -> dict[str, Any]:
        """Get pipeline statistics.

        Returns:
            Dictionary with pipeline statistics.
        """
        return {
            "running": self.is_running(),
            "queue_size": self._processing_queue.qsize(),
            "stats": {
                "events_processed": self._stats.events_processed,
                "events_deduplicated": self._stats.events_deduplicated,
                "events_transformed": self._stats.events_transformed,
                "events_stored": self._stats.events_stored,
                "events_failed": self._stats.events_failed,
                "processing_time_avg": self._stats.processing_time_avg,
                "last_event_time": (
                    self._stats.last_event_time.isoformat()
                    if self._stats.last_event_time
                    else None
                ),
            },
        }

    async def _processing_loop(self) -> None:
        """Main processing loop for events."""
        self.logger.info("Event processing loop started")

        try:
            while True:
                # Process events in batches
                events = []

                # Get first event
                try:
                    event = await asyncio.wait_for(
                        self._processing_queue.get(), timeout=1.0
                    )
                    events.append(event)
                except TimeoutError:
                    continue

                # Get additional events up to batch size
                while len(events) < self._batch_size:
                    try:
                        event = self._processing_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break

                # Process batch
                if events:
                    await self._process_batch(events)

                # Update queue size metrics periodically
                await self._update_metrics()

        except asyncio.CancelledError:
            self.logger.debug("Processing loop cancelled")
        except Exception as e:
            self.logger.error("Error in processing loop", error=str(e))
        finally:
            self.logger.info("Event processing loop stopped")

    async def _process_batch(self, events: list[MQTTEvent | WebSocketEvent]) -> None:
        """Process a batch of events.

        Args:
            events: List of events to process
        """
        start_time = datetime.utcnow()

        try:
            # Process each event
            for event in events:
                await self._process_single_event(event)

            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._stats.update_processing_time(processing_time)

            # Record pipeline processing time
            metrics_collector = get_metrics_collector()
            metrics_collector.record_pipeline_processing_time(processing_time)

            if processing_time > self._max_processing_time:
                self.logger.warning(
                    "Batch processing took longer than expected",
                    processing_time=processing_time,
                    max_time=self._max_processing_time,
                )

        except Exception as e:
            self.logger.error("Error processing event batch", error=str(e))
            self._stats.events_failed += len(events)

    async def _process_single_event(self, event: MQTTEvent | WebSocketEvent) -> None:
        """Process a single event through the pipeline.

        Args:
            event: Event to process
        """
        # Get metrics collector
        metrics_collector = get_metrics_collector()

        try:
            # Check deduplication
            if self._is_duplicate(event):
                self._stats.events_deduplicated += 1
                metrics_collector.record_event_deduplicated()
                self.logger.debug(
                    "Event deduplicated", event_id=self._get_event_id(event)
                )
                return

            # Apply filters
            if not self._should_process_event(event):
                self.logger.debug(
                    "Event filtered out", event_id=self._get_event_id(event)
                )
                return

            # Transform event
            transformed_event = await self._transform_event(event)
            if transformed_event:
                self._stats.events_transformed += 1

            # Store event
            if await self._store_event(transformed_event or event):
                self._stats.events_stored += 1
                # Record successful event processing
                source = self._get_event_type(event)
                metrics_collector.record_event_processed(source, success=True)
            else:
                self._stats.events_failed += 1
                # Record failed event processing
                source = self._get_event_type(event)
                metrics_collector.record_event_processed(source, success=False)

            # Update statistics
            self._stats.events_processed += 1
            self._stats.last_event_time = datetime.utcnow()

            # Add to deduplication cache
            self._add_to_dedup_cache(event)

        except Exception as e:
            self.logger.error(
                "Error processing event",
                event_id=self._get_event_id(event),
                error=str(e),
            )
            self._stats.events_failed += 1
            # Record error
            metrics_collector.record_error()

    def _is_duplicate(self, event: MQTTEvent | WebSocketEvent) -> bool:
        """Check if event is a duplicate.

        Args:
            event: Event to check

        Returns:
            True if duplicate, False otherwise.
        """
        event_id = self._get_event_id(event)

        if event_id in self._recent_events:
            last_time = self._recent_events[event_id]
            time_diff = (datetime.utcnow() - last_time).total_seconds()

            if time_diff < self._dedup_window:
                return True

        return False

    def _should_process_event(self, event: MQTTEvent | WebSocketEvent) -> bool:
        """Check if event should be processed.

        Args:
            event: Event to check

        Returns:
            True if event should be processed, False otherwise.
        """
        event_type = self._get_event_type(event)

        # Check if we have a filter for this event type
        if event_type in self._filters:
            try:
                result = self._filters[event_type](event)
                if isinstance(result, bool):
                    return result
                else:
                    self.logger.warning(
                        "Filter returned non-boolean value",
                        event_type=event_type,
                        result=result,
                    )
                    return True  # Default to processing if filter returns non-boolean
            except Exception as e:
                self.logger.error(
                    "Error applying filter", event_type=event_type, error=str(e)
                )
                return True  # Default to processing if filter fails

        return True

    async def _transform_event(self, event: MQTTEvent | WebSocketEvent) -> Any | None:
        """Transform event using registered transformers.

        Args:
            event: Event to transform

        Returns:
            Transformed event or None if no transformation
        """
        event_type = self._get_event_type(event)

        # Check if we have a transformer for this event type
        if event_type in self._transformers:
            try:
                transformer = self._transformers[event_type]
                if asyncio.iscoroutinefunction(transformer):
                    result = await transformer(event)
                else:
                    result = transformer(event)

                return result

            except Exception as e:
                self.logger.error(
                    "Error applying transformer", event_type=event_type, error=str(e)
                )

        return None

    async def _store_event(self, event: MQTTEvent | WebSocketEvent) -> bool:
        """Store event using registered storage handlers.

        Args:
            event: Event to store

        Returns:
            True if storage successful, False otherwise.
        """
        if not self._storage_handlers:
            self.logger.warning("No storage handlers registered")
            return False

        success_count = 0
        total_handlers = len(self._storage_handlers)

        for handler in self._storage_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event)
                else:
                    result = handler(event)

                if result:
                    success_count += 1

            except Exception as e:
                self.logger.error(
                    "Error in storage handler", handler=handler.__name__, error=str(e)
                )

        return success_count > 0

    async def _update_metrics(self) -> None:
        """Update pipeline metrics."""
        try:
            metrics_collector = get_metrics_collector()

            # Update queue size metric
            queue_size = self._processing_queue.qsize()
            metrics_collector.record_pipeline_queue_size(queue_size)

        except Exception as e:
            self.logger.error("Error updating metrics", error=str(e))

    def _get_event_id(self, event: MQTTEvent | WebSocketEvent) -> str:
        """Generate unique event ID for deduplication.

        Args:
            event: Event to generate ID for

        Returns:
            Unique event ID string
        """
        if isinstance(event, MQTTEvent):
            # For MQTT events, use topic + payload hash
            content = f"{event.topic}:{event.payload}"
        elif isinstance(event, WebSocketEvent):
            # For WebSocket events, use event type + data hash
            content = f"{event.event_type}:{str(event.data)}"
        else:
            # Fallback
            content = str(event)

        return hashlib.md5(content.encode()).hexdigest()

    def _get_event_type(self, event: MQTTEvent | WebSocketEvent) -> str:
        """Get event type for routing and processing.

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

    def _add_to_dedup_cache(self, event: MQTTEvent | WebSocketEvent) -> None:
        """Add event to deduplication cache.

        Args:
            event: Event to add to cache
        """
        event_id = self._get_event_id(event)
        self._recent_events[event_id] = datetime.utcnow()

        # Clean up old entries if cache is too large
        if len(self._recent_events) > self._dedup_cache_size:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self._dedup_window)
            self._recent_events = {
                k: v for k, v in self._recent_events.items() if v > cutoff_time
            }

    async def _process_remaining_events(self) -> None:
        """Process any remaining events in the queue."""
        remaining_events = []

        try:
            while not self._processing_queue.empty():
                event = self._processing_queue.get_nowait()
                remaining_events.append(event)
        except asyncio.QueueEmpty:
            pass

        if remaining_events:
            self.logger.info("Processing remaining events", count=len(remaining_events))
            await self._process_batch(remaining_events)

    def _setup_default_components(self) -> None:
        """Setup default transformers and filters."""

        # Default MQTT event transformer - convert to InfluxDB point
        def mqtt_to_influxdb(event: MQTTEvent) -> InfluxDBPoint:
            # Filter out None values from tags
            tags = {k: v for k, v in event.get_tags().items() if v is not None}
            return InfluxDBPoint(
                measurement=event.get_measurement_name(),
                tags=tags,
                fields=event.get_fields(),
                timestamp=event.timestamp,
            )

        # Default WebSocket event transformer - convert to InfluxDB point
        def websocket_to_influxdb(event: WebSocketEvent) -> InfluxDBPoint:
            # Filter out None values from tags
            tags = {k: v for k, v in event.get_tags().items() if v is not None}
            return InfluxDBPoint(
                measurement=event.get_measurement_name(),
                tags=tags,
                fields=event.get_fields(),
                timestamp=event.timestamp,
            )

        # Default filter - accept all events
        def accept_all(event: MQTTEvent | WebSocketEvent) -> bool:
            return True

        # Register default components
        self.add_transformer("mqtt", mqtt_to_influxdb)
        self.add_transformer("websocket", websocket_to_influxdb)
        self.add_filter("mqtt", accept_all)
        self.add_filter("websocket", accept_all)
