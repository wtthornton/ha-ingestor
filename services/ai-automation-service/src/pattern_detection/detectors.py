"""
Pattern Detector Implementations

Week 2 Implementation - 10 Pattern Detection Rules
Epic AI-1, Enhanced Implementation

All detectors inherit from PatternDetector base class
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import time, timedelta
from collections import Counter, defaultdict
from sklearn.cluster import DBSCAN

from .pattern_detector import PatternDetector
from .pattern_types import PatternResult, PatternType

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. Time of Day Detector
# ==============================================================================

class TimeOfDayDetector(PatternDetector):
    """
    Detect consistent time-of-day patterns

    Finds devices that activate at similar times daily
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7,
        time_window_minutes: int = 30
    ):
        super().__init__(min_occurrences, min_confidence)
        self.time_window_minutes = time_window_minutes

    def _get_pattern_type(self) -> PatternType:
        return PatternType.TIME_OF_DAY

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect time-of-day patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        # Ensure timestamp column
        if 'timestamp' in events_df.columns:
            events_df['hour'] = pd.to_datetime(events_df['timestamp']).dt.hour
            events_df['minute'] = pd.to_datetime(events_df['timestamp']).dt.minute
        elif 'hour' not in events_df.columns:
            return patterns

        # Group by entity
        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences:
                continue

            # Cluster by time
            time_clusters = self._cluster_by_time(entity_events)

            for cluster_time, cluster_events in time_clusters.items():
                hour, minute = cluster_time
                occurrences = len(cluster_events)

                if occurrences < self.min_occurrences:
                    continue

                # Calculate consistency
                time_variance = cluster_events['minute'].std()
                consistency = 1.0 - min(time_variance / 30.0, 1.0)

                confidence = self._calculate_confidence(
                    occurrences=occurrences,
                    total_possible=len(entity_events),
                    consistency_score=consistency
                )

                patterns.append(PatternResult(
                    pattern_type=PatternType.TIME_OF_DAY,
                    confidence=confidence,
                    entity_id=entity_id,
                    hour=hour,
                    minute=minute,
                    occurrences=occurrences,
                    description=f"{entity_id} activates around {hour:02d}:{minute:02d}",
                    metadata={
                        'time_variance_minutes': time_variance,
                        'consistency_score': consistency
                    }
                ))

        return patterns

    def _cluster_by_time(
        self,
        events: pd.DataFrame
    ) -> Dict[Tuple[int, int], pd.DataFrame]:
        """Cluster events by similar time using DBSCAN"""
        if events.empty:
            return {}

        # Convert time to minutes since midnight
        events['minutes_since_midnight'] = events['hour'] * 60 + events['minute']

        # Cluster times within time_window
        time_values = events[['minutes_since_midnight']].values

        if len(time_values) < 2:
            # Single event - use its time
            hour = int(events.iloc[0]['hour'])
            minute = int(events.iloc[0]['minute'])
            return {(hour, minute): events}

        clustering = DBSCAN(
            eps=self.time_window_minutes,
            min_samples=self.min_occurrences
        ).fit(time_values)

        # Group by cluster
        clusters = {}
        for label in set(clustering.labels_):
            if label == -1:  # Noise
                continue

            cluster_events = events[clustering.labels_ == label]
            avg_minutes = int(cluster_events['minutes_since_midnight'].mean())
            hour = avg_minutes // 60
            minute = avg_minutes % 60

            clusters[(hour, minute)] = cluster_events

        return clusters


# ==============================================================================
# 2. Co-Occurrence Detector
# ==============================================================================

