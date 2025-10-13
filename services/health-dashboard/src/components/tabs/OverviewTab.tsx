import React, { useState, useEffect } from 'react';
import { useHealth } from '../../hooks/useHealth';
import { useStatistics } from '../../hooks/useStatistics';
import { useDataSources } from '../../hooks/useDataSources';
import { useRealtimeMetrics } from '../../hooks/useRealtimeMetrics';
import { useAlerts } from '../../hooks/useAlerts';
import { StatusCard } from '../StatusCard';
import { MetricCard } from '../MetricCard';
import { SkeletonCard } from '../skeletons';
import { EnhancedHealthStatus } from '../EnhancedHealthStatus';
import { ServiceHealthResponse } from '../../types/health';
import { apiService } from '../../services/api';
import { TabProps } from './types';

export const OverviewTab: React.FC<TabProps> = ({ darkMode }) => {
  // Enhanced health monitoring (Epic 17.2)
  const [enhancedHealth, setEnhancedHealth] = useState<ServiceHealthResponse | null>(null);
  const [enhancedHealthLoading, setEnhancedHealthLoading] = useState(true);

  // Fetch enhanced health data
  useEffect(() => {
    const fetchEnhancedHealth = async () => {
      try {
        const data = await apiService.getEnhancedHealth();
        setEnhancedHealth(data);
        setEnhancedHealthLoading(false);
      } catch (error) {
        console.error('Failed to fetch enhanced health:', error);
        setEnhancedHealthLoading(false);
      }
    };

    fetchEnhancedHealth();
    const interval = setInterval(fetchEnhancedHealth, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  // Fetch critical alerts for banner (Story 21.6)
  const { alerts, summary } = useAlerts({
    filters: { severity: 'critical' },
    pollInterval: 30000,
    autoRefresh: true
  });

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
  
  // Extract metrics from the actual API response structure
  const websocketMetrics = statistics?.metrics?.['websocket-ingestion'];
  const enrichmentMetrics = statistics?.metrics?.['enrichment-pipeline'];

  // Calculate critical alert counts
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' && a.status === 'active');
  const totalCritical = summary?.critical || criticalAlerts.length;

  return (
    <>
      {/* Critical Alerts Banner (Story 21.6) */}
      {totalCritical > 0 && (
        <div className={`mb-6 rounded-lg shadow-md p-6 border-2 ${
          darkMode 
            ? 'bg-red-900/20 border-red-500/50' 
            : 'bg-red-50 border-red-300'
        }`}>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 flex-1">
              <span className="text-3xl">🚨</span>
              <div>
                <h3 className={`text-lg font-bold ${darkMode ? 'text-red-200' : 'text-red-800'} mb-1`}>
                  {totalCritical} Critical {totalCritical === 1 ? 'Alert' : 'Alerts'} Requiring Immediate Attention
                </h3>
                <p className={`text-sm ${darkMode ? 'text-red-300' : 'text-red-700'}`}>
                  System health is degraded. Review and resolve critical issues immediately.
                </p>
                {criticalAlerts.slice(0, 3).map(alert => (
                  <div key={alert.id} className={`mt-2 text-sm ${darkMode ? 'text-red-200' : 'text-red-800'}`}>
                    <span className="font-medium">• {alert.service}:</span> {alert.message}
                  </div>
                ))}
                {totalCritical > 3 && (
                  <p className={`mt-2 text-sm ${darkMode ? 'text-red-300' : 'text-red-700'}`}>
                    ... and {totalCritical - 3} more
                  </p>
                )}
              </div>
            </div>
            <a
              href="#alerts"
              onClick={(e) => {
                e.preventDefault();
                // Navigate to Alerts tab (would need to implement tab switching)
                const alertsTab = document.querySelector('[data-tab="alerts"]') as HTMLElement;
                if (alertsTab) alertsTab.click();
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
                darkMode
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              View All Alerts →
            </a>
          </div>
        </div>
      )}

      {/* Enhanced Health Status (Epic 17.2) */}
      {!enhancedHealthLoading && enhancedHealth && (
        <div className="mb-8">
          <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
            Service Health & Dependencies
          </h2>
          <EnhancedHealthStatus health={enhancedHealth} darkMode={darkMode} />
        </div>
      )}

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
                status={health?.status === 'healthy' ? 'healthy' : 'unhealthy'}
                value={health?.status || 'unknown'}
              />
              
              <StatusCard
                title="WebSocket Connection"
                status={health?.dependencies?.find(dep => dep.name === 'WebSocket Ingestion')?.status === 'healthy' ? 'connected' : 'disconnected'}
                value={websocketMetrics?.connection_attempts || 0}
                subtitle="connection attempts"
              />
              
              <StatusCard
                title="Event Processing"
                status={websocketMetrics?.events_per_minute > 0 ? 'healthy' : 'unhealthy'}
                value={websocketMetrics?.events_per_minute || 0}
                subtitle="events/min"
              />
              
              <StatusCard
                title="Database Storage"
                status={health?.dependencies?.find(dep => dep.name === 'InfluxDB')?.status === 'healthy' ? 'connected' : 'disconnected'}
                value={websocketMetrics?.error_rate || 0}
                subtitle="error rate %"
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
                value={websocketMetrics?.total_events_received || 0}
                unit="events"
                isLive={true}
              />
              
              <MetricCard
                title="Events per Minute"
                value={websocketMetrics?.events_per_minute || 0}
                unit="events/min"
                isLive={true}
              />
              
              <MetricCard
                title="Error Rate"
                value={websocketMetrics?.error_rate || 0}
                unit="%"
              />
              
              <MetricCard
                title="Enrichment Pipeline"
                value={enrichmentMetrics?.connection_attempts || 0}
                unit="attempts"
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
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
            aria-label="View API health endpoint"
          >
            🔗 API Health
          </a>
          <a 
            href="/api/statistics" 
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
            aria-label="View API statistics endpoint"
          >
            📊 API Statistics
          </a>
          <a 
            href="/api/data-sources" 
            className={`${darkMode ? 'text-blue-400 hover:text-blue-300' : 'text-blue-600 hover:text-blue-500'} transition-colors duration-200`}
            aria-label="View data sources endpoint"
          >
            🌐 Data Sources
          </a>
        </div>
      </div>
    </>
  );
};

