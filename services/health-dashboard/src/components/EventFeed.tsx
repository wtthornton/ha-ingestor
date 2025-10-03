import React, { useState } from 'react';
import { EventData, EventFilter } from '../types';
import { format } from 'date-fns';

interface EventFeedProps {
  events: EventData[];
  loading?: boolean;
  onFilter?: (filter: EventFilter) => void;
}

export const EventFeed: React.FC<EventFeedProps> = ({ events, loading = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntity, setSelectedEntity] = useState<string>('');

  const filteredEvents = events.filter(event => {
    const matchesSearch = !searchTerm || 
      event.entity_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.event_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesEntity = !selectedEntity || event.entity_id === selectedEntity;
    
    return matchesSearch && matchesEntity;
  });

  const uniqueEntities = Array.from(new Set(events.map(event => event.entity_id))).slice(0, 20);

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

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Recent Events</h2>
        <div className="text-sm text-gray-500">
          {filteredEvents.length} events
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 space-y-3">
        <div>
          <input
            type="text"
            placeholder="Search events..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <select
            value={selectedEntity}
            onChange={(e) => setSelectedEntity(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All entities</option>
            {uniqueEntities.map(entity => (
              <option key={entity} value={entity}>{entity}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {filteredEvents.length === 0 ? (
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
                    {format(new Date(event.timestamp), 'MMM dd, yyyy HH:mm:ss')}
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
