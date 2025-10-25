# Pattern Detection Module

**Week 2 Implementation - 10 Pattern Detection Rules**
**Epic AI-1 Enhanced Implementation**
**Created:** October 25, 2025

---

## Overview

This module implements a comprehensive pattern detection framework for Home Assistant automation. It analyzes 30 days of event data to identify recurring behavioral patterns using 10 specialized rule-based detectors.

## Architecture

### Three-File Structure

1. **`pattern_types.py`** - Core data models
   - `PatternType` enum - 10 pattern types
   - `PatternResult` dataclass - Standardized pattern output

2. **`pattern_detector.py`** - Abstract base class
   - `PatternDetector` - Base class for all detectors
   - Common confidence calculation logic
   - Threshold filtering

3. **`detectors.py`** - 10 specialized detector implementations
   - Each detector inherits from `PatternDetector`
   - Implements `detect()` method
   - Returns list of `PatternResult` objects

---

## The 10 Pattern Detectors

### 1. TimeOfDayDetector
**Purpose:** Detect devices that activate at consistent times daily

**Example Pattern:**
- Bedroom light turns on at 7:15 AM every day (±15 min variance)

**Parameters:**
- `min_occurrences`: Minimum times pattern must occur (default: 5)
- `min_confidence`: Minimum confidence score (default: 0.7)
- `time_window_minutes`: Clustering tolerance (default: 30)

**Algorithm:**
- Groups events by entity_id
- Uses DBSCAN clustering on time-of-day
- Calculates consistency from time variance

---

### 2. CoOccurrenceDetector
**Purpose:** Find devices that frequently activate together

**Example Pattern:**
- Living room light and kitchen light turn on within 5 minutes

**Parameters:**
- `window_minutes`: Time window for co-occurrence (default: 5)

**Algorithm:**
- Sliding window approach
- Tracks device pairs within time window
- Calculates time delta statistics

---

### 3. SequenceDetector
**Purpose:** Detect sequential activation patterns (A → B → C)

**Example Pattern:**
- Morning routine: Coffee maker → Bathroom light → Kitchen light

**Parameters:**
- `sequence_length`: Number of devices in sequence (default: 3)
- `max_gap_minutes`: Maximum time between steps (default: 15)

**Algorithm:**
- Sliding window over sorted events
- Identifies repeated sequences
- Tracks sequence frequency

---

### 4. ContextualDetector
**Purpose:** Find patterns tied to external context

**Context Types:**
- **Sun position:** Activations at sunrise/sunset
- **Weather:** Temperature-based patterns
- **Occupancy:** Home/away patterns

**Example Patterns:**
- Porch light activates at sunset
- Heater turns on when temp < 65°F
- Security system arms when leaving home

---

### 5. DurationDetector
**Purpose:** Detect consistent state durations

**Example Pattern:**
- Office light stays on for 2 hours (±15 min)

**Algorithm:**
- Calculates time between state changes
- Groups by state value
- Identifies consistent durations

---

### 6. DayTypeDetector
**Purpose:** Distinguish weekday vs weekend patterns

**Example Patterns:**
- Alarm activates weekdays only
- Coffee maker starts at 9 AM on weekends

**Parameters:**
- Ratio threshold for day type dominance (default: 0.7 = 70%)

---

### 7. RoomBasedDetector
**Purpose:** Find multi-device room-level patterns

**Example Pattern:**
- Bedroom: 3 devices (light, fan, blinds) activate together

**Parameters:**
- `window_minutes`: Co-activation window (default: 10)

**Algorithm:**
- Groups events by area
- Finds device combinations within window
- Identifies room-level automations

---

### 8. SeasonalDetector
**Purpose:** Detect seasonal behavior changes

**Seasons:**
- Winter: Dec-Feb
- Spring: Mar-May
- Summer: Jun-Aug
- Fall: Sep-Nov

**Example Pattern:**
- Space heater only used in winter

---

### 9. AnomalyDetector
**Purpose:** Find unusual patterns (security, diagnostics)

