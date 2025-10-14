/**
 * EventsWidget Component
 * 
 * Compact event stream widget for customizable dashboard
 * Epic 15.3: Dashboard Customization & Layout
 */

import React from 'react';

interface EventsWidgetProps {
  darkMode: boolean;
}

export const EventsWidget: React.FC<EventsWidgetProps> = ({ darkMode }) => {
  // TODO: Implement HTTP polling for events from /api/v1/events endpoint
  const events: any[] = [];

  return (
    <div className="h-full flex flex-col">
      <h3 className={`text-lg font-semibold mb-3 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        📡 Live Events
      </h3>
      
      <div className="flex-1 overflow-y-auto space-y-2">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
              No recent events
            </p>
          </div>
        ) : (
          events.map((event: any, idx: number) => (
            <div
              key={idx}
              className={`p-2 rounded border text-xs ${
                darkMode ? 'border-gray-700 hover:bg-gray-700/50' : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`font-mono ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className={`${darkMode ? 'text-white' : 'text-gray-900'} truncate`}>
                {event.message || JSON.stringify(event).slice(0, 100)}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

