import React from 'react';
import { useHealth } from '../../hooks/useHealth';
import { useStatistics } from '../../hooks/useStatistics';
import { useDataSources } from '../../hooks/useDataSources';
import { useRealtimeMetrics } from '../../hooks/useRealtimeMetrics';
import { StatusCard } from '../StatusCard';
import { MetricCard } from '../MetricCard';
import { SkeletonCard } from '../skeletons';
import { TabProps } from './types';

export const OverviewTab: React.FC<TabProps> = ({ darkMode }) => {
  // Real-time WebSocket metrics (Epic 15.1)
  const {
    metrics: realtimeMetrics,
    error: wsError,
  } = useRealtimeMetrics({ enabled: true });
  
  // Fallback HTTP polling (keep for compatibility)
  const { health: httpHealth, loading: httpHealthLoading, error: httpHealthError } = useHealth(30000);
  const { statistics: httpStats, loading: httpStatsLoading } = useStatistics('1h', 60000);
  const { dataSources } = useDataSources(30000);
  
  // Use WebSocket data if available, fallback to HTTP
  const health = realtimeMetrics?.health || httpHealth;
  const statistics = realtimeMetrics?.statistics || httpStats;
  const healthLoading = realtimeMetrics === null && httpHealthLoading;
  const statsLoading = realtimeMetrics === null && httpStatsLoading;

  return (
    <>
      {/* System Health Status */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            System Health
          </h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => window.location.reload()}
              className={`p-2 rounded-lg ${darkMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-100 hover:bg-blue-200'} transition-colors duration-200`}
              title="Refresh Dashboard"
            >
              🔄
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {healthLoading ? (
            <>
              <SkeletonCard variant="service" />
              <SkeletonCard variant="service" />
              <SkeletonCard variant="service" />
              <SkeletonCard variant="service" />
            </>
          ) : (
            <div className="contents content-fade-in">
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
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="mb-8">
        <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'} mb-4`}>
          📊 Key Metrics (Last Hour)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statsLoading ? (
            <>
              <SkeletonCard variant="metric" />
              <SkeletonCard variant="metric" />
              <SkeletonCard variant="metric" />
              <SkeletonCard variant="metric" />
            </>
          ) : (
            <div className="contents content-fade-in">
              <MetricCard
                title="Total Events"
                value={health?.ingestion_service?.event_processing?.total_events || 0}
                unit="events"
                isLive={true}
              />
              
              <MetricCard
                title="Events per Minute"
                value={health?.ingestion_service?.event_processing?.events_per_minute || 0}
                unit="events/min"
                isLive={true}
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
                isLive={true}
              />
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className={`text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mt-12 pt-8 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <p className="font-semibold">
          🏠 HA Ingestor Dashboard - Enhanced with Real-time Monitoring & Data Enrichment
        </p>
        <p className="text-xs mt-2">
          {Object.values(dataSources || {}).filter(d => d !== null).length} Data Sources Active • 
          Storage Optimized • Built with React & TypeScript
        </p>
        <div className="mt-4 flex justify-center space-x-6 text-xs">
          <a 
            href="/api/health" 
            target="_blank" 
            rel="noopener noreferrer"
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
          >
            🔗 API Health
          </a>
          <a 
            href="/api/statistics" 
            target="_blank" 
            rel="noopener noreferrer"
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
          >
            📊 API Statistics
          </a>
          <a 
            href="/api/data-sources" 
            target="_blank" 
            rel="noopener noreferrer"
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
          >
            🌐 Data Sources
          </a>
        </div>
      </div>
    </>
  );
};

