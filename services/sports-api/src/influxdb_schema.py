"""
InfluxDB Schema Definitions for Sports Data

Defines measurements, tags, and fields for optimal time-series storage.
Following Context7 KB best practices for InfluxDB schema design.
"""

from typing import Dict, Any, List

# ============================================================================
# Measurement Names
# ============================================================================

MEASUREMENT_NFL_SCORES = "nfl_scores"
MEASUREMENT_NHL_SCORES = "nhl_scores"
MEASUREMENT_NFL_PLAYER_STATS = "nfl_player_stats"
MEASUREMENT_NFL_INJURIES = "nfl_injuries"
MEASUREMENT_NFL_STANDINGS = "nfl_standings"
MEASUREMENT_NHL_STANDINGS = "nhl_standings"

# ============================================================================
# Retention Policies
# ============================================================================

RETENTION_POLICIES = {
    "sports_events_2y": {
        "duration": "730d",  # 2 years
        "measurements": [MEASUREMENT_NFL_SCORES, MEASUREMENT_NHL_SCORES],
        "description": "Live scores and game data"
    },
    "sports_stats_2y": {
        "duration": "730d",  # 2 years
        "measurements": [MEASUREMENT_NFL_PLAYER_STATS, MEASUREMENT_NFL_INJURIES],
        "description": "Player statistics and injury reports"
    },
    "sports_standings_5y": {
        "duration": "1825d",  # 5 years
        "measurements": [MEASUREMENT_NFL_STANDINGS, MEASUREMENT_NHL_STANDINGS],
        "description": "Historical standings for trend analysis"
    }
}

# ============================================================================
# Tag Keys (indexed for fast querying)
# ============================================================================

# NFL Scores Tags
NFL_SCORES_TAGS = [
    "game_id",          # Unique game identifier
    "season",           # Season year
    "week",             # Week number
    "home_team",        # Home team name
    "away_team",        # Away team name
    "status",           # Game status (scheduled, live, finished)
    "home_conference",  # Home team conference (AFC/NFC)
    "away_conference",  # Away team conference
    "home_division",    # Home team division
    "away_division"     # Away team division
]

# NHL Scores Tags
NHL_SCORES_TAGS = [
    "game_id",
    "season",
    "home_team",
    "away_team",
    "status",
    "home_conference",
    "away_conference",
    "home_division",
    "away_division"
]

# Player Stats Tags
PLAYER_STATS_TAGS = [
    "player_id",
    "player_name",
    "team",
    "position",
    "game_id",
    "season",
    "week"
]

# Injury Tags
INJURY_TAGS = [
    "player_id",
    "player_name",
    "team",
    "position",
    "status",
    "injury_type",
    "season"
]

# Standings Tags
STANDINGS_TAGS = [
    "team",
    "conference",
    "division",
    "season"
]

# ============================================================================
# Field Keys (measurement data)
# ============================================================================

# NFL Scores Fields
NFL_SCORES_FIELDS = [
    "home_score",       # Home team score (integer)
    "away_score",       # Away team score (integer)
    "quarter",          # Current quarter (string)
    "time_remaining",   # Time remaining (string)
    "possession",       # Team with possession (string)
    "down_distance",    # Down and distance (string)
    "field_position"    # Field position (string)
]

# NHL Scores Fields  
NHL_SCORES_FIELDS = [
    "home_score",
    "away_score",
    "period",
    "time_remaining",
    "home_shots",
    "away_shots",
    "home_power_play",
    "away_power_play"
]

# Player Stats Fields (dynamic based on position)
# These are examples - actual fields come from API response
PLAYER_STATS_FIELDS = [
    "passing_yards",
    "passing_touchdowns",
    "interceptions",
    "rushing_yards",
    "rushing_touchdowns",
    "receptions",
    "receiving_yards",
    "receiving_touchdowns",
    "qb_rating"
]

# Injury Fields
INJURY_FIELDS = [
    "weeks_out",
    "practice_participation"
]

# Standings Fields
STANDINGS_FIELDS = [
    "wins",
    "losses",
    "ties",
    "win_percentage",
    "points_for",
    "points_against",
    "point_differential",
    "division_wins",
    "conference_wins"
]

# ============================================================================
# Schema Helpers
# ============================================================================

def get_measurement_tags(measurement: str) -> List[str]:
    """
    Get tag keys for a measurement.
    
    Args:
        measurement: Measurement name
        
    Returns:
        List of tag keys
    """
    tag_map = {
        MEASUREMENT_NFL_SCORES: NFL_SCORES_TAGS,
        MEASUREMENT_NHL_SCORES: NHL_SCORES_TAGS,
        MEASUREMENT_NFL_PLAYER_STATS: PLAYER_STATS_TAGS,
        MEASUREMENT_NFL_INJURIES: INJURY_TAGS,
        MEASUREMENT_NFL_STANDINGS: STANDINGS_TAGS,
        MEASUREMENT_NHL_STANDINGS: STANDINGS_TAGS
    }
    return tag_map.get(measurement, [])


def get_measurement_fields(measurement: str) -> List[str]:
    """
    Get field keys for a measurement.
    
    Args:
        measurement: Measurement name
        
    Returns:
        List of field keys
    """
    field_map = {
        MEASUREMENT_NFL_SCORES: NFL_SCORES_FIELDS,
        MEASUREMENT_NHL_SCORES: NHL_SCORES_FIELDS,
        MEASUREMENT_NFL_PLAYER_STATS: PLAYER_STATS_FIELDS,
        MEASUREMENT_NFL_INJURIES: INJURY_FIELDS,
        MEASUREMENT_NFL_STANDINGS: STANDINGS_FIELDS,
        MEASUREMENT_NHL_STANDINGS: STANDINGS_FIELDS
    }
    return field_map.get(measurement, [])


def get_retention_policy(measurement: str) -> str:
    """
    Get retention policy for a measurement.
    
    Args:
        measurement: Measurement name
        
    Returns:
        Retention policy name
    """
    for policy_name, policy_config in RETENTION_POLICIES.items():
        if measurement in policy_config["measurements"]:
            return policy_name
    return "default"

