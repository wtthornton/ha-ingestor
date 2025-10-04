import React from 'react';
import { Statistics } from '../types';

interface StatisticsCardProps {
  statistics?: Statistics;
  loading?: boolean;
}

export const StatisticsCard: React.FC<StatisticsCardProps> = ({ 
  statistics, 
  loading = false 
}) => {
  if (loading) {
    return (
      <div className="bg-design-surface border border-design-border rounded-design-lg p-6 shadow-design-sm">
        <div className="animate-pulse">
          <div className="h-4 bg-design-background-secondary rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-design-background-secondary rounded"></div>
            <div className="h-3 bg-design-background-secondary rounded w-5/6"></div>
            <div className="h-3 bg-design-background-secondary rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!statistics) {
    return (
      <div className="bg-design-surface border border-design-border rounded-design-lg p-6 shadow-design-sm">
        <h3 className="text-lg font-semibold text-design-text mb-4">Statistics</h3>
        <div className="text-center text-design-text-secondary">
          <p>No statistics data available</p>
        </div>
      </div>
    );
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getTrendColor = (trend: number) => {
    if (trend > 0) return 'text-design-success';
    if (trend < 0) return 'text-design-error';
    return 'text-design-text-secondary';
  };

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return '↗';
    if (trend < 0) return '↘';
    return '→';
  };

  return (
    <div className="bg-design-surface border border-design-border rounded-design-lg p-6 shadow-design-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-design-text">Statistics</h3>
        <div className="text-sm text-design-text-secondary">
          {statistics.period} • {new Date(statistics.timestamp).toLocaleTimeString()}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Events */}
        <div className="text-center">
          <div className="text-2xl font-bold text-design-text">
            {formatNumber(statistics.metrics?.total_events || 0)}
          </div>
          <div className="text-sm text-design-text-secondary">Total Events</div>
          {statistics.trends?.total_events !== undefined && (
            <div className={`text-xs ${getTrendColor(statistics.trends.total_events)}`}>
              {getTrendIcon(statistics.trends.total_events)} {Math.abs(statistics.trends.total_events).toFixed(1)}%
            </div>
          )}
        </div>

        {/* Active Entities */}
        <div className="text-center">
          <div className="text-2xl font-bold text-design-text">
            {statistics.metrics?.active_entities || 0}
          </div>
          <div className="text-sm text-design-text-secondary">Active Entities</div>
          {statistics.trends?.active_entities !== undefined && (
            <div className={`text-xs ${getTrendColor(statistics.trends.active_entities)}`}>
              {getTrendIcon(statistics.trends.active_entities)} {Math.abs(statistics.trends.active_entities).toFixed(1)}%
            </div>
          )}
        </div>

        {/* Error Rate */}
        <div className="text-center">
          <div className="text-2xl font-bold text-design-text">
            {statistics.metrics?.error_rate ? (statistics.metrics.error_rate * 100).toFixed(1) + '%' : '0%'}
          </div>
          <div className="text-sm text-design-text-secondary">Error Rate</div>
          {statistics.trends?.error_rate !== undefined && (
            <div className={`text-xs ${getTrendColor(-statistics.trends.error_rate)}`}>
              {getTrendIcon(-statistics.trends.error_rate)} {Math.abs(statistics.trends.error_rate * 100).toFixed(1)}%
            </div>
          )}
        </div>

        {/* Events per Minute */}
        <div className="text-center">
          <div className="text-2xl font-bold text-design-text">
            {formatNumber(statistics.metrics?.events_per_minute || 0)}
          </div>
          <div className="text-sm text-design-text-secondary">Events/min</div>
          {statistics.trends?.events_per_minute !== undefined && (
            <div className={`text-xs ${getTrendColor(statistics.trends.events_per_minute)}`}>
              {getTrendIcon(statistics.trends.events_per_minute)} {Math.abs(statistics.trends.events_per_minute).toFixed(1)}%
            </div>
          )}
        </div>
      </div>

      {/* Alerts Summary */}
      {statistics.alerts && statistics.alerts.length > 0 && (
        <div className="mt-6 pt-6 border-t border-design-border">
          <h4 className="text-sm font-medium text-design-text mb-3">Recent Alerts</h4>
          <div className="space-y-2">
            {statistics.alerts.slice(0, 3).map((alert, index) => (
              <div key={index} className="flex items-center space-x-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${
                  alert.level === 'critical' ? 'bg-design-error' :
                  alert.level === 'error' ? 'bg-design-error' :
                  alert.level === 'warning' ? 'bg-design-warning' :
                  'bg-design-info'
                }`}></div>
                <span className="text-design-text-secondary">{alert.service}</span>
                <span className="text-design-text">{alert.message}</span>
              </div>
            ))}
            {statistics.alerts.length > 3 && (
              <div className="text-xs text-design-text-secondary">
                +{statistics.alerts.length - 3} more alerts
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
