import { useState, useEffect, useCallback } from 'react';
import { SystemHealth } from '../types';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';

export const useHealth = (refreshInterval: number = 30000) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setError(null);
      const healthData = await apiService.getHealth();
      setHealth(healthData);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
      console.error('Health fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchHealth();

    // Set up polling
    const interval = setInterval(fetchHealth, refreshInterval);

    // Set up WebSocket subscription
    const unsubscribe = websocketService.subscribe((message) => {
      if (message.type === 'health_update') {
        setHealth(message.data);
        setLastUpdate(new Date().toISOString());
        setError(null);
      }
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [fetchHealth, refreshInterval]);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchHealth();
  }, [fetchHealth]);

  return {
    health,
    loading,
    error,
    lastUpdate,
    refresh,
  };
};
