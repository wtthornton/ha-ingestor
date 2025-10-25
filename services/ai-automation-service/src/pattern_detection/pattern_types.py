"""
Pattern Types and Result Models

Week 2 Implementation - Pattern Detection Framework
Epic AI-1, Enhanced Implementation
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


class PatternType(Enum):
    """Types of detectable patterns in Home Assistant events"""

    TIME_OF_DAY = "time_of_day"
    CO_OCCURRENCE = "co_occurrence"
    SEQUENCE = "sequence"
    CONTEXTUAL = "contextual"
    DURATION = "duration"
    DAY_TYPE = "day_type"
    ROOM_BASED = "room_based"
    SEASONAL = "seasonal"
    ANOMALY = "anomaly"
    FREQUENCY = "frequency"


@dataclass
class PatternResult:
    """
    Standardized pattern detection result

    All detectors return this structure for consistency
    """

    pattern_type: PatternType
    confidence: float  # 0.0-1.0
    entity_id: Optional[str] = None
    entities: Optional[List[str]] = None  # For multi-entity patterns
    description: str = ""
    metadata: Dict[str, Any] = None

    # Time information
    hour: Optional[int] = None
    minute: Optional[int] = None
    day_of_week: Optional[str] = None
    season: Optional[str] = None

    # Pattern-specific data
    occurrences: int = 0
    avg_value: Optional[float] = None
    std_dev: Optional[float] = None

    # Additional context
    area: Optional[str] = None
    device_class: Optional[str] = None

    def __post_init__(self):
        """Initialize metadata if not provided"""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/API"""
        return {
            'pattern_type': self.pattern_type.value,
            'confidence': self.confidence,
            'entity_id': self.entity_id,
            'entities': self.entities,
            'description': self.description,
            'metadata': self.metadata,
            'hour': self.hour,
            'minute': self.minute,
            'day_of_week': self.day_of_week,
            'season': self.season,
            'occurrences': self.occurrences,
            'avg_value': self.avg_value,
            'std_dev': self.std_dev,
            'area': self.area,
            'device_class': self.device_class
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatternResult':
        """Create from dictionary"""
        data = data.copy()
        data['pattern_type'] = PatternType(data['pattern_type'])
        return cls(**data)