class CoOccurrenceDetector(PatternDetector):
    """
    Detect devices that frequently activate together

    Finds pairs of devices used within a time window
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7,
        window_minutes: int = 5
    ):
        super().__init__(min_occurrences, min_confidence)
        self.window_minutes = window_minutes

    def _get_pattern_type(self) -> PatternType:
        return PatternType.CO_OCCURRENCE

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect co-occurrence patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        # Ensure timestamp
        if 'timestamp' not in events_df.columns:
            return patterns

        events_df = events_df.copy()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df = events_df.sort_values('timestamp')

        # Find co-occurrences
        window = timedelta(minutes=self.window_minutes)
        co_occurrences = defaultdict(list)

        for i, event1 in events_df.iterrows():
            entity1 = event1['entity_id']
            time1 = event1['timestamp']

            # Look ahead within window
            future_events = events_df[
                (events_df['timestamp'] > time1) &
                (events_df['timestamp'] <= time1 + window)
            ]

            for _, event2 in future_events.iterrows():
                entity2 = event2['entity_id']

                if entity1 != entity2:
                    pair = tuple(sorted([entity1, entity2]))
                    time_delta = (event2['timestamp'] - time1).total_seconds()
                    co_occurrences[pair].append(time_delta)

        # Create patterns
        for (entity1, entity2), deltas in co_occurrences.items():
            occurrences = len(deltas)

            if occurrences < self.min_occurrences:
                continue

            avg_delta = np.mean(deltas)
            std_delta = np.std(deltas)
            consistency = 1.0 - min(std_delta / 60.0, 1.0)  # Normalized by 1 minute

            # Calculate confidence
            total_events1 = len(events_df[events_df['entity_id'] == entity1])
            confidence = self._calculate_confidence(
                occurrences=occurrences,
                total_possible=total_events1,
                consistency_score=consistency
            )

            patterns.append(PatternResult(
                pattern_type=PatternType.CO_OCCURRENCE,
                confidence=confidence,
                entities=[entity1, entity2],
                occurrences=occurrences,
                avg_value=avg_delta,
                std_dev=std_delta,
                description=f"{entity1} and {entity2} activate within {self.window_minutes} min",
                metadata={
                    'avg_time_delta_seconds': avg_delta,
                    'std_time_delta_seconds': std_delta,
                    'consistency_score': consistency
                }
            ))

        return patterns


# ==============================================================================
# 3. Sequence Detector
# ==============================================================================

class SequenceDetector(PatternDetector):
    """
    Detect sequential activation patterns

    Finds consistent sequences like A → B → C
    """

    def __init__(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.7,
        max_gap_minutes: int = 15,
        sequence_length: int = 3
    ):
        super().__init__(min_occurrences, min_confidence)
        self.max_gap_minutes = max_gap_minutes
        self.sequence_length = sequence_length

    def _get_pattern_type(self) -> PatternType:
        return PatternType.SEQUENCE

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect sequence patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        if 'timestamp' not in events_df.columns:
            return patterns

        events_df = events_df.copy()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df = events_df.sort_values('timestamp')

        # Find sequences
        sequences = defaultdict(int)
        max_gap = timedelta(minutes=self.max_gap_minutes)

        for i in range(len(events_df) - self.sequence_length + 1):
            window = events_df.iloc[i:i + self.sequence_length]

            # Check if within max gap
            time_span = window.iloc[-1]['timestamp'] - window.iloc[0]['timestamp']
            if time_span > max_gap:
                continue

            # Create sequence key
            sequence = tuple(window['entity_id'].tolist())
            sequences[sequence] += 1

        # Create patterns
        for sequence, count in sequences.items():
            if count < self.min_occurrences:
                continue

            # Calculate confidence
            first_entity_count = len(events_df[events_df['entity_id'] == sequence[0]])
            confidence = self._calculate_confidence(
                occurrences=count,
                total_possible=max(first_entity_count, 1),
                consistency_score=0.8  # Sequences are inherently consistent if repeated
            )

            patterns.append(PatternResult(
                pattern_type=PatternType.SEQUENCE,
                confidence=confidence,
                entities=list(sequence),
                occurrences=count,
                description=f"Sequence: {' → '.join(sequence)}",
                metadata={
                    'sequence_length': len(sequence),
                    'max_gap_minutes': self.max_gap_minutes
                }
            ))

        return patterns


# ==============================================================================
# 4. Contextual Detector (Sun/Weather/Occupancy)
# ==============================================================================

class ContextualDetector(PatternDetector):
    """
    Detect patterns tied to context (sun position, weather, occupancy)

    Finds automations that should trigger based on external conditions
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7
    ):
        super().__init__(min_occurrences, min_confidence)

    def _get_pattern_type(self) -> PatternType:
        return PatternType.CONTEXTUAL

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect contextual patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        # Sun-based patterns
        if 'sun_elevation' in events_df.columns:
            patterns.extend(self._detect_sun_patterns(events_df))

        # Weather-based patterns
        if 'temperature' in events_df.columns:
            patterns.extend(self._detect_weather_patterns(events_df))

        # Occupancy-based patterns
        if 'occupancy' in events_df.columns:
            patterns.extend(self._detect_occupancy_patterns(events_df))

        return patterns

    def _detect_sun_patterns(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect patterns based on sun position"""
        patterns = []

        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences:
                continue

            # Check if events cluster around sunrise/sunset
            sunrise_events = entity_events[
                (entity_events['sun_elevation'] > -6) &
                (entity_events['sun_elevation'] < 6)
            ]

            if len(sunrise_events) >= self.min_occurrences:
                confidence = self._calculate_confidence(
                    occurrences=len(sunrise_events),
                    total_possible=len(entity_events),
                    consistency_score=0.9
                )

                patterns.append(PatternResult(
                    pattern_type=PatternType.CONTEXTUAL,
                    confidence=confidence,
                    entity_id=entity_id,
                    occurrences=len(sunrise_events),
                    description=f"{entity_id} activates around sunrise/sunset",
                    metadata={
                        'context_type': 'sun_position',
                        'trigger': 'sunrise/sunset'
                    }
                ))

        return patterns

    def _detect_weather_patterns(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect patterns based on weather"""
        patterns = []

        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences:
                continue

            # Temperature-based patterns
            if 'temperature' in entity_events.columns:
                avg_temp = entity_events['temperature'].mean()
                temp_range = entity_events['temperature'].std()

                # Check if activations correlate with temperature
                if temp_range < 10:  # Temperature is consistent
                    confidence = self._calculate_confidence(
                        occurrences=len(entity_events),
                        total_possible=len(events_df[events_df['entity_id'] == entity_id]),
                        consistency_score=0.8
                    )

                    patterns.append(PatternResult(
                        pattern_type=PatternType.CONTEXTUAL,
                        confidence=confidence,
                        entity_id=entity_id,
                        occurrences=len(entity_events),
                        avg_value=avg_temp,
                        description=f"{entity_id} activates when temp around {avg_temp:.1f}°F",
                        metadata={
                            'context_type': 'temperature',
                            'avg_temperature': avg_temp,
                            'temp_range': temp_range
                        }
                    ))

        return patterns

    def _detect_occupancy_patterns(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect patterns based on occupancy"""
        patterns = []

        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences:
                continue

            # Check if device only activates when home
            if 'occupancy' in entity_events.columns:
                home_events = entity_events[entity_events['occupancy'] == 'home']

                if len(home_events) >= self.min_occurrences:
                    home_ratio = len(home_events) / len(entity_events)

                    if home_ratio > 0.8:  # 80% of activations when home
                        confidence = self._calculate_confidence(
                            occurrences=len(home_events),
                            total_possible=len(entity_events),
                            consistency_score=home_ratio
                        )

                        patterns.append(PatternResult(
                            pattern_type=PatternType.CONTEXTUAL,
                            confidence=confidence,
                            entity_id=entity_id,
                            occurrences=len(home_events),
                            description=f"{entity_id} activates only when home",
                            metadata={
                                'context_type': 'occupancy',
                                'condition': 'home',
                                'home_ratio': home_ratio
                            }
                        ))

        return patterns


# ==============================================================================
# 5. Duration Detector
# ==============================================================================

class DurationDetector(PatternDetector):
    """
    Detect patterns in how long devices stay in states

    Finds consistent duration patterns (e.g., lights on for 2 hours)
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7
    ):
        super().__init__(min_occurrences, min_confidence)

    def _get_pattern_type(self) -> PatternType:
        return PatternType.DURATION

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect duration patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        if 'timestamp' not in events_df.columns or 'state' not in events_df.columns:
            return patterns

        events_df = events_df.copy()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df = events_df.sort_values('timestamp')

        # Calculate durations for each entity
        for entity_id, entity_events in events_df.groupby('entity_id'):
            durations = []

            for i in range(len(entity_events) - 1):
                current_state = entity_events.iloc[i]['state']
                next_time = entity_events.iloc[i + 1]['timestamp']
                current_time = entity_events.iloc[i]['timestamp']

                duration_minutes = (next_time - current_time).total_seconds() / 60
                durations.append((current_state, duration_minutes))

            if not durations:
                continue

            # Group by state
            state_durations = defaultdict(list)
            for state, duration in durations:
                state_durations[state].append(duration)

            # Find patterns for each state
            for state, dur_list in state_durations.items():
                if len(dur_list) < self.min_occurrences:
                    continue

                avg_duration = np.mean(dur_list)
                std_duration = np.std(dur_list)
                consistency = 1.0 - min(std_duration / max(avg_duration, 1), 1.0)

                confidence = self._calculate_confidence(
                    occurrences=len(dur_list),
                    total_possible=len(durations),
                    consistency_score=consistency
                )

                patterns.append(PatternResult(
                    pattern_type=PatternType.DURATION,
                    confidence=confidence,
                    entity_id=entity_id,
                    occurrences=len(dur_list),
                    avg_value=avg_duration,
                    std_dev=std_duration,
                    description=f"{entity_id} stays '{state}' for ~{avg_duration:.0f} min",
                    metadata={
                        'state': state,
                        'avg_duration_minutes': avg_duration,
                        'std_duration_minutes': std_duration,
                        'consistency_score': consistency
                    }
                ))

        return patterns


# ==============================================================================
# 6. Day Type Detector (Weekday/Weekend)
# ==============================================================================

class DayTypeDetector(PatternDetector):
    """
    Detect patterns that differ between weekdays and weekends

    Finds behaviors that only happen on weekends or weekdays
    """

    def __init__(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.7
    ):
        super().__init__(min_occurrences, min_confidence)

    def _get_pattern_type(self) -> PatternType:
        return PatternType.DAY_TYPE

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect day-type patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        # Determine day type
        if 'timestamp' in events_df.columns:
            events_df = events_df.copy()
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
            events_df['day_of_week'] = events_df['timestamp'].dt.dayofweek
            events_df['day_type'] = events_df['day_of_week'].apply(
                lambda x: 'weekend' if x >= 5 else 'weekday'
            )
        elif 'day_type' not in events_df.columns:
            return patterns

        # Analyze by entity
        for entity_id, entity_events in events_df.groupby('entity_id'):
            day_type_counts = entity_events['day_type'].value_counts()

            for day_type, count in day_type_counts.items():
                if count < self.min_occurrences:
                    continue

                # Check if this day type is dominant
                total = len(entity_events)
                ratio = count / total

                if ratio > 0.7:  # 70% or more on this day type
                    confidence = self._calculate_confidence(
                        occurrences=count,
                        total_possible=total,
                        consistency_score=ratio
                    )

                    patterns.append(PatternResult(
                        pattern_type=PatternType.DAY_TYPE,
                        confidence=confidence,
                        entity_id=entity_id,
                        day_of_week=day_type,
                        occurrences=count,
                        description=f"{entity_id} activates primarily on {day_type}s",
                        metadata={
                            'day_type': day_type,
                            'day_type_ratio': ratio
                        }
                    ))

        return patterns


# ==============================================================================
# 7. Room Based Detector
# ==============================================================================

class RoomBasedDetector(PatternDetector):
    """
    Detect patterns involving multiple devices in the same room/area

    Finds room-level automation opportunities
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7,
        window_minutes: int = 10
    ):
        super().__init__(min_occurrences, min_confidence)
        self.window_minutes = window_minutes

    def _get_pattern_type(self) -> PatternType:
        return PatternType.ROOM_BASED

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect room-based patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        if 'area' not in events_df.columns:
            # Try to infer area from entity_id
            events_df = events_df.copy()
            events_df['area'] = events_df['entity_id'].apply(self._infer_area)

        if events_df['area'].isna().all():
            return patterns

        # Analyze by area
        for area, area_events in events_df.groupby('area'):
            if pd.isna(area) or len(area_events) < self.min_occurrences:
                continue

            # Find devices that activate together in this area
            area_entities = area_events['entity_id'].unique()

            if len(area_entities) < 2:
                continue

            # Find co-activations within window
            if 'timestamp' not in area_events.columns:
                continue

            area_events = area_events.copy()
            area_events['timestamp'] = pd.to_datetime(area_events['timestamp'])
            area_events = area_events.sort_values('timestamp')

            window = timedelta(minutes=self.window_minutes)
            co_activations = []

            for i in range(len(area_events)):
                event_time = area_events.iloc[i]['timestamp']
                window_events = area_events[
                    (area_events['timestamp'] >= event_time) &
                    (area_events['timestamp'] <= event_time + window)
                ]

                unique_entities = window_events['entity_id'].unique()
                if len(unique_entities) >= 2:
                    co_activations.append(sorted(unique_entities))

            if not co_activations:
                continue

            # Count most common combinations
            from collections import Counter
            combo_counts = Counter(tuple(combo) for combo in co_activations)

            for combo, count in combo_counts.most_common(5):
                if count < self.min_occurrences:
                    continue

                confidence = self._calculate_confidence(
                    occurrences=count,
                    total_possible=len(co_activations),
                    consistency_score=0.8
                )

                patterns.append(PatternResult(
                    pattern_type=PatternType.ROOM_BASED,
                    confidence=confidence,
                    entities=list(combo),
                    area=area,
                    occurrences=count,
                    description=f"Room '{area}': {len(combo)} devices activate together",
                    metadata={
                        'area': area,
                        'device_count': len(combo),
                        'window_minutes': self.window_minutes
                    }
                ))

        return patterns

    def _infer_area(self, entity_id: str) -> Optional[str]:
        """Infer area from entity_id"""
        # Common patterns: light.bedroom_lamp, switch.kitchen_outlet
        parts = entity_id.split('.')
        if len(parts) >= 2:
            # Check if second part contains room name
            name = parts[1]
            for room in ['bedroom', 'kitchen', 'living', 'bathroom', 'office', 'garage']:
                if room in name.lower():
                    return room.capitalize()

        return None


# ==============================================================================
# 8. Seasonal Detector
# ==============================================================================

class SeasonalDetector(PatternDetector):
    """
    Detect seasonal patterns (winter/spring/summer/fall)

    Finds behaviors that only occur in specific seasons
    """

    def __init__(
        self,
        min_occurrences: int = 5,
        min_confidence: float = 0.7
    ):
        super().__init__(min_occurrences, min_confidence)

    def _get_pattern_type(self) -> PatternType:
        return PatternType.SEASONAL

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect seasonal patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        # Determine season
        if 'timestamp' in events_df.columns:
            events_df = events_df.copy()
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
            events_df['month'] = events_df['timestamp'].dt.month
            events_df['season'] = events_df['month'].apply(self._get_season)
        elif 'season' not in events_df.columns:
            return patterns

        # Analyze by entity
        for entity_id, entity_events in events_df.groupby('entity_id'):
            season_counts = entity_events['season'].value_counts()

            for season, count in season_counts.items():
                if count < self.min_occurrences:
                    continue

                # Check if this season is dominant
                total = len(entity_events)
                ratio = count / total

                if ratio > 0.6:  # 60% or more in this season
                    confidence = self._calculate_confidence(
                        occurrences=count,
                        total_possible=total,
                        consistency_score=ratio
                    )

                    patterns.append(PatternResult(
                        pattern_type=PatternType.SEASONAL,
                        confidence=confidence,
                        entity_id=entity_id,
                        season=season,
                        occurrences=count,
                        description=f"{entity_id} activates primarily in {season}",
                        metadata={
                            'season': season,
                            'season_ratio': ratio
                        }
                    ))

        return patterns

    def _get_season(self, month: int) -> str:
        """Convert month to season"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'fall'


# ==============================================================================
# 9. Anomaly Detector
# ==============================================================================

class AnomalyDetector(PatternDetector):
    """
    Detect unusual patterns that deviate from normal behavior

    Finds anomalies that might indicate issues or security concerns
    """

    def __init__(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.7,
        sensitivity: float = 2.0
    ):
        super().__init__(min_occurrences, min_confidence)
        self.sensitivity = sensitivity  # Standard deviations for anomaly

    def _get_pattern_type(self) -> PatternType:
        return PatternType.ANOMALY

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect anomaly patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        if 'timestamp' not in events_df.columns:
            return patterns

        events_df = events_df.copy()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])

        # Detect time-based anomalies
        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences * 2:
                continue

            # Extract hour of day
            entity_events['hour'] = entity_events['timestamp'].dt.hour

            # Calculate normal hours
            hour_counts = entity_events['hour'].value_counts()
            mean_count = hour_counts.mean()
            std_count = hour_counts.std()

            if std_count == 0:
                continue

            # Find anomalous hours (unusually high activity)
            anomalous_hours = hour_counts[
                hour_counts > mean_count + (self.sensitivity * std_count)
            ]

            for hour, count in anomalous_hours.items():
                anomaly_score = (count - mean_count) / std_count

                confidence = min(anomaly_score / 3.0, 1.0)  # Normalize to 0-1

                if confidence >= self.min_confidence:
                    patterns.append(PatternResult(
                        pattern_type=PatternType.ANOMALY,
                        confidence=confidence,
                        entity_id=entity_id,
                        hour=int(hour),
                        occurrences=int(count),
                        description=f"{entity_id} has unusual activity at {hour:02d}:00",
                        metadata={
                            'anomaly_type': 'time_based',
                            'anomaly_score': float(anomaly_score),
                            'normal_mean': float(mean_count),
                            'normal_std': float(std_count)
                        }
                    ))

        return patterns


