import React from 'react';
import { useHealth } from '../hooks/useHealth';
import { useStatistics } from '../hooks/useStatistics';
import { StatusCard } from './StatusCard';
import { MetricCard } from './MetricCard';

export const Dashboard: React.FC = () => {
  const { health, loading: healthLoading, error: healthError } = useHealth(30000);
  const { statistics, loading: statsLoading, error: statsError } = useStatistics('1h', 60000);

  if (healthLoading || statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (healthError || statsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Dashboard Error</h1>
          <p className="text-gray-600 mb-4">
            {healthError || statsError}
          </p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">HA Ingestor Dashboard</h1>
              <p className="text-gray-600">Home Assistant Event Ingestion Monitor</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Last updated (PST)</p>
              <p className="text-sm font-medium text-gray-900">
                {health?.timestamp ? new Date(health.timestamp + 'Z').toLocaleTimeString('en-US', {
                  timeZone: 'America/Los_Angeles',
                  hour12: true,
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                }) : new Date().toLocaleTimeString('en-US', {
                  timeZone: 'America/Los_Angeles',
                  hour12: true,
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* System Health Status */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Health</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatusCard
              title="Overall Status"
              status={health?.overall_status || 'unhealthy'}
              value={health?.overall_status}
            />
            
            <StatusCard
              title="WebSocket Connection"
              status={health?.ingestion_service?.websocket_connection?.is_connected ? 'connected' : 'disconnected'}
              value={health?.ingestion_service?.websocket_connection?.connection_attempts || 0}
              subtitle="connection attempts"
            />
            
            <StatusCard
              title="Event Processing"
              status={health?.ingestion_service?.event_processing?.status || 'unhealthy'}
              value={health?.ingestion_service?.event_processing?.events_per_minute || 0}
              subtitle="events/min"
            />
            
            <StatusCard
              title="Database Storage"
              status={health?.ingestion_service?.influxdb_storage?.is_connected ? 'connected' : 'disconnected'}
              value={health?.ingestion_service?.influxdb_storage?.write_errors || 0}
              subtitle="write errors"
            />
          </div>
        </div>

        {/* Key Metrics */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Metrics (Last Hour)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              title="Total Events"
              value={health?.ingestion_service?.event_processing?.total_events || 0}
              unit="events"
            />
            
            <MetricCard
              title="Events per Minute"
              value={health?.ingestion_service?.event_processing?.events_per_minute || 0}
              unit="events/min"
            />
            
            <MetricCard
              title="Error Rate"
              value={health?.ingestion_service?.event_processing?.error_rate || 0}
              unit="%"
            />
            
            <MetricCard
              title="Weather API Calls"
              value={health?.ingestion_service?.weather_enrichment?.api_calls || 0}
              unit="calls"
            />
          </div>
        </div>

        {/* Service Status */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Service Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {health?.services && Object.entries(health.services).map(([serviceName, service]) => (
              <StatusCard
                key={serviceName}
                title={serviceName.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                status={service.status}
                value={service.response_time ? `${service.response_time}ms` : undefined}
                subtitle="response time"
              />
            ))}
          </div>
        </div>

        {/* Weather Enrichment */}
        {health?.ingestion_service?.weather_enrichment && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Weather Enrichment</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <StatusCard
                title="Weather Service"
                status={health.ingestion_service.weather_enrichment.enabled ? 'healthy' : 'unhealthy'}
                value={health.ingestion_service.weather_enrichment.enabled ? 'Enabled' : 'Disabled'}
              />
              
              <MetricCard
                title="Cache Hits"
                value={health.ingestion_service.weather_enrichment.cache_hits || 0}
                unit="hits"
              />
              
              <MetricCard
                title="API Calls"
                value={health.ingestion_service.weather_enrichment.api_calls || 0}
                unit="calls"
              />
            </div>
          </div>
        )}

        {/* Alerts */}
        {statistics?.alerts && statistics.alerts.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Alerts</h2>
            <div className="space-y-3">
              {statistics.alerts.map((alert, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${
                    alert.severity === 'error' 
                      ? 'bg-red-50 border-red-200 text-red-800'
                      : alert.severity === 'warning'
                      ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                      : 'bg-blue-50 border-blue-200 text-blue-800'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="text-lg mr-3">
                      {alert.severity === 'error' ? '🚨' : alert.severity === 'warning' ? '⚠️' : 'ℹ️'}
                    </span>
                    <div>
                      <p className="font-medium">{alert.type}</p>
                      <p className="text-sm opacity-90">{alert.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-sm text-gray-500 mt-12">
          <p>HA Ingestor Dashboard - Simple Health Monitor</p>
          <p>Auto-refreshing every 30 seconds</p>
        </div>
      </div>
    </div>
  );
};
