import React from 'react';
import { SystemHealth, ServiceStatus } from '../types';
import { clsx } from 'clsx';
import { HealthCardSkeleton } from './SkeletonLoader';
import { StatusIndicator, StatusBadge, ProgressBar } from './StatusIndicator';
import { HealthMetrics, MetricCard } from './HealthMetrics';
import { useStatusAnimation } from '../hooks/useStatusUpdates';

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
    return <HealthCardSkeleton />;
  }

  const { ingestion_service } = health;
  const overallStatus = health.overall_status;
  const { animationClasses } = useStatusAnimation(overallStatus);

  // Convert ServiceStatus to StatusType
  const getStatusType = (status: ServiceStatus): 'healthy' | 'warning' | 'error' | 'unknown' => {
    switch (status) {
      case 'healthy':
        return 'healthy';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'unknown';
    }
  };

  return (
    <div className={`bg-design-surface rounded-design-lg shadow-design-md p-6 hover:shadow-design-lg transition-shadow duration-design-normal ${animationClasses}`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-design-text">System Health</h2>
        <StatusBadge 
          status={getStatusType(overallStatus)} 
          text={overallStatus.toUpperCase()} 
          size="md"
        />
      </div>

      <div className="space-y-4">
        {/* WebSocket Connection */}
        <StatusIndicator
          status={ingestion_service.websocket_connection.is_connected ? 'healthy' : 'error'}
          label="WebSocket Connection"
          value={ingestion_service.websocket_connection.is_connected ? 'Connected' : 'Disconnected'}
          lastUpdated={new Date(health.timestamp)}
          variant="inline"
          size="sm"
        />

        {/* Event Processing */}
        <StatusIndicator
          status="healthy"
          label="Event Processing"
          value={`${ingestion_service.event_processing.events_per_minute.toFixed(1)} events/min`}
          lastUpdated={new Date(health.timestamp)}
          variant="inline"
          size="sm"
        />

        {/* Weather Enrichment */}
        <StatusIndicator
          status={ingestion_service.weather_enrichment.enabled ? 'healthy' : 'unknown'}
          label="Weather Enrichment"
          value={ingestion_service.weather_enrichment.enabled ? 'Enabled' : 'Disabled'}
          lastUpdated={new Date(health.timestamp)}
          variant="inline"
          size="sm"
        />

        {/* InfluxDB Storage */}
        <StatusIndicator
          status={ingestion_service.influxdb_storage.is_connected ? 'healthy' : 'error'}
          label="InfluxDB Storage"
          value={ingestion_service.influxdb_storage.is_connected ? 'Connected' : 'Disconnected'}
          lastUpdated={new Date(health.timestamp)}
          variant="inline"
          size="sm"
        />

        {/* Error Rate */}
        <div className="space-y-2">
          <StatusIndicator
            status={
              ingestion_service.event_processing.error_rate > 0.05
                ? 'error'
                : ingestion_service.event_processing.error_rate > 0.01
                ? 'warning'
                : 'healthy'
            }
            label="Error Rate"
            value={`${(ingestion_service.event_processing.error_rate * 100).toFixed(2)}%`}
            lastUpdated={new Date(health.timestamp)}
            variant="inline"
            size="sm"
          />
          <ProgressBar
            value={ingestion_service.event_processing.error_rate * 100}
            max={10}
            status={
              ingestion_service.event_processing.error_rate > 0.05
                ? 'error'
                : ingestion_service.event_processing.error_rate > 0.01
                ? 'warning'
                : 'healthy'
            }
            showPercentage={false}
          />
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-design-border">
        <div className="text-xs text-design-text-tertiary">
          Last updated: {new Date(health.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
};
