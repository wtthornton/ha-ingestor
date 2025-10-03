import React from 'react';
import { SystemHealth, ServiceStatus } from '../types';
import { clsx } from 'clsx';

interface HealthCardProps {
  health: SystemHealth;
  loading?: boolean;
}

const getStatusColor = (status: ServiceStatus): string => {
  switch (status) {
    case 'healthy':
      return 'text-green-600 bg-green-50 border-green-200';
    case 'degraded':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'unhealthy':
      return 'text-red-600 bg-red-50 border-red-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getStatusIcon = (status: ServiceStatus): string => {
  switch (status) {
    case 'healthy':
      return '✓';
    case 'degraded':
      return '⚠';
    case 'unhealthy':
      return '✗';
    default:
      return '?';
  }
};

export const HealthCard: React.FC<HealthCardProps> = ({ health, loading = false }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          <div className="h-3 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  const { ingestion_service } = health;
  const overallStatus = health.overall_status;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
        <div className={clsx(
          'px-3 py-1 rounded-full text-sm font-medium border',
          getStatusColor(overallStatus)
        )}>
          <span className="mr-1">{getStatusIcon(overallStatus)}</span>
          {overallStatus.toUpperCase()}
        </div>
      </div>

      <div className="space-y-4">
        {/* WebSocket Connection */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">WebSocket Connection</span>
          <div className={clsx(
            'px-2 py-1 rounded text-xs font-medium',
            ingestion_service.websocket_connection.is_connected
              ? 'text-green-600 bg-green-50'
              : 'text-red-600 bg-red-50'
          )}>
            {ingestion_service.websocket_connection.is_connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        {/* Event Processing */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Event Processing</span>
          <div className="text-sm text-gray-900">
            {ingestion_service.event_processing.events_per_minute.toFixed(1)} events/min
          </div>
        </div>

        {/* Weather Enrichment */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Weather Enrichment</span>
          <div className={clsx(
            'px-2 py-1 rounded text-xs font-medium',
            ingestion_service.weather_enrichment.enabled
              ? 'text-green-600 bg-green-50'
              : 'text-gray-600 bg-gray-50'
          )}>
            {ingestion_service.weather_enrichment.enabled ? 'Enabled' : 'Disabled'}
          </div>
        </div>

        {/* InfluxDB Storage */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">InfluxDB Storage</span>
          <div className={clsx(
            'px-2 py-1 rounded text-xs font-medium',
            ingestion_service.influxdb_storage.is_connected
              ? 'text-green-600 bg-green-50'
              : 'text-red-600 bg-red-50'
          )}>
            {ingestion_service.influxdb_storage.is_connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        {/* Error Rate */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Error Rate</span>
          <div className={clsx(
            'text-sm font-medium',
            ingestion_service.event_processing.error_rate > 0.05
              ? 'text-red-600'
              : ingestion_service.event_processing.error_rate > 0.01
              ? 'text-yellow-600'
              : 'text-green-600'
          )}>
            {(ingestion_service.event_processing.error_rate * 100).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-500">
          Last updated: {new Date(health.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
};
