"""Base filter classes and filter chain implementation."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.logging import get_logger
from ..models.events import Event
from ..metrics.collector import get_metrics_collector

logger = get_logger(__name__)


@dataclass
class FilterResult:
    """Result of a filter operation."""
    
    should_process: bool
    transformed_event: Optional[Event] = None
    filter_name: str = ""
    processing_time_ms: float = 0.0
    cache_hit: bool = False


class Filter(ABC):
    """Base class for all filters."""
    
    def __init__(self, name: str = None):
        """Initialize filter.
        
        Args:
            name: Name of the filter for logging and identification
        """
        self.name = name or self.__class__.__name__
        self.logger = get_logger(f"{__name__}.{self.name}")
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_processed = 0
        self._metrics_collector = get_metrics_collector()
        self._filter_type = self.__class__.__name__.lower().replace('filter', '')
        
    @abstractmethod
    async def should_process(self, event: Event) -> bool:
        """Determine if an event should be processed.
        
        Args:
            event: The event to evaluate
            
        Returns:
            True if the event should be processed, False otherwise
        """
        pass
    
    async def transform(self, event: Event) -> Event:
        """Transform an event (optional).
        
        Args:
            event: The event to transform
            
        Returns:
            The transformed event (defaults to original event)
        """
        return event
    
    async def process(self, event: Event) -> FilterResult:
        """Process an event through this filter.
        
        Args:
            event: The event to process
            
        Returns:
            FilterResult with processing decision and transformed event
        """
        start_time = asyncio.get_event_loop().time()
        
        # Check cache first
        cache_key = self._get_cache_key(event)
        if cache_key in self._cache:
            self._cache_hits += 1
            cached_result = self._cache[cache_key]
            
            # Record cache hit metrics
            self._metrics_collector.record_filter_metrics(
                self.name, self._filter_type, 0.0, True, False
            )
            
            return FilterResult(
                should_process=cached_result.should_process,
                transformed_event=cached_result.transformed_event,
                filter_name=self.name,
                processing_time_ms=0.0,
                cache_hit=True
            )
        
        # Process the event
        try:
            should_process = await self.should_process(event)
            transformed_event = event
            
            if should_process:
                transformed_event = await self.transform(event)
            
            # Create result
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            result = FilterResult(
                should_process=should_process,
                transformed_event=transformed_event,
                filter_name=self.name,
                processing_time_ms=processing_time,
                cache_hit=False
            )
            
            # Cache the result
            self._cache[cache_key] = result
            
            # Record processing metrics
            self._metrics_collector.record_filter_metrics(
                self.name, self._filter_type, 
                processing_time / 1000.0,  # Convert to seconds for metrics
                False,  # Not a cache hit
                not should_process  # Event filtered out if should_process is False
            )
            
            # Update cache size metrics
            self._metrics_collector.update_filter_cache_size(
                self.name, self._filter_type, len(self._cache)
            )
            
            self._total_processed += 1
            return result
            
        except Exception as e:
            self.logger.error("Error processing event in filter", 
                            filter_name=self.name, error=str(e))
            # On error, allow the event to pass through
            return FilterResult(
                should_process=True,
                transformed_event=event,
                filter_name=self.name,
                processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                cache_hit=False
            )
    
    def _get_cache_key(self, event: Event) -> str:
        """Generate a cache key for an event.
        
        Args:
            event: The event to generate a key for
            
        Returns:
            Cache key string
        """
        # Simple cache key based on event properties
        return f"{event.domain}:{event.entity_id}:{hash(str(event.attributes))}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filter statistics.
        
        Returns:
            Dictionary with filter statistics
        """
        return {
            "name": self.name,
            "total_processed": self._total_processed,
            "cache_hits": self._cache_hits,
            "cache_misses": self._total_processed - self._cache_hits,
            "cache_hit_rate": self._cache_hits / max(self._total_processed, 1),
            "cache_size": len(self._cache)
        }
    
    def clear_cache(self) -> None:
        """Clear the filter's cache."""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


