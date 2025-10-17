"""
ProcessedEvents Data Structures
Standardized event representation with all features pre-extracted
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import numpy as np


@dataclass
class ProcessedEvent:
    """
    Single event with all features pre-extracted
    Foundation for all pattern detectors
    
    This standardized structure ensures:
    - Features extracted once (not per detector)
    - Consistent feature definitions
    - Easy to extend (add new feature, all detectors get it)
    - ML-ready (embeddings included)
    """
    
    # ============================================================================
    # CORE IDENTITY
    # ============================================================================
    event_id: str
    timestamp: datetime
    device_id: str
    entity_id: str
    
    # ============================================================================
    # DEVICE METADATA (from data-api)
    # ============================================================================
    device_name: str
    device_type: str  # light, switch, sensor, climate, etc.
    area: Optional[str] = None  # bedroom, kitchen, living_room
    floor: Optional[int] = None
    
    # ============================================================================
    # STATE INFORMATION
    # ============================================================================
    old_state: Any = None
    new_state: Any = None
    state_duration: float = 0.0  # seconds in previous state
    state_change_type: Optional[str] = None  # on_to_off, brightness_change, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # ============================================================================
    # TEMPORAL FEATURES (auto-extracted)
    # ============================================================================
    hour: int = 0  # 0-23
    minute: int = 0  # 0-59
    day_of_week: int = 0  # 0=Monday, 6=Sunday
    day_type: str = 'weekday'  # 'weekday' or 'weekend'
    season: str = 'spring'  # 'spring', 'summer', 'fall', 'winter'
    time_of_day: str = 'morning'  # 'morning', 'afternoon', 'evening', 'night'
    
    # ============================================================================
    # CONTEXTUAL FEATURES (from sensors/API)
    # ============================================================================
    sun_elevation: Optional[float] = None
    is_sunrise: bool = False
    is_sunset: bool = False
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    occupancy_state: Optional[str] = None  # 'home', 'away'
    
    # ============================================================================
    # SESSION FEATURES (for sequence detection)
    # ============================================================================
    session_id: Optional[str] = None
    event_index_in_session: int = 0
    session_device_count: int = 0
    time_from_prev_event: Optional[float] = None  # seconds
    
    # ============================================================================
    # EMBEDDING (from model - ML-ready)
    # ============================================================================
    embedding: Optional[np.ndarray] = None  # (384,) array from all-MiniLM-L6-v2
    
    # ============================================================================
    # METADATA
    # ============================================================================
    processed_at: datetime = field(default_factory=datetime.utcnow)
    processing_version: str = '1.0'
    
    def to_text(self) -> str:
        """
        Convert to natural language for embedding generation
        """
        return (
            f"{self.device_name} {self.state_change_type or 'changes'} "
            f"at {self.hour:02d}:{self.minute:02d} on {self.day_type}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (for JSON storage)"""
        data = {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'entity_id': self.entity_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'area': self.area,
            'hour': self.hour,
            'minute': self.minute,
            'day_type': self.day_type,
            'season': self.season,
            'time_of_day': self.time_of_day,
            'session_id': self.session_id,
        }
        
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        
        return data


@dataclass
class ProcessedEvents:
    """
    Collection of processed events with metadata and indices
    Optimized for fast pattern detection
    """
    
    events: List[ProcessedEvent]
    
    # Indices for fast lookup
    device_index: Dict[str, List[ProcessedEvent]] = field(default_factory=dict)
    temporal_index: Dict[int, List[ProcessedEvent]] = field(default_factory=dict)  # by hour
    session_index: Dict[str, List[ProcessedEvent]] = field(default_factory=dict)
    
    # Metadata
    total_events: int = 0
    unique_devices: int = 0
    unique_sessions: int = 0
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    processing_time_seconds: float = 0.0
    
    def __post_init__(self):
        """Build indices after initialization"""
        self.total_events = len(self.events)
        
        # Build device index
        for event in self.events:
            if event.device_id not in self.device_index:
                self.device_index[event.device_id] = []
            self.device_index[event.device_id].append(event)
        
        self.unique_devices = len(self.device_index)
        
        # Build temporal index (by hour)
        for event in self.events:
            if event.hour not in self.temporal_index:
                self.temporal_index[event.hour] = []
            self.temporal_index[event.hour].append(event)
        
        # Build session index
        for event in self.events:
            if event.session_id and event.session_id not in self.session_index:
                self.session_index[event.session_id] = []
            if event.session_id:
                self.session_index[event.session_id].append(event)
        
        self.unique_sessions = len(self.session_index)
        
        # Date range
        if self.events:
            timestamps = [e.timestamp for e in self.events]
            self.date_range_start = min(timestamps)
            self.date_range_end = max(timestamps)
    
    def get_events_by_device(self, device_id: str) -> List[ProcessedEvent]:
        """Fast lookup by device"""
        return self.device_index.get(device_id, [])
    
    def get_events_by_hour(self, hour: int) -> List[ProcessedEvent]:
        """Fast lookup by hour"""
        return self.temporal_index.get(hour, [])
    
    def get_events_in_session(self, session_id: str) -> List[ProcessedEvent]:
        """Fast lookup by session"""
        return self.session_index.get(session_id, [])
    
    def to_summary(self) -> Dict[str, Any]:
        """Get preprocessing summary"""
        return {
            'total_events': self.total_events,
            'unique_devices': self.unique_devices,
            'unique_sessions': self.unique_sessions,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'processing_time_seconds': self.processing_time_seconds
        }

