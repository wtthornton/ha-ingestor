"""Entity-based filter for Home Assistant events with regex pattern support."""

import re
from typing import List, Optional, Union, Pattern, Dict, Any
from .base import Filter
from ..models.events import Event

class EntityFilter(Filter):
    """Filter events based on entity ID patterns with regex support."""
    
    def __init__(self, patterns: Union[List[str], str], name: str = None, use_regex: bool = True):
        """Initialize entity filter.
        
        Args:
            patterns: List of entity ID patterns to allow, or single pattern string
            name: Optional name for the filter
            use_regex: Whether to treat patterns as regex (default: True)
        """
        super().__init__(name or f"entity_filter_{'_'.join(self._normalize_patterns(patterns))}")
        
        self.use_regex = use_regex
        self.patterns = self._normalize_patterns(patterns)
        
        # Compile regex patterns for performance
        self._compiled_patterns = self._compile_patterns()
        
        # Pattern optimization cache for frequently used patterns
        self._pattern_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        self.logger.info("Entity filter initialized", 
                        patterns=self.patterns,
                        use_regex=use_regex,
                        total_patterns=len(self.patterns))
    
    def _normalize_patterns(self, patterns: Union[List[str], str]) -> List[str]:
        """Normalize patterns input to a list.
        
        Args:
            patterns: Input patterns (string or list)
            
        Returns:
            Normalized list of patterns
        """
        if isinstance(patterns, str):
            return [patterns]
        elif isinstance(patterns, list):
            return [str(pattern).strip() for pattern in patterns if pattern]
        else:
            raise ValueError("patterns must be a string or list of strings")
    
    def _compile_patterns(self) -> List[Pattern]:
        """Compile regex patterns for efficient matching.
        
        Returns:
            List of compiled regex patterns
        """
        compiled = []
        for pattern in self.patterns:
            try:
                if self.use_regex:
                    # Compile regex pattern
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                else:
                    # Convert glob pattern to regex
                    regex_pattern = self._glob_to_regex(pattern)
                    compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
                
                compiled.append(compiled_pattern)
                
            except re.error as e:
                self.logger.warning("Invalid regex pattern, skipping", 
                                  pattern=pattern, error=str(e))
                # Create a pattern that never matches
                compiled.append(re.compile(r'(?!)'))
        
        return compiled
    
    def _glob_to_regex(self, glob_pattern: str) -> str:
        """Convert glob pattern to regex pattern.
        
        Args:
            glob_pattern: Glob pattern (e.g., "light.*", "sensor.temp_*")
            
        Returns:
            Regex pattern string
        """
        # Escape special regex characters
        pattern = re.escape(glob_pattern)
        
        # Convert glob wildcards to regex
        pattern = pattern.replace(r'\*', '.*')  # * -> .*
        pattern = pattern.replace(r'\?', '.')   # ? -> .
        
        # Add start/end anchors
        return f"^{pattern}$"
    
    async def should_process(self, event: Event) -> bool:
        """Check if event entity ID matches any of the patterns.
        
        Args:
            event: The event to check
            
        Returns:
            True if entity ID matches a pattern, False otherwise
        """
        if not event.entity_id:
            self.logger.debug("Event has no entity ID, filtering out")
            return False
        
        # Check pattern cache first for performance
        cache_key = event.entity_id
        if cache_key in self._pattern_cache:
            self._cache_hits += 1
            return self._pattern_cache[cache_key]
        
        self._cache_misses += 1
        
        # Check if entity ID matches any pattern
        for pattern in self._compiled_patterns:
            if pattern.search(event.entity_id):
                # Cache positive result
                self._pattern_cache[cache_key] = True
                
                # Limit cache size to prevent memory issues
                if len(self._pattern_cache) > 1000:
                    # Remove oldest entries (simple LRU-like behavior)
                    oldest_keys = list(self._pattern_cache.keys())[:100]
                    for key in oldest_keys:
                        del self._pattern_cache[key]
                
                self.logger.debug("Entity ID matches pattern", 
                                entity_id=event.entity_id,
                                pattern=pattern.pattern)
                return True
        
        # Cache negative result
        self._pattern_cache[cache_key] = False
        
        # Limit cache size
        if len(self._pattern_cache) > 1000:
            oldest_keys = list(self._pattern_cache.keys())[:100]
            for key in oldest_keys:
                del self._pattern_cache[key]
        
        self.logger.debug("Entity ID filtered out", 
                         entity_id=event.entity_id,
                         patterns=self.patterns)
        return False
    
    def add_pattern(self, pattern: str) -> None:
        """Add a pattern to the filter.
        
        Args:
            pattern: Pattern to add
        """
        normalized_pattern = pattern.strip()
        if normalized_pattern and normalized_pattern not in self.patterns:
            self.patterns.append(normalized_pattern)
            
            # Compile and add the new pattern
            try:
                if self.use_regex:
                    compiled_pattern = re.compile(normalized_pattern, re.IGNORECASE)
                else:
                    regex_pattern = self._glob_to_regex(normalized_pattern)
                    compiled_pattern = re.compile(regex_pattern, re.IGNORECASE)
                
                self._compiled_patterns.append(compiled_pattern)
                
                self.logger.info("Added pattern to filter", 
                               pattern=normalized_pattern,
                               total_patterns=len(self.patterns))
                
            except re.error as e:
                self.logger.error("Failed to compile pattern", 
                                pattern=normalized_pattern, error=str(e))
                # Remove the invalid pattern
                self.patterns.remove(normalized_pattern)
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove a pattern from the filter.
        
        Args:
            pattern: Pattern to remove
            
        Returns:
            True if pattern was removed, False if not found
        """
        normalized_pattern = pattern.strip()
        if normalized_pattern in self.patterns:
            # Find and remove the pattern and its compiled version
            index = self.patterns.index(normalized_pattern)
            self.patterns.pop(index)
            self._compiled_patterns.pop(index)
            
            self.logger.info("Removed pattern from filter", 
                           pattern=normalized_pattern,
                           total_patterns=len(self.patterns))
            return True
        return False
    
    def get_patterns(self) -> List[str]:
        """Get list of patterns.
        
        Returns:
            List of patterns
        """
        return self.patterns.copy()
    
    def is_entity_allowed(self, entity_id: str) -> bool:
        """Check if a specific entity ID would be allowed.
        
        Args:
            entity_id: Entity ID to check
            
        Returns:
            True if entity ID would be allowed, False otherwise
        """
        if not entity_id:
            return False
        
        for pattern in self._compiled_patterns:
            if pattern.search(entity_id):
                return True
        return False
    
    def clear_cache(self) -> None:
        """Clear the filter's cache and recompile patterns."""
        super().clear_cache()
        self._compiled_patterns = self._compile_patterns()
        self._pattern_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self.logger.info("Recompiled patterns after cache clear")
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern optimization statistics.
        
        Returns:
            Dictionary with pattern optimization statistics
        """
        return {
            "pattern_cache_size": len(self._pattern_cache),
            "pattern_cache_hits": self._cache_hits,
            "pattern_cache_misses": self._cache_misses,
            "pattern_cache_hit_rate": self._cache_hits / max(self._cache_hits + self._cache_misses, 1),
            "total_patterns": len(self.patterns),
            "compiled_patterns": len(self._compiled_patterns)
        }
