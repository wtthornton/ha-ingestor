"""
Simple Statistics Calculator for Sports Data

Calculate team statistics from game data.
Story 12.2 - Historical Query Endpoints
"""

import logging
from typing import List, Dict, Any
from src.models_history import TeamStatistics


logger = logging.getLogger(__name__)


def calculate_team_record(games: List[Dict[str, Any]], team: str, season: str) -> TeamStatistics:
    """
    Calculate team record from games.
    
    Args:
        games: List of game dictionaries
        team: Team name
        season: Season
        
    Returns:
        TeamStatistics with wins/losses/stats
    """
    wins = 0
    losses = 0
    ties = 0
    points_for = 0
    points_against = 0
    
    for game in games:
        # Determine if team is home or away
        is_home = game.get('home_team') == team
        team_score = game.get('home_score', 0) if is_home else game.get('away_score', 0)
        opp_score = game.get('away_score', 0) if is_home else game.get('home_score', 0)
        
        # Only count finished games
        if game.get('status') != 'finished':
            continue
        
        points_for += team_score
        points_against += opp_score
        
        if team_score > opp_score:
            wins += 1
        elif team_score < opp_score:
            losses += 1
        else:
            ties += 1
    
    games_played = wins + losses + ties
    win_percentage = wins / games_played if games_played > 0 else 0.0
    
    return TeamStatistics(
        team=team,
        season=season,
        games_played=games_played,
        wins=wins,
        losses=losses,
        ties=ties,
        win_percentage=round(win_percentage, 3),
        points_for=points_for,
        points_against=points_against,
        point_differential=points_for - points_against
    )