**Example Patterns:**
- Door opens at 3 AM (unusual time)
- Device activates 50x more than normal

**Parameters:**
- `sensitivity`: Standard deviations for anomaly (default: 2.0)

**Algorithm:**
- Calculates normal behavior statistics
- Flags outliers beyond threshold

---

### 10. FrequencyDetector
**Purpose:** Detect consistent activation frequency

**Frequency Types:**
- Hourly: < 2 hour interval
- Daily: 2-30 hour interval
- Weekly: > 30 hour interval

**Example Pattern:**
- Weather sensor updates every 60 minutes

---

## Usage

### Basic Example

```python
from pattern_detection import TimeOfDayDetector
import pandas as pd

# Load event data
events_df = pd.read_csv('events.csv')

# Create detector
detector = TimeOfDayDetector(
    min_occurrences=5,
    min_confidence=0.7
)

# Detect patterns
patterns = detector.detect_and_filter(events_df)

# Process results
for pattern in patterns:
    print(f"{pattern.entity_id} at {pattern.hour}:{pattern.minute:02d}")
    print(f"Confidence: {pattern.confidence:.0%}")
    print(f"Occurrences: {pattern.occurrences}")
```

### Using All Detectors

```python
from pattern_detection import (
    TimeOfDayDetector,
    CoOccurrenceDetector,
    DayTypeDetector
    # ... import others
)

# Create all detectors
detectors = [
    TimeOfDayDetector(),
    CoOccurrenceDetector(),
    SequenceDetector(),
    ContextualDetector(),
    DurationDetector(),
    DayTypeDetector(),
    RoomBasedDetector(),
    SeasonalDetector(),
    AnomalyDetector(),
    FrequencyDetector()
]

# Run all detectors
all_patterns = []
for detector in detectors:
    patterns = detector.detect_and_filter(events_df)
    all_patterns.extend(patterns)

print(f"Total patterns found: {len(all_patterns)}")
```

---

## Data Requirements

### Required Columns

**Minimum:**
- `entity_id` (str) - Home Assistant entity ID
- `timestamp` (datetime) - Event timestamp
- `state` (str) - Device state

**Optional (enables more detectors):**
- `area` (str) - Room/area name
- `sun_elevation` (float) - Sun position
- `temperature` (float) - Weather temperature
- `occupancy` (str) - Home/away status

### Example DataFrame

```python
import pandas as pd
from datetime import datetime

events_df = pd.DataFrame([
    {
        'entity_id': 'light.bedroom',
        'timestamp': datetime(2025, 1, 1, 7, 15),
        'state': 'on',
        'area': 'Bedroom'
    },
    {
        'entity_id': 'light.kitchen',
        'timestamp': datetime(2025, 1, 1, 18, 30),
        'state': 'on',
        'area': 'Kitchen',
        'temperature': 72.5,
        'occupancy': 'home'
    }
])
```

---

## Pattern Result Schema

Every detector returns `PatternResult` objects with:

```python
PatternResult(
    pattern_type: PatternType,         # Enum (TIME_OF_DAY, etc.)
    confidence: float,                 # 0.0-1.0
    entity_id: Optional[str],          # Single entity
    entities: Optional[List[str]],     # Multiple entities
    description: str,                  # Human-readable
    hour: Optional[int],               # 0-23
    minute: Optional[int],             # 0-59
    day_of_week: Optional[str],        # weekday/weekend
    season: Optional[str],             # winter/spring/summer/fall
    occurrences: int,                  # Count
    avg_value: Optional[float],        # Average metric
    std_dev: Optional[float],          # Standard deviation
    area: Optional[str],               # Room/area
    metadata: Dict[str, Any]           # Additional data
)
```

### Converting to Dictionary

```python
pattern_dict = pattern.to_dict()
# {'pattern_type': 'time_of_day', 'confidence': 0.85, ...}

# Restore from dict
pattern = PatternResult.from_dict(pattern_dict)
```

---

## Confidence Calculation

