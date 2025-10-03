import React, { useState, useMemo } from 'react';
import { EventData } from '../types';
import { MetricsChart } from './MetricsChart';
import { format, parseISO, startOfHour, subHours } from 'date-fns';

interface DataVisualizationProps {
  events: EventData[];
  loading?: boolean;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
  }[];
}

type ChartType = 'events_over_time' | 'entity_activity' | 'event_types' | 'state_changes';

export const DataVisualization: React.FC<DataVisualizationProps> = ({ events, loading = false }) => {
  const [selectedChart, setSelectedChart] = useState<ChartType>('events_over_time');
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h');

  const filteredEvents = useMemo(() => {
    const now = new Date();
    let startTime: Date;

    switch (timeRange) {
      case '1h':
        startTime = subHours(now, 1);
        break;
      case '6h':
        startTime = subHours(now, 6);
        break;
      case '24h':
        startTime = subHours(now, 24);
        break;
      case '7d':
        startTime = subHours(now, 24 * 7);
        break;
      default:
        startTime = subHours(now, 24);
    }

    return events.filter(event => {
      const eventTime = parseISO(event.timestamp);
      return eventTime >= startTime && eventTime <= now;
    });
  }, [events, timeRange]);

  const eventsOverTimeData = useMemo((): ChartData => {
    const hourlyData = new Map<string, number>();
    
    filteredEvents.forEach(event => {
      const hour = startOfHour(parseISO(event.timestamp));
      const hourKey = format(hour, 'HH:mm');
      hourlyData.set(hourKey, (hourlyData.get(hourKey) || 0) + 1);
    });

    const labels = Array.from(hourlyData.keys()).sort();
    const data = labels.map(label => hourlyData.get(label) || 0);

    return {
      labels,
      datasets: [
        {
          label: 'Events per Hour',
          data,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
        },
      ],
    };
  }, [filteredEvents]);

  const entityActivityData = useMemo((): ChartData => {
    const entityCounts = new Map<string, number>();
    
    filteredEvents.forEach(event => {
      entityCounts.set(event.entity_id, (entityCounts.get(event.entity_id) || 0) + 1);
    });

    // Get top 10 most active entities
    const sortedEntities = Array.from(entityCounts.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    const labels = sortedEntities.map(([entity]) => entity);
    const data = sortedEntities.map(([, count]) => count);

    return {
      labels,
      datasets: [
        {
          label: 'Event Count',
          data,
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(99, 102, 241, 0.8)',
            'rgba(236, 72, 153, 0.8)',
            'rgba(14, 165, 233, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(168, 85, 247, 0.8)',
            'rgba(251, 146, 60, 0.8)',
            'rgba(156, 163, 175, 0.8)',
          ],
          borderColor: [
            'rgba(239, 68, 68, 1)',
            'rgba(245, 158, 11, 1)',
            'rgba(34, 197, 94, 1)',
            'rgba(99, 102, 241, 1)',
            'rgba(236, 72, 153, 1)',
            'rgba(14, 165, 233, 1)',
            'rgba(34, 197, 94, 1)',
            'rgba(168, 85, 247, 1)',
            'rgba(251, 146, 60, 1)',
            'rgba(156, 163, 175, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [filteredEvents]);

  const eventTypesData = useMemo((): ChartData => {
    const typeCounts = new Map<string, number>();
    
    filteredEvents.forEach(event => {
      typeCounts.set(event.event_type, (typeCounts.get(event.event_type) || 0) + 1);
    });

    const labels = Array.from(typeCounts.keys());
    const data = Array.from(typeCounts.values());

    return {
      labels,
      datasets: [
        {
          label: 'Event Count',
          data,
          backgroundColor: [
            'rgba(59, 130, 246, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(239, 68, 68, 0.8)',
            'rgba(168, 85, 247, 0.8)',
          ],
          borderColor: [
            'rgba(59, 130, 246, 1)',
            'rgba(34, 197, 94, 1)',
            'rgba(245, 158, 11, 1)',
            'rgba(239, 68, 68, 1)',
            'rgba(168, 85, 247, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  }, [filteredEvents]);

  const stateChangesData = useMemo((): ChartData => {
    const stateCounts = new Map<string, number>();
    
    filteredEvents
      .filter(event => event.event_type === 'state_changed' && event.new_state)
      .forEach(event => {
        const state = event.new_state!.state;
        stateCounts.set(state, (stateCounts.get(state) || 0) + 1);
      });

    const labels = Array.from(stateCounts.keys());
    const data = Array.from(stateCounts.values());

    return {
      labels,
      datasets: [
        {
          label: 'State Changes',
          data,
          backgroundColor: labels.map((_, index) => {
            const colors = [
              'rgba(34, 197, 94, 0.8)',   // green for 'on'
              'rgba(239, 68, 68, 0.8)',   // red for 'off'
              'rgba(59, 130, 246, 0.8)',  // blue for other states
              'rgba(245, 158, 11, 0.8)',  // yellow
              'rgba(168, 85, 247, 0.8)',  // purple
            ];
            return colors[index % colors.length];
          }),
          borderColor: labels.map((_, index) => {
            const colors = [
              'rgba(34, 197, 94, 1)',
              'rgba(239, 68, 68, 1)',
              'rgba(59, 130, 246, 1)',
              'rgba(245, 158, 11, 1)',
              'rgba(168, 85, 247, 1)',
            ];
            return colors[index % colors.length];
          }),
          borderWidth: 1,
        },
      ],
    };
  }, [filteredEvents]);

  const getChartData = (): ChartData => {
    switch (selectedChart) {
      case 'events_over_time':
        return eventsOverTimeData;
      case 'entity_activity':
        return entityActivityData;
      case 'event_types':
        return eventTypesData;
      case 'state_changes':
        return stateChangesData;
      default:
        return eventsOverTimeData;
    }
  };

  const getChartType = (): 'line' | 'bar' | 'doughnut' => {
    switch (selectedChart) {
      case 'events_over_time':
        return 'line';
      case 'entity_activity':
        return 'bar';
      case 'event_types':
        return 'doughnut';
      case 'state_changes':
        return 'doughnut';
      default:
        return 'line';
    }
  };

  const getChartTitle = (): string => {
    switch (selectedChart) {
      case 'events_over_time':
        return 'Events Over Time';
      case 'entity_activity':
        return 'Most Active Entities';
      case 'event_types':
        return 'Event Types Distribution';
      case 'state_changes':
        return 'State Changes Distribution';
      default:
        return 'Events Over Time';
    }
  };

  const chartData = getChartData();
  const chartType = getChartType();
  const chartTitle = getChartTitle();

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Data Visualization</h2>
        <div className="flex items-center space-x-4">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>

          {/* Chart Type Selector */}
          <select
            value={selectedChart}
            onChange={(e) => setSelectedChart(e.target.value as ChartType)}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="events_over_time">Events Over Time</option>
            <option value="entity_activity">Entity Activity</option>
            <option value="event_types">Event Types</option>
            <option value="state_changes">State Changes</option>
          </select>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{filteredEvents.length}</div>
          <div className="text-sm text-blue-800">Total Events</div>
        </div>
        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {new Set(filteredEvents.map(e => e.entity_id)).size}
          </div>
          <div className="text-sm text-green-800">Unique Entities</div>
        </div>
        <div className="text-center p-4 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {new Set(filteredEvents.map(e => e.event_type)).size}
          </div>
          <div className="text-sm text-purple-800">Event Types</div>
        </div>
        <div className="text-center p-4 bg-yellow-50 rounded-lg">
          <div className="text-2xl font-bold text-yellow-600">
            {filteredEvents.filter(e => e.event_type === 'state_changed').length}
          </div>
          <div className="text-sm text-yellow-800">State Changes</div>
        </div>
      </div>

      {/* Chart */}
      <div className="mb-4">
        <MetricsChart
          data={chartData}
          type={chartType}
          title={chartTitle}
          loading={loading}
          height={400}
        />
      </div>

      {/* Chart Description */}
      <div className="text-sm text-gray-600">
        {selectedChart === 'events_over_time' && (
          <p>Shows the distribution of events over time in hourly intervals for the selected time range.</p>
        )}
        {selectedChart === 'entity_activity' && (
          <p>Displays the top 10 most active entities by event count in the selected time range.</p>
        )}
        {selectedChart === 'event_types' && (
          <p>Shows the distribution of different event types in the selected time range.</p>
        )}
        {selectedChart === 'state_changes' && (
          <p>Displays the distribution of state changes for entities in the selected time range.</p>
        )}
      </div>
    </div>
  );
};
