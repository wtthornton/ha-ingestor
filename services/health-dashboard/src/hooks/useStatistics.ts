import { useState, useEffect } from 'react';
import { Statistics } from '../types';
import { apiService } from '../services/api';

export const useStatistics = (period: string = '1h', refreshInterval: number = 60000) => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = async () => {
    try {
      setError(null);
      const statsData = await apiService.getStatistics(period);
      setStatistics(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
      console.error('Statistics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchStatistics();

    // Set up polling
    const interval = setInterval(fetchStatistics, refreshInterval);

    return () => clearInterval(interval);
  }, [period, refreshInterval]);

  return { statistics, loading, error, refresh: fetchStatistics };
};
