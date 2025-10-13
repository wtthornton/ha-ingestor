import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

export interface Device {
  device_id: string;
  name: string;
  manufacturer: string;
  model: string;
  sw_version?: string;
  area_id?: string;
  entity_count: number;
  timestamp: string;
}

export interface Entity {
  entity_id: string;
  device_id?: string;
  domain: string;
  platform: string;
  unique_id?: string;
  area_id?: string;
  disabled: boolean;
  timestamp: string;
}

export interface Integration {
  entry_id: string;
  domain: string;
  title: string;
  state: string;
  version: number;
  timestamp: string;
}

export function useDevices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async (filters?: Record<string, string>) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
      }
      
      const queryString = params.toString();
      const url = queryString ? `/api/devices?${queryString}` : '/api/devices';
      
      const response = await apiService.get(url);
      setDevices(response.data.devices || []);
    } catch (err: any) {
      console.error('Error fetching devices:', err);
      setError(err.message || 'Failed to fetch devices');
      setDevices([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchEntities = useCallback(async (filters?: Record<string, string>) => {
    try {
      const params = new URLSearchParams();
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) params.append(key, value);
        });
      }
      
      const queryString = params.toString();
      const url = queryString ? `/api/entities?${queryString}` : '/api/entities';
      
      const response = await apiService.get(url);
      setEntities(response.data.entities || []);
    } catch (err: any) {
      console.error('Error fetching entities:', err);
      setEntities([]);
    }
  }, []);

  const fetchIntegrations = useCallback(async () => {
    try {
      const response = await apiService.get('/api/integrations');
      setIntegrations(response.data.integrations || []);
    } catch (err: any) {
      console.error('Error fetching integrations:', err);
      setIntegrations([]);
    }
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        fetchDevices(),
        fetchEntities(),
        fetchIntegrations()
      ]);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [fetchDevices, fetchEntities, fetchIntegrations]);

  // Initial fetch
  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    devices,
    entities,
    integrations,
    loading,
    error,
    fetchDevices,
    fetchEntities,
    fetchIntegrations,
    refresh: fetchAll
  };
}

