import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { DataSourceHealth } from '../types';

export const useDataSources = (refreshInterval: number = 30000) => {
  const [dataSources, setDataSources] = useState<{
    weather: DataSourceHealth | null;
    carbonIntensity: DataSourceHealth | null;
    electricityPricing: DataSourceHealth | null;
    airQuality: DataSourceHealth | null;
    calendar: DataSourceHealth | null;
    smartMeter: DataSourceHealth | null;
  } | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDataSources = async () => {
    try {
      const data = await apiService.getAllDataSources();
      setDataSources(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data sources');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDataSources();
    const interval = setInterval(fetchDataSources, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { dataSources, loading, error, refetch: fetchDataSources };
};

