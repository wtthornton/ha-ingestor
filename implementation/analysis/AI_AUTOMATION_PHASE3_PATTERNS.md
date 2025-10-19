# Phase 3: Pattern Detection
## Epic AI-1 - Pattern Detection & Automation Suggestions

**Epic:** AI-1 - Pattern Detection & Automation Suggestions  
**Duration:** 15-45 seconds  
**Database:** SQLite (`patterns` table)  
**Last Updated:** October 17, 2025  
**Last Validated:** October 19, 2025 ✅

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 2 - Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md)
- [→ Next: Phase 4 - Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md)

---

## 📋 Overview

**Purpose:** Detect time-of-day and co-occurrence patterns from event history

Phase 3 analyzes the historical events (from Phase 2) to discover:
1. **Time-of-Day Patterns:** Devices that activate consistently at the same time
2. **Co-Occurrence Patterns:** Devices that are frequently activated together

These patterns become the foundation for AI-generated automation suggestions in Phase 5.

---

## 🔄 Call Tree

```
run_daily_analysis() [line 203]
├── Time-of-Day Pattern Detection [line 208]
│   ├── TimeOfDayPatternDetector.__init__() [pattern_analyzer/time_of_day.py]
│   │   ├── min_occurrences = 5
│   │   └── min_confidence = 0.7
│   │
│   └── tod_detector.detect_patterns(events_df) [time_of_day.py:~50]
│       ├── Group events by (entity_id, hour)
│       ├── Calculate frequency and confidence
│       ├── Filter by min_occurrences and min_confidence
│       └── Returns: List[Dict] with pattern metadata:
│           - pattern_type: 'time_of_day'
│           - device_id
│           - hour, minute
│           - occurrences
│           - confidence
│           - last_seen
│
├── Co-Occurrence Pattern Detection [line 221]
│   ├── CoOccurrencePatternDetector.__init__() [pattern_analyzer/co_occurrence.py]
│   │   ├── window_minutes = 5
│   │   ├── min_support = 5
│   │   └── min_confidence = 0.7
│   │
│   ├── IF len(events_df) > 50,000:
│   │   └── co_detector.detect_patterns_optimized(events_df) [co_occurrence.py:~150]
│   │       ├── Optimized sliding window algorithm
│   │       ├── Hash-based lookups for performance
│   │       └── Returns: List[Dict] co-occurrence patterns
│   │
│   └── ELSE:
│       └── co_detector.detect_patterns(events_df) [co_occurrence.py:~80]
│           ├── Standard sliding window (O(n²))
│           ├── Find events within time window
│           ├── Calculate support and confidence
│           └── Returns: List[Dict] with pattern metadata:
│               - pattern_type: 'co_occurrence'
│               - trigger_device_id
│               - target_device_id
│               - time_window_minutes
│               - support
│               - confidence
│
├── Combine all_patterns = tod_patterns + co_patterns [line 233]
│
└── store_patterns() [line 241]
    ├── database/crud.py:store_patterns()
    │   ├── For each pattern:
    │   │   ├── Pattern.from_dict()
    │   │   └── db.add(pattern)
    │   │
    │   └── db.commit()
    │
    └── Returns: patterns_stored (int)
```

**Key Files:**
- `pattern_analyzer/time_of_day.py` - Time-based pattern detection
- `pattern_analyzer/co_occurrence.py` - Sequential event pattern detection
- `database/crud.py` - Database storage operations

**Database Impact:** Inserts into `patterns` table (SQLite)  
**Performance:** Optimized path for >50K events using hash-based algorithms

---

## 🕐 Time-of-Day Pattern Detection

### Algorithm

**Purpose:** Find devices that consistently activate at the same time each day

**Process:**
1. Group events by `(entity_id, hour_of_day)`
2. Count occurrences in 30-day window
3. Calculate confidence score: `occurrences / total_days`
4. Filter patterns by thresholds:
   - Minimum occurrences: 5
   - Minimum confidence: 0.7 (70%)

**Example Pattern:**
```python
{
    'pattern_type': 'time_of_day',
    'entity_id': 'light.living_room',
    'device_id': 'abc123',
    'hour': 7,
    'minute': 15,
    'occurrences': 26,  # Activated 26 times in last 30 days
    'confidence': 0.87,  # 87% regularity
    'last_seen': '2025-10-17T07:15:00Z'
}
```

**Interpretation:** The living room light turns on at 7:15 AM on 87% of days (26 out of 30 days).

---

## 🔗 Co-Occurrence Pattern Detection

### Algorithm

**Purpose:** Find devices that are frequently activated together within a time window

