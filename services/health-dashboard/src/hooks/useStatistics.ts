import { useState, useEffect, useCallback } from 'react';
import { Statistics } from '../types';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';

export const useStatistics = (period: string = '1h', refreshInterval: number = 30000) => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setError(null);
      const statsData = await apiService.getStatistics(period);
      setStatistics(statsData);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
      console.error('Statistics fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    // Initial fetch
    fetchStatistics();

    // Set up polling
    const interval = setInterval(fetchStatistics, refreshInterval);

    // Set up WebSocket subscription
    const unsubscribe = websocketService.subscribe((message) => {
      if (message.type === 'stats_update') {
        setStatistics(message.data);
        setLastUpdate(new Date().toISOString());
        setError(null);
      }
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [fetchStatistics, refreshInterval]);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    statistics,
    loading,
    error,
    lastUpdate,
    refresh,
  };
};
