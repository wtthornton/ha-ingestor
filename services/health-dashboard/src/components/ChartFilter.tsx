import React, { useState, useEffect } from 'react';
import { format, subDays, subHours, subWeeks, subMonths } from 'date-fns';
import { ChartFilters, ChartType } from '../types';

interface ChartFilterProps {
  filters: ChartFilters;
  onFilterChange: (filters: ChartFilters) => void;
  chartType: ChartType;
}

const TIME_RANGE_PRESETS = [
  { label: 'Last Hour', value: '1h', getValue: () => ({ start: subHours(new Date(), 1), end: new Date() }) },
  { label: 'Last 6 Hours', value: '6h', getValue: () => ({ start: subHours(new Date(), 6), end: new Date() }) },
  { label: 'Last 24 Hours', value: '24h', getValue: () => ({ start: subDays(new Date(), 1), end: new Date() }) },
  { label: 'Last 3 Days', value: '3d', getValue: () => ({ start: subDays(new Date(), 3), end: new Date() }) },
  { label: 'Last Week', value: '1w', getValue: () => ({ start: subWeeks(new Date(), 1), end: new Date() }) },
  { label: 'Last Month', value: '1m', getValue: () => ({ start: subMonths(new Date(), 1), end: new Date() }) },
];

const ENTITY_TYPES = [
  'sensor',
  'binary_sensor',
  'switch',
  'light',
  'climate',
  'cover',
  'fan',
  'lock',
  'alarm_control_panel',
  'camera',
  'device_tracker',
  'person',
  'sun',
  'weather',
  'zone',
];

const EVENT_TYPES = [
  'state_changed',
  'homeassistant_start',
  'homeassistant_stop',
  'call_service',
  'service_registered',
  'component_loaded',
  'logbook_entry',
  'system_log_event',
];

export const ChartFilter: React.FC<ChartFilterProps> = ({
  filters,
  onFilterChange,
  chartType,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState<ChartFilters>(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleTimeRangePreset = (preset: typeof TIME_RANGE_PRESETS[0]) => {
    const timeRange = preset.getValue();
    const newFilters = { ...localFilters, timeRange };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleCustomTimeRange = (field: 'start' | 'end', value: string) => {
    const newTimeRange = {
      ...localFilters.timeRange,
      [field]: new Date(value),
    };
    const newFilters = { ...localFilters, timeRange: newTimeRange };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleEntityTypeToggle = (entityType: string) => {
    const currentTypes = localFilters.entityTypes || [];
    const newTypes = currentTypes.includes(entityType)
      ? currentTypes.filter(t => t !== entityType)
      : [...currentTypes, entityType];
    
    const newFilters = { ...localFilters, entityTypes: newTypes };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleEventTypeToggle = (eventType: string) => {
    const currentTypes = localFilters.eventTypes || [];
    const newTypes = currentTypes.includes(eventType)
      ? currentTypes.filter(t => t !== eventType)
      : [...currentTypes, eventType];
    
    const newFilters = { ...localFilters, eventTypes: newTypes };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleDataPointsChange = (value: string) => {
    const dataPoints = value ? parseInt(value, 10) : undefined;
    const newFilters = { ...localFilters, dataPoints };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const clearFilters = () => {
    const newFilters: ChartFilters = {};
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const hasActiveFilters = () => {
    return !!(
      localFilters.timeRange ||
      (localFilters.entityTypes && localFilters.entityTypes.length > 0) ||
      (localFilters.eventTypes && localFilters.eventTypes.length > 0) ||
      localFilters.dataPoints
    );
  };

  return (
    <div className="border-b border-gray-200 pb-4">
      {/* Filter Toggle */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
        >
          <svg
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <span>Filters</span>
          {hasActiveFilters() && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              Active
            </span>
          )}
        </button>

        {hasActiveFilters() && (
          <button
            onClick={clearFilters}
            className="text-xs text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Filter Content */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Time Range Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Time Range
            </label>
            <div className="flex flex-wrap gap-2">
              {TIME_RANGE_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => handleTimeRangePreset(preset)}
                  className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors ${
                    localFilters.timeRange &&
                    format(localFilters.timeRange.start, 'yyyy-MM-dd') === format(preset.getValue().start, 'yyyy-MM-dd')
                      ? 'bg-blue-100 text-blue-800 border-blue-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Time Range */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                id="start-date"
                type="datetime-local"
                value={localFilters.timeRange?.start ? format(localFilters.timeRange.start, "yyyy-MM-dd'T'HH:mm") : ''}
                onChange={(e) => handleCustomTimeRange('start', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                id="end-date"
                type="datetime-local"
                value={localFilters.timeRange?.end ? format(localFilters.timeRange.end, "yyyy-MM-dd'T'HH:mm") : ''}
                onChange={(e) => handleCustomTimeRange('end', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Entity Types (only for certain chart types) */}
          {(chartType === 'line' || chartType === 'bar') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Entity Types
              </label>
              <div className="flex flex-wrap gap-2">
                {ENTITY_TYPES.map((entityType) => (
                  <button
                    key={entityType}
                    onClick={() => handleEntityTypeToggle(entityType)}
                    className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors ${
                      localFilters.entityTypes?.includes(entityType)
                        ? 'bg-green-100 text-green-800 border-green-300'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {entityType}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Event Types */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Event Types
            </label>
            <div className="flex flex-wrap gap-2">
              {EVENT_TYPES.map((eventType) => (
                <button
                  key={eventType}
                  onClick={() => handleEventTypeToggle(eventType)}
                  className={`px-3 py-1 text-xs font-medium rounded-md border transition-colors ${
                    localFilters.eventTypes?.includes(eventType)
                      ? 'bg-purple-100 text-purple-800 border-purple-300'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {eventType}
                </button>
              ))}
            </div>
          </div>

          {/* Data Points Limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Data Points
            </label>
            <input
              type="number"
              min="10"
              max="10000"
              step="10"
              value={localFilters.dataPoints || ''}
              onChange={(e) => handleDataPointsChange(e.target.value)}
              placeholder="e.g., 1000"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Limit the number of data points for better performance
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