**Process:**
1. Use sliding window algorithm (5-minute window)
2. For each event A, find events B within window
3. Count co-occurrences
4. Calculate support and confidence:
   - **Support:** How often A and B occur together
   - **Confidence:** P(B|A) - When A happens, probability B follows

**Example Pattern:**
```python
{
    'pattern_type': 'co_occurrence',
    'trigger_entity_id': 'light.kitchen',
    'target_entity_id': 'media_player.kitchen_speaker',
    'trigger_device_id': 'device_1',
    'target_device_id': 'device_2',
    'time_window_minutes': 5,
    'occurrences': 18,  # Happened together 18 times
    'support': 18,
    'confidence': 0.75,  # 75% of the time kitchen light → speaker
    'avg_time_delta_seconds': 45,  # Average 45s between activations
    'last_seen': '2025-10-17T18:30:00Z'
}
```

**Interpretation:** When kitchen light turns on, the kitchen speaker also turns on within 5 minutes, 75% of the time (typically 45 seconds later).

---

## ⚡ Performance Optimization

### Standard vs Optimized Algorithm

**Standard Algorithm (< 50K events):**
```python
# O(n²) sliding window
for event_a in events:
    for event_b in events:
        if is_within_window(event_a, event_b):
            count_co_occurrence(event_a, event_b)
```
- **Complexity:** O(n²)
- **Time:** ~15-30s for 50K events
- **Use Case:** Small to medium datasets

**Optimized Algorithm (>50K events):**
```python
# Hash-based lookups with time indexing
time_index = build_time_index(events)  # O(n)
for event_a in events:
    candidates = time_index.get_window(event_a.time, window=5min)  # O(log n)
    for event_b in candidates:
        count_co_occurrence(event_a, event_b)  # O(k) where k << n
```
- **Complexity:** O(n log n)
- **Time:** ~20-45s for 100K events
- **Speedup:** 3-5x faster than standard
- **Automatic:** Switches automatically if `len(events_df) > 50,000`

---

## 📊 Pattern Storage

### Database Schema

**SQLite Table: `patterns`**

```sql
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type VARCHAR NOT NULL,  -- 'time_of_day' or 'co_occurrence'
    entity_id VARCHAR,  -- For time_of_day patterns
    device_id VARCHAR,
    trigger_entity_id VARCHAR,  -- For co_occurrence patterns
    target_entity_id VARCHAR,
    metadata JSON NOT NULL,  -- Pattern-specific data
    confidence FLOAT NOT NULL,
    occurrences INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    last_seen DATETIME NOT NULL
);
```

**Metadata Field Contents:**

**Time-of-Day Pattern:**
```json
{
  "hour": 7,
  "minute": 15,
  "weekday_pattern": [true, true, true, true, true, false, false]  // Mon-Fri only
}
```

**Co-Occurrence Pattern:**
```json
{
  "time_window_minutes": 5,
  "avg_time_delta_seconds": 45.2,
  "support": 18,
  "trigger_state": "on",
  "target_state": "on"
}
```

---

## 🎯 Phase 3 Output

**Typical Results:**
```python
{
    'time_of_day_patterns': 15,
    'co_occurrence_patterns': 8,
    'total_patterns': 23,
    'patterns_stored': 23
}
```

**Example Detected Patterns:**
1. Living room light at 7:15 AM (confidence: 0.87)
2. Bedroom light at 10:30 PM (confidence: 0.92)
3. Coffee maker at 6:45 AM on weekdays (confidence: 0.81)
4. Kitchen light → Kitchen speaker within 5min (confidence: 0.75)
5. Front door lock → Entry light within 2min (confidence: 0.88)

---

## ⚠️ Error Handling

**Pattern Detection Errors:**

```python
try:
    patterns = detector.detect_patterns(events_df)
except Exception as e:
    logger.error(f"Pattern detection failed: {e}")
    patterns = []  # Empty list, don't fail entire job
```

**Storage Errors:**

```python
try:
    await store_patterns(db, patterns)
except Exception as e:
    logger.error(f"Pattern storage failed: {e}")
    # Patterns lost, but job continues
```

**Graceful Degradation:**
- If pattern detection fails, Phase 5 can still generate feature-based suggestions (Epic AI-2)
- Job continues even if zero patterns detected
- Next run (24 hours later) will retry

---

## 🔗 Next Steps

**Phase 3 Output Used By:**
- [Phase 5: OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md) - Converts patterns to automations

**Related Phases:**
- [Phase 2: Historical Event Fetching](AI_AUTOMATION_PHASE2_EVENTS.md) - Provides input data
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md) - Parallel analysis path
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** AI-1 - Pattern Detection

