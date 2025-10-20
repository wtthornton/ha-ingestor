/**
 * AnalyticsPanel Component (REFACTORED)
 * 
 * System performance analytics with charts and trends
 * Epic 13.2: System Performance Analytics
 * 
 * REFACTORING: Story 32.1
 * - Extracted data fetching to useAnalyticsData hook
 * - Extracted helper functions to analyticsHelpers
 * - Created sub-components for loading, error, filters
 * - Reduced complexity from 54 to <15
 */

import React, { useState } from 'react';
import { MiniChart } from './charts/MiniChart';
import { useAnalyticsData, type TimeRange } from '../hooks/useAnalyticsData';
import { getTrendIcon, getTrendColor } from '../utils/analyticsHelpers';
import { AnalyticsLoadingState } from './analytics/AnalyticsLoadingState';
import { AnalyticsErrorState } from './analytics/AnalyticsErrorState';
import { AnalyticsFilters } from './analytics/AnalyticsFilters';

interface AnalyticsPanelProps {
  darkMode: boolean;
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({ darkMode }): JSX.Element | null => {
  const [timeRange, setTimeRange] = useState<TimeRange>('1h');
  
  // Use custom hook for data fetching
  const { data: analytics, loading, error, lastUpdate, refetch } = useAnalyticsData(timeRange);

  // Handle loading state
  if (loading) {
    return <AnalyticsLoadingState />;
  }

  // Handle error state
  if (error) {
    return (
      <AnalyticsErrorState
        message={error}
        onRetry={refetch}
        darkMode={darkMode}
      />
    );
  }

  // Handle no data
  if (!analytics) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <AnalyticsFilters
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        lastUpdate={lastUpdate}
        darkMode={darkMode}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Events */}
        <div className={`rounded-lg shadow-md p-4 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Total Events</p>
              <p className={`text-2xl font-bold mt-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {analytics.summary.totalEvents.toLocaleString()}
              </p>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </div>

        {/* Success Rate */}
        <div className={`rounded-lg shadow-md p-4 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Success Rate</p>
              <p className={`text-2xl font-bold mt-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {analytics.summary.successRate.toFixed(2)}%
              </p>
            </div>
            <div className="text-3xl">✅</div>
          </div>
        </div>

        {/* Avg Latency */}
        <div className={`rounded-lg shadow-md p-4 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Avg Latency</p>
              <p className={`text-2xl font-bold mt-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {analytics.summary.avgLatency.toFixed(0)}ms
              </p>
            </div>
            <div className="text-3xl">⚡</div>
          </div>
        </div>

        {/* Uptime */}
        <div className={`rounded-lg shadow-md p-4 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Uptime</p>
              <p className={`text-2xl font-bold mt-1 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                {analytics.summary.uptime.toFixed(2)}%
              </p>
            </div>
            <div className="text-3xl">🔄</div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Events Per Minute */}
        <MetricCard
          title="Events Per Minute"
          metric={analytics.eventsPerMinute}
          darkMode={darkMode}
          icon="📨"
        />

        {/* API Response Time */}
        <MetricCard
          title="API Response Time"
          metric={analytics.apiResponseTime}
          darkMode={darkMode}
          icon="⏱️"
          unit="ms"
        />

        {/* Database Latency */}
        <MetricCard
          title="Database Latency"
          metric={analytics.databaseLatency}
          darkMode={darkMode}
          icon="💾"
          unit="ms"
        />

        {/* Error Rate */}
        <MetricCard
          title="Error Rate"
          metric={analytics.errorRate}
          darkMode={darkMode}
          icon="⚠️"
          unit="%"
        />
      </div>
    </div>
  );
};

/**
 * MetricCard Component
 * 
 * Displays a single metric with chart and statistics
 * Extracted to reduce complexity of main component
 */
interface MetricCardProps {
  title: string;
  metric: {
    current: number;
    peak: number;
    average: number;
    min: number;
    trend: 'up' | 'down' | 'stable';
    data: Array<{ timestamp: string; value: number }>;
  };
  darkMode: boolean;
  icon: string;
  unit?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  metric,
  darkMode,
  icon,
  unit = ''
}): JSX.Element => {
  const trendIcon = getTrendIcon(metric.trend);
  const trendColor = getTrendColor(metric.trend, darkMode);

  return (
    <div className={`rounded-lg shadow-md p-6 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-lg font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          {icon} {title}
        </h3>
        <span className={`text-sm ${trendColor}`}>
          {trendIcon} {metric.trend}
        </span>
      </div>

      {/* Current Value */}
      <div className={`text-3xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
        {metric.current.toFixed(2)}{unit}
      </div>

      {/* Chart */}
      <div className="mb-4" style={{ height: '120px' }}>
        <MiniChart
          data={metric.data}
          darkMode={darkMode}
          trend={metric.trend}
        />
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-700">
        <div>
          <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Peak</p>
          <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {metric.peak.toFixed(2)}{unit}
          </p>
        </div>
        <div>
          <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Avg</p>
          <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {metric.average.toFixed(2)}{unit}
          </p>
        </div>
        <div>
          <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>Min</p>
          <p className={`text-sm font-semibold ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {metric.min.toFixed(2)}{unit}
          </p>
        </div>
      </div>
    </div>
  );
};

