import { useState, useEffect, useCallback } from 'react';
import { EventData, EventFilter } from '../types';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';

export const useEvents = (filter: EventFilter = {}, refreshInterval: number = 10000) => {
  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setError(null);
      const eventsData = await apiService.getEvents(filter);
      setEvents(eventsData);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
      console.error('Events fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    // Initial fetch
    fetchEvents();

    // Set up polling
    const interval = setInterval(fetchEvents, refreshInterval);

    // Set up WebSocket subscription
    const unsubscribe = websocketService.subscribe((message) => {
      if (message.type === 'event_update') {
        const newEvent = message.data;
        setEvents(prev => [newEvent, ...prev.slice(0, (filter.limit || 100) - 1)]);
        setLastUpdate(new Date().toISOString());
        setError(null);
      }
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, [fetchEvents, refreshInterval, filter]);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchEvents();
  }, [fetchEvents]);

  const searchEvents = useCallback(async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      const searchResults = await apiService.searchEvents(query);
      setEvents(searchResults);
      setLastUpdate(new Date().toISOString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search events');
      console.error('Events search error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    events,
    loading,
    error,
    lastUpdate,
    refresh,
    searchEvents,
  };
};
