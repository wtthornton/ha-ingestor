"""
Unit tests for Stats Calculator

Story 12.2 - Historical Query Endpoints
"""

import pytest
from src.stats_calculator import calculate_team_record


def test_calculate_team_record():
    """Test team record calculation"""
    games = [
        {"home_team": "Patriots", "away_team": "Chiefs", "home_score": 21, "away_score": 17, "status": "finished"},
        {"home_team": "Bills", "away_team": "Patriots", "home_score": 14, "away_score": 24, "status": "finished"},
        {"home_team": "Patriots", "away_team": "Dolphins", "home_score": 28, "away_score": 24, "status": "finished"}
    ]
    
    stats = calculate_team_record(games, "Patriots", "2025")
    
    assert stats.games_played == 3
    assert stats.wins == 3
    assert stats.losses == 0
    assert stats.win_percentage == 1.0


def test_calculate_team_record_with_losses():
    """Test team record with wins and losses"""
    games = [
        {"home_team": "Patriots", "away_team": "Chiefs", "home_score": 21, "away_score": 24, "status": "finished"},
        {"home_team": "Patriots", "away_team": "Bills", "home_score": 28, "away_score": 14, "status": "finished"}
    ]
    
    stats = calculate_team_record(games, "Patriots", "2025")
    
    assert stats.games_played == 2
    assert stats.wins == 1
    assert stats.losses == 1
    assert stats.win_percentage == 0.5