All detectors use a weighted confidence formula:

```python
confidence = (0.6 × frequency_score) + (0.4 × consistency_score)
```

**Where:**
- `frequency_score = occurrences / total_possible`
- `consistency_score` = detector-specific metric (time variance, ratio, etc.)

**Thresholds:**
- Patterns below `min_occurrences` are filtered out
- Patterns below `min_confidence` are filtered out

---

## Integration with Daily Analysis

The pattern detection module integrates with the daily analysis scheduler:

**File:** `services/ai-automation-service/src/scheduler/daily_analysis.py`

```python
# Phase 3: Pattern Detection
from pattern_detection import TimeOfDayDetector, CoOccurrenceDetector

tod_detector = TimeOfDayDetector(min_occurrences=5, min_confidence=0.7)
co_detector = CoOccurrenceDetector(window_minutes=5, min_occurrences=5)

tod_patterns = tod_detector.detect_and_filter(events_df)
co_patterns = co_detector.detect_and_filter(events_df)

all_patterns = tod_patterns + co_patterns
```

---

## Testing

### Run Tests

```bash
cd services/ai-automation-service
pytest tests/test_pattern_detectors.py -v
```

### Test Coverage

Each detector has:
- Unit tests with synthetic data
- Integration tests with realistic patterns
- Edge case handling tests

**Test File:** `tests/test_pattern_detectors.py`

---

## Performance Considerations

### Optimization Tips

1. **Pre-filter events** - Remove irrelevant entities before detection
2. **Batch processing** - Process 30 days of data once daily, not real-time
3. **Parallel detection** - Detectors are independent, can run in parallel
4. **Database indexing** - Index on entity_id, timestamp for fast queries

### Expected Performance

- **10,000 events:** ~2-5 seconds for all 10 detectors
- **100,000 events:** ~15-30 seconds (with optimizations)

### Memory Usage

- **Events DataFrame:** ~100KB per 1000 events
- **Pattern storage:** ~1KB per pattern
- **Total:** < 10MB for typical 30-day dataset

---

## Extending the Framework

### Creating a Custom Detector

```python
from pattern_detection import PatternDetector, PatternResult, PatternType

class MyCustomDetector(PatternDetector):
    def _get_pattern_type(self) -> PatternType:
        return PatternType.CUSTOM  # Add to enum first

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        patterns = []

        # Your detection logic here

        return patterns

# Use it
detector = MyCustomDetector(min_occurrences=3)
patterns = detector.detect_and_filter(events_df)
```

---

## Troubleshooting

### Common Issues

**1. No patterns detected**
- Check `min_occurrences` threshold (try lowering)
- Verify events_df has required columns
- Ensure sufficient data (at least 7-14 days)

**2. Low confidence scores**
- Patterns may be inconsistent in timing
- Try increasing `time_window_minutes` for time-based detectors
- Check data quality (missing timestamps, incorrect entity_ids)

**3. Too many patterns**
- Increase `min_confidence` threshold
- Filter by specific entity_ids before detection
- Use pattern ranking/scoring

---

## Dependencies

Required packages (from `requirements.txt`):

```txt
pandas==2.1.4
numpy==1.26.2
scikit-learn==1.3.2  # For DBSCAN clustering
```

---

## Future Enhancements

**Planned for Week 3-4:**
- Pattern composition (combine simple patterns into complex ones)
- ML-based pattern validation
- Priority scoring and ranking
- Pattern clustering (find similar patterns)
- Automatic categorization (energy/comfort/security/convenience)

---

## References

- **Implementation Plan:** `/implementation/AI_PATTERN_DETECTION_IMPLEMENTATION_PLAN.md`
- **Epic AI-1:** `/docs/stories/epic-ai1-summary.md`
- **Week 2 Roadmap:** `/implementation/ENHANCED_EPIC_AI1_ROADMAP.md`

---

**Version:** 1.0
**Status:** ✅ Complete - Ready for Integration
**Next Steps:** Integrate with daily analysis scheduler, add pattern composition
