import React, { useState, useEffect, useMemo } from 'react';
import { EventData, EventFilter } from '../types';
import { apiService } from '../services/api';
import { format, parseISO } from 'date-fns';

interface EventBrowserProps {
  onExport?: (events: EventData[], format: 'csv' | 'json') => void;
}

interface FilterState {
  entityId: string;
  eventType: string;
  startTime: string;
  endTime: string;
  searchQuery: string;
  limit: number;
}

export const EventBrowser: React.FC<EventBrowserProps> = ({ onExport }) => {
  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [queryTime, setQueryTime] = useState<number>(0);

  const [filters, setFilters] = useState<FilterState>({
    entityId: '',
    eventType: '',
    startTime: '',
    endTime: '',
    searchQuery: '',
    limit: 100,
  });

  const [availableEntities, setAvailableEntities] = useState<string[]>([]);
  const [availableEventTypes, setAvailableEventTypes] = useState<string[]>([]);

  useEffect(() => {
    fetchEvents();
    fetchAvailableData();
  }, [filters]);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      const filter: EventFilter = {
        limit: filters.limit,
        offset: 0,
      };

      if (filters.entityId) filter.entity_id = filters.entityId;
      if (filters.eventType) filter.event_type = filters.eventType;
      if (filters.startTime) filter.start_time = filters.startTime;
      if (filters.endTime) filter.end_time = filters.endTime;

      const eventsData = await apiService.getEvents(filter);
      setEvents(eventsData);
      setTotalCount(eventsData.length);

      const endTime = performance.now();
      setQueryTime(endTime - startTime);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableData = async () => {
    try {
      const [entities, eventTypes] = await Promise.all([
        apiService.getActiveEntities(50),
        apiService.getEventTypes(20),
      ]);
      
      setAvailableEntities(entities.map((e: any) => e.entity_id || e));
      setAvailableEventTypes(eventTypes.map((e: any) => e.event_type || e));
    } catch (err) {
      console.error('Failed to fetch available data:', err);
    }
  };

  const handleFilterChange = (key: keyof FilterState, value: string | number) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSearch = async () => {
    if (filters.searchQuery.trim()) {
      try {
        setLoading(true);
        const searchResults = await apiService.searchEvents(filters.searchQuery);
        setEvents(searchResults);
        setTotalCount(searchResults.length);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
      } finally {
        setLoading(false);
      }
    } else {
      fetchEvents();
    }
  };

  const clearFilters = () => {
    setFilters({
      entityId: '',
      eventType: '',
      startTime: '',
      endTime: '',
      searchQuery: '',
      limit: 100,
    });
  };

  const exportData = (format: 'csv' | 'json') => {
    onExport?.(events, format);
  };

  const getEventTypeColor = (eventType: string): string => {
    switch (eventType) {
      case 'state_changed':
        return 'bg-blue-100 text-blue-800';
      case 'entity_registry_updated':
        return 'bg-green-100 text-green-800';
      case 'service_registered':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredEvents = useMemo(() => {
    return events.filter(event => {
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        return (
          event.entity_id.toLowerCase().includes(query) ||
          event.event_type.toLowerCase().includes(query) ||
          JSON.stringify(event.attributes).toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [events, filters.searchQuery]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Event Browser</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {totalCount} events • {queryTime.toFixed(0)}ms
          </span>
          <button
            onClick={() => exportData('csv')}
            className="px-3 py-1 bg-green-100 text-green-800 rounded text-sm font-medium hover:bg-green-200"
          >
            Export CSV
          </button>
          <button
            onClick={() => exportData('json')}
            className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium hover:bg-blue-200"
          >
            Export JSON
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Entity ID
          </label>
          <select
            value={filters.entityId}
            onChange={(e) => handleFilterChange('entityId', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All entities</option>
            {availableEntities.map(entity => (
              <option key={entity} value={entity}>{entity}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Event Type
          </label>
          <select
            value={filters.eventType}
            onChange={(e) => handleFilterChange('eventType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All types</option>
            {availableEventTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Limit
          </label>
          <select
            value={filters.limit}
            onChange={(e) => handleFilterChange('limit', Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={50}>50 events</option>
            <option value={100}>100 events</option>
            <option value={500}>500 events</option>
            <option value={1000}>1000 events</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Time
          </label>
          <input
            type="datetime-local"
            value={filters.startTime}
            onChange={(e) => handleFilterChange('startTime', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Time
          </label>
          <input
            type="datetime-local"
            value={filters.endTime}
            onChange={(e) => handleFilterChange('endTime', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-end space-x-2">
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button
            onClick={clearFilters}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Search events by entity ID, event type, or attributes..."
            value={filters.searchQuery}
            onChange={(e) => handleFilterChange('searchQuery', e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <svg
            className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Query Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Events List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading events...</p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No events found
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getEventTypeColor(event.event_type)}`}>
                      {event.event_type}
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {event.entity_id}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-600 mb-2">
                    {format(parseISO(event.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                  </div>

                  {event.new_state && (
                    <div className="text-sm">
                      <span className="text-gray-500">State: </span>
                      <span className="font-medium">{event.new_state.state}</span>
                      {event.new_state.attributes?.unit_of_measurement && (
                        <span className="text-gray-500 ml-1">
                          ({event.new_state.attributes.unit_of_measurement})
                        </span>
                      )}
                    </div>
                  )}

                  {event.attributes && Object.keys(event.attributes).length > 0 && (
                    <div className="mt-2">
                      <details className="text-sm">
                        <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                          Attributes ({Object.keys(event.attributes).length})
                        </summary>
                        <div className="mt-2 pl-4 space-y-1">
                          {Object.entries(event.attributes).slice(0, 5).map(([key, value]) => (
                            <div key={key} className="text-xs">
                              <span className="font-medium">{key}:</span> {String(value)}
                            </div>
                          ))}
                          {Object.keys(event.attributes).length > 5 && (
                            <div className="text-xs text-gray-500">
                              ... and {Object.keys(event.attributes).length - 5} more
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
