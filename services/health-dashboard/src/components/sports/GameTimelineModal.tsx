/**
 * GameTimelineModal Component
 * 
 * Modal displaying score progression timeline for a game
 * Epic 21 Story 21.2 Phase 3
 */

import React, { useState, useEffect } from 'react';
import { dataApi } from '../../services/api';
import { ScoreTimelineChart } from './charts/ScoreTimelineChart';

interface GameTimelineModalProps {
  game: {
    game_id: string;
    league: string;
    home_team: string;
    away_team: string;
    home_score: number;
    away_score: number;
    timestamp: string;
  };
  onClose: () => void;
  darkMode?: boolean;
}

interface TimelinePoint {
  timestamp: string;
  home_score: number;
  away_score: number;
  quarter_period: string;
  time_remaining: string;
}

export const GameTimelineModal: React.FC<GameTimelineModalProps> = ({
  game,
  onClose,
  darkMode = false
}) => {
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const modalBg = darkMode ? 'bg-gray-800' : 'bg-white';
  const textPrimary = darkMode ? 'text-white' : 'text-gray-900';
  const textSecondary = darkMode ? 'text-gray-400' : 'text-gray-600';
  const overlayBg = darkMode ? 'bg-black bg-opacity-70' : 'bg-black bg-opacity-50';

  useEffect(() => {
    fetchGameTimeline();
  }, [game.game_id]);

  const fetchGameTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Query game timeline from InfluxDB
      const data = await dataApi.getGameTimeline(game.game_id);
      
      if (data && data.timeline) {
        setTimeline(data.timeline);
      } else {
        setTimeline([]);
      }
    } catch (err) {
      console.error('Error fetching game timeline:', err);
      setError(err instanceof Error ? err.message : 'Failed to load game timeline');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${overlayBg}`}
      onClick={onClose}
    >
      <div 
        className={`${modalBg} rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div>
            <h2 className={`text-xl font-bold ${textPrimary}`}>
              Game Timeline
            </h2>
            <p className={`text-sm ${textSecondary}`}>
              {game.home_team} vs {game.away_team}
            </p>
          </div>
          <button
            onClick={onClose}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
              darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
            }`}
            aria-label="Close modal"
          >
            <span className="text-2xl">×</span>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Final Score */}
          <div className="mb-6">
            <div className="flex items-center justify-center gap-8 p-4 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-750 dark:to-gray-700">
              <div className="text-center">
                <div className={`text-lg font-semibold ${textPrimary}`}>{game.home_team}</div>
                <div className="text-4xl font-bold mt-2">{game.home_score}</div>
              </div>
              <div className={`text-2xl font-bold ${textSecondary}`}>-</div>
              <div className="text-center">
                <div className={`text-lg font-semibold ${textPrimary}`}>{game.away_team}</div>
                <div className="text-4xl font-bold mt-2">{game.away_score}</div>
              </div>
            </div>
            <div className={`text-center text-sm ${textSecondary} mt-2`}>
              {new Date(game.timestamp).toLocaleString()}
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className={textSecondary}>Loading timeline...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="text-center py-12">
              <div className="text-red-500 mb-4">⚠️</div>
              <p className="text-red-500">{error}</p>
            </div>
          )}

          {/* Timeline Chart */}
          {!loading && !error && timeline.length > 0 && (
            <div>
              <h3 className={`text-lg font-semibold ${textPrimary} mb-4`}>
                Score Progression
              </h3>
              <ScoreTimelineChart
                timeline={timeline}
                homeTeam={game.home_team}
                awayTeam={game.away_team}
                darkMode={darkMode}
              />
            </div>
          )}

          {/* No Data State */}
          {!loading && !error && timeline.length === 0 && (
            <div className={`text-center py-12 ${textSecondary}`}>
              <div className="text-4xl mb-4">📊</div>
              <p>No timeline data available for this game</p>
              <p className="text-sm mt-2">Timeline data may not be recorded for all games</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-200 hover:bg-gray-300 text-gray-900'
            }`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