# ==============================================================================
# 10. Frequency Detector
# ==============================================================================

class FrequencyDetector(PatternDetector):
    """
    Detect patterns in activation frequency

    Finds devices used with consistent frequency (hourly, daily, weekly)
    """

    def __init__(
        self,
        min_occurrences: int = 10,
        min_confidence: float = 0.7
    ):
        super().__init__(min_occurrences, min_confidence)

    def _get_pattern_type(self) -> PatternType:
        return PatternType.FREQUENCY

    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """Detect frequency patterns"""
        patterns = []

        if events_df.empty or 'entity_id' not in events_df.columns:
            return patterns

        if 'timestamp' not in events_df.columns:
            return patterns

        events_df = events_df.copy()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])

        # Analyze by entity
        for entity_id, entity_events in events_df.groupby('entity_id'):
            if len(entity_events) < self.min_occurrences:
                continue

            # Calculate time between events
            entity_events = entity_events.sort_values('timestamp')
            time_diffs = entity_events['timestamp'].diff().dt.total_seconds() / 3600  # Hours

            time_diffs = time_diffs.dropna()

            if len(time_diffs) < self.min_occurrences:
                continue

            avg_interval = time_diffs.mean()
            std_interval = time_diffs.std()

            if avg_interval == 0:
                continue

            consistency = 1.0 - min(std_interval / avg_interval, 1.0)

            # Determine frequency type
            if avg_interval < 2:
                freq_type = 'hourly'
            elif avg_interval < 30:
                freq_type = 'daily'
            else:
                freq_type = 'weekly'

            confidence = self._calculate_confidence(
                occurrences=len(time_diffs),
                total_possible=len(entity_events),
                consistency_score=consistency
            )

            patterns.append(PatternResult(
                pattern_type=PatternType.FREQUENCY,
                confidence=confidence,
                entity_id=entity_id,
                occurrences=len(entity_events),
                avg_value=avg_interval,
                std_dev=std_interval,
                description=f"{entity_id} activates {freq_type} (~every {avg_interval:.1f}h)",
                metadata={
                    'frequency_type': freq_type,
                    'avg_interval_hours': avg_interval,
                    'std_interval_hours': std_interval,
                    'consistency_score': consistency
                }
            ))

        return patterns