class FilterChain:
    """Chain of filters to process events sequentially."""
    
    def __init__(self, filters: List[Filter] = None, name: str = "filter_chain"):
        """Initialize filter chain.
        
        Args:
            filters: List of filters to apply in order
            name: Name of the filter chain
        """
        self.filters = filters or []
        self.name = name
        self.logger = get_logger(f"{__name__}.{self.name}")
        self._total_processed = 0
        self._total_filtered = 0
        self._processing_times = []
        self._metrics_collector = get_metrics_collector()
        
    def add_filter(self, filter: Filter) -> None:
        """Add a filter to the chain.
        
        Args:
            filter: Filter to add
        """
        self.filters.append(filter)
        self.logger.info("Added filter to chain", 
                        filter_name=filter.name, 
                        total_filters=len(self.filters))
    
    def remove_filter(self, filter_name: str) -> bool:
        """Remove a filter from the chain by name.
        
        Args:
            filter_name: Name of the filter to remove
            
        Returns:
            True if filter was removed, False if not found
        """
        for i, filter in enumerate(self.filters):
            if filter.name == filter_name:
                removed_filter = self.filters.pop(i)
                self.logger.info("Removed filter from chain", 
                               filter_name=removed_filter.name,
                               total_filters=len(self.filters))
                return True
        return False
    
    async def process_event(self, event: Event) -> Optional[Event]:
        """Process an event through the entire filter chain.
        
        Args:
            event: The event to process
            
        Returns:
            The transformed event if it passes all filters, None if filtered out
        """
        start_time = asyncio.get_event_loop().time()
        current_event = event
        

        
        try:
            for filter in self.filters:
                result = await filter.process(current_event)
                

                
                if not result.should_process:
                    self._total_filtered += 1
                    

                    
                    self.logger.debug("Event filtered out", 
                                    filter_name=filter.name,
                                    event_domain=event.domain,
                                    event_entity_id=event.entity_id)
                    return None
                
                # Update event with transformation
                if result.transformed_event:
                    current_event = result.transformed_event
                
                # Log performance if significant
                if result.processing_time_ms > 10.0:  # Log if >10ms
                    self.logger.warning("Filter processing time high",
                                      filter_name=filter.name,
                                      processing_time_ms=result.processing_time_ms)
            
            # Event passed all filters
            self._total_processed += 1
            total_time = (asyncio.get_event_loop().time() - start_time) * 1000
            self._processing_times.append(total_time)
            
            # Keep only last 1000 processing times for stats
            if len(self._processing_times) > 1000:
                self._processing_times = self._processing_times[-1000:]
            

            
            # Record filter chain metrics
            self._metrics_collector.record_filter_chain_metrics(
                len(self.filters),
                self._total_processed,
                self._total_filtered,
                total_time / 1000.0  # Convert to seconds for metrics
            )
            

            
            self.logger.debug("Event processed successfully",
                            event_domain=event.domain,
                            event_entity_id=event.entity_id,
                            total_time_ms=total_time)
            
            return current_event
            
        except Exception as e:
            self.logger.error("Error in filter chain", 
                            error=str(e),
                            event_domain=event.domain,
                            event_entity_id=event.entity_id)
            # On error, allow the event to pass through
            return event
    
    def get_stats(self) -> Dict[str, Any]:
        """Get filter chain statistics.
        
        Returns:
            Dictionary with filter chain statistics
        """
        if not self._processing_times:
            avg_time = 0.0
            max_time = 0.0
            min_time = 0.0
        else:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            max_time = max(self._processing_times)
            min_time = min(self._processing_times)
        
        filter_stats = [filter.get_stats() for filter in self.filters]
        
        return {
            "name": self.name,
            "total_filters": len(self.filters),
            "total_processed": self._total_processed,
            "total_filtered": self._total_filtered,
            "filter_rate": self._total_filtered / max(self._total_processed + self._total_filtered, 1),
            "avg_processing_time_ms": avg_time,
            "max_processing_time_ms": max_time,
            "min_processing_time_ms": min_time,
            "filter_stats": filter_stats
        }
    
    def clear_cache(self) -> None:
        """Clear cache for all filters in the chain."""
        for filter in self.filters:
            filter.clear_cache()
        self.logger.info("Cleared cache for all filters in chain")
