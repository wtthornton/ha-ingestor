import { useState, useEffect } from 'react';
import { HealthStatus } from '../types';
import { apiService } from '../services/api';

export const useHealth = (refreshInterval: number = 30000) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setError(null);
      const healthData = await apiService.getHealth();
      setHealth(healthData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
      console.error('Health fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchHealth();

    // Set up polling
    const interval = setInterval(fetchHealth, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { health, loading, error, refresh: fetchHealth };
};
