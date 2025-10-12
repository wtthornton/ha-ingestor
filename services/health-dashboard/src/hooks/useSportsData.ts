/**
 * useSportsData Hook
 * 
 * Fetches and manages sports game data with polling
 * Following Context7 KB patterns for custom hooks
 */

import { useState, useEffect, useCallback } from 'react';
import type { Game } from '../types/sports';

interface UseSportsDataProps {
  teamIds: string[];
  league?: 'NFL' | 'NHL' | 'all';
  pollInterval?: number;
}

export const useSportsData = ({
  teamIds,
  league = 'all',
  pollInterval = 30000
}: UseSportsDataProps) => {
  const [liveGames, setLiveGames] = useState<Game[]>([]);
  const [upcomingGames, setUpcomingGames] = useState<Game[]>([]);
  const [completedGames, setCompletedGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Fetch games function (memoized with useCallback from Context7 KB pattern)
  const fetchGames = useCallback(async () => {
    if (teamIds.length === 0) {
      setLiveGames([]);
      setUpcomingGames([]);
      setCompletedGames([]);
      setLoading(false);
      return;
    }

    try {
      setError(null);
      const teamIdsParam = teamIds.join(',');
      const leagueParam = league !== 'all' ? `&league=${league}` : '';

      // Fetch live games
      const liveResponse = await fetch(
        `/api/sports/games/live?team_ids=${teamIdsParam}${leagueParam}`
      );
      
      if (!liveResponse.ok) {
        throw new Error(`HTTP ${liveResponse.status}: ${liveResponse.statusText}`);
      }
      
      const liveData = await liveResponse.json();
      setLiveGames(liveData.games || []);

      // Fetch upcoming games (next 24 hours)
      const upcomingResponse = await fetch(
        `/api/sports/games/upcoming?team_ids=${teamIdsParam}&hours=24${leagueParam}`
      );
      
      if (!upcomingResponse.ok) {
        throw new Error(`HTTP ${upcomingResponse.status}: ${upcomingResponse.statusText}`);
      }
      
      const upcomingData = await upcomingResponse.json();
      setUpcomingGames(upcomingData.games || []);

      // TODO: Fetch completed games (Story 11.4)
      setCompletedGames([]);

      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sports data');
      console.error('Sports data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [teamIds, league]);

  // Initial fetch and polling setup (Context7 KB useEffect pattern)
  useEffect(() => {
    fetchGames();

    // Set up polling for real-time updates
    const interval = setInterval(fetchGames, pollInterval);

    return () => clearInterval(interval);
  }, [fetchGames, pollInterval]);

  return {
    liveGames,
    upcomingGames,
    completedGames,
    loading,
    error,
    lastUpdate,
    refresh: fetchGames
  };
};

