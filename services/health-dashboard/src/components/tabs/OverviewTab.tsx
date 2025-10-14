import React, { useState, useEffect } from 'react';
import { useHealth } from '../../hooks/useHealth';
import { useStatistics } from '../../hooks/useStatistics';
import { useDataSources } from '../../hooks/useDataSources';
import { useAlerts } from '../../hooks/useAlerts';
import { usePerformanceHistory } from '../../hooks/usePerformanceHistory';
import { useDevices } from '../../hooks/useDevices';
import { SkeletonCard } from '../skeletons';
import { SystemStatusHero } from '../SystemStatusHero';
import { CoreSystemCard } from '../CoreSystemCard';
import { PerformanceSparkline } from '../PerformanceSparkline';
import { ServiceDetailsModal, ServiceDetail } from '../ServiceDetailsModal';
import { ServiceHealthResponse } from '../../types/health';
import { apiService } from '../../services/api';
import { TabProps } from './types';

export const OverviewTab: React.FC<TabProps> = ({ darkMode }) => {
  // Enhanced health monitoring (Epic 17.2)
  const [enhancedHealth, setEnhancedHealth] = useState<ServiceHealthResponse | null>(null);
  const [enhancedHealthLoading, setEnhancedHealthLoading] = useState(true);
  
  // Phase 2: Service details modal
  const [selectedService, setSelectedService] = useState<{
    title: string;
    icon: string;
    service: string;
    status: 'healthy' | 'degraded' | 'unhealthy' | 'paused';
    details: ServiceDetail[];
  } | null>(null);
  
  // Phase 3: Sparkline time range control
  const [sparklineTimeRange, setSparklineTimeRange] = useState('1h');

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

  // HTTP polling for health and statistics (30s refresh)
  const { health, loading: healthLoading, error: healthError } = useHealth(30000);
  const { statistics, loading: statsLoading } = useStatistics('1h', 30000);
  const { dataSources } = useDataSources(30000);
  
  // Devices & Integrations data (for HA Integration section)
  const { devices, entities, integrations, loading: devicesLoading } = useDevices();
  
  // Extract metrics from the actual API response structure
  const websocketMetrics = statistics?.metrics?.['websocket-ingestion'];
  const enrichmentMetrics = statistics?.metrics?.['enrichment-pipeline'];

  // Calculate critical alert counts
  const criticalAlerts = alerts.filter(a => a.severity === 'critical' && a.status === 'active');
  const totalCritical = summary?.critical || criticalAlerts.length;

  // Calculate overall system status
  const calculateOverallStatus = (): 'operational' | 'degraded' | 'error' => {
    if (totalCritical > 0) return 'error';
    
    // Check if any core dependencies are unhealthy
    const influxdb = enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB');
    const websocket = enhancedHealth?.dependencies?.find(d => d.name === 'WebSocket Ingestion');
    const enrichment = enhancedHealth?.dependencies?.find(d => d.name === 'Enrichment Pipeline');
    
    const unhealthyDeps = [influxdb, websocket, enrichment].filter(d => d?.status !== 'healthy').length;
    
    if (unhealthyDeps > 0) return 'degraded';
    if (health?.status !== 'healthy') return 'degraded';
    
    return 'operational';
  };

  // Calculate aggregated metrics for Hero section
  const calculateAggregatedMetrics = () => {
    const uptime = enhancedHealth?.metrics?.uptime_human || 'N/A';
    const throughput = websocketMetrics?.events_per_minute || 0;
    
    // Calculate average latency across services
    const latencies = enhancedHealth?.dependencies
      ?.filter(d => d.response_time_ms !== undefined)
      .map(d => d.response_time_ms!) || [];
    const avgLatency = latencies.length > 0 
      ? latencies.reduce((sum, val) => sum + val, 0) / latencies.length 
      : 0;
    
    const errorRate = websocketMetrics?.error_rate || 0;
    
    return { uptime, throughput, latency: avgLatency, errorRate };
  };

  const metrics = calculateAggregatedMetrics();
  const overallStatus = calculateOverallStatus();
  
  // Phase 2: Track performance history for sparkline
  const { history: throughputHistory, stats: throughputStats } = usePerformanceHistory(
    metrics.throughput,
    { maxDataPoints: 60, sampleInterval: 60000 }
  );

  // Calculate HA Integration health metrics
  const calculateHAIntegrationHealth = () => {
    const totalDevices = devices.length;
    const totalEntities = entities.length;
    const totalIntegrations = integrations.length;
    
    // Calculate health percentage based on integration states
    const healthyIntegrations = integrations.filter(i => i.state === 'loaded').length;
    const healthPercent = totalIntegrations > 0 
      ? Math.round((healthyIntegrations / totalIntegrations) * 100) 
      : 0;
    
    // Get top integrations by device count
    const integrationDeviceCounts = new Map<string, number>();
    devices.forEach(device => {
      entities
        .filter(e => e.device_id === device.device_id)
        .forEach(entity => {
          const count = integrationDeviceCounts.get(entity.platform) || 0;
          integrationDeviceCounts.set(entity.platform, count + 1);
        });
    });
    
    const topIntegrations = Array.from(integrationDeviceCounts.entries())
      .map(([platform, deviceCount]) => ({
        platform,
        deviceCount,
        integration: integrations.find(i => i.domain === platform),
        healthy: integrations.find(i => i.domain === platform)?.state === 'loaded'
      }))
      .sort((a, b) => b.deviceCount - a.deviceCount)
      .slice(0, 6);
    
    return {
      totalDevices,
      totalEntities,
      totalIntegrations,
      healthPercent,
      topIntegrations
    };
  };
  
  // Only calculate if we're showing the section
  const haIntegration = devices.length > 0 ? calculateHAIntegrationHealth() : null;

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

      {/* System Status Hero Section - Phase 2: With Trends */}
      {!healthLoading && !enhancedHealthLoading ? (
        <SystemStatusHero
          overallStatus={overallStatus}
          uptime={metrics.uptime}
          throughput={metrics.throughput}
          latency={metrics.latency}
          errorRate={metrics.errorRate}
          lastUpdate={new Date()}
          darkMode={darkMode}
          trends={{
            throughput: throughputStats.previous,
            latency: metrics.latency, // Could track previous latency similarly
            errorRate: metrics.errorRate
          }}
        />
      ) : (
        <div className="mb-8">
          <SkeletonCard variant="metric" />
        </div>
      )}

      {/* Core System Components - Phase 3: With animations */}
      <div className="mb-8">
        <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          📊 Core System Components
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6" role="group" aria-label="Core system components">
          {healthLoading || enhancedHealthLoading ? (
            <>
              <SkeletonCard variant="service" />
              <SkeletonCard variant="service" />
              <SkeletonCard variant="service" />
            </>
          ) : (
            <>
              {/* Ingestion Card - Phase 2: Clickable for details */}
              <CoreSystemCard
                title="INGESTION"
                icon="🔌"
                service="WebSocket Connection"
                status={
                  enhancedHealth?.dependencies?.find(d => d.name === 'WebSocket Ingestion')?.status === 'healthy'
                    ? 'healthy'
                    : 'unhealthy'
                }
                metrics={{
                  primary: {
                    label: 'Events per Minute',
                    value: websocketMetrics?.events_per_minute || 0,
                    unit: 'evt/min'
                  },
                  secondary: {
                    label: 'Total Events',
                    value: websocketMetrics?.total_events_received || 0,
                    unit: 'events'
                  }
                }}
                uptime={enhancedHealth?.metrics?.uptime_human || 'N/A'}
                darkMode={darkMode}
                onExpand={() => setSelectedService({
                  title: 'INGESTION',
                  icon: '🔌',
                  service: 'WebSocket Connection',
                  status: enhancedHealth?.dependencies?.find(d => d.name === 'WebSocket Ingestion')?.status === 'healthy' ? 'healthy' : 'unhealthy',
                  details: [
                    { label: 'Events per Minute', value: websocketMetrics?.events_per_minute || 0, unit: 'evt/min' },
                    { label: 'Total Events Received', value: websocketMetrics?.total_events_received || 0, unit: 'events' },
                    { label: 'Connection Status', value: enhancedHealth?.dependencies?.find(d => d.name === 'WebSocket Ingestion')?.status || 'unknown' },
                    { label: 'Response Time', value: enhancedHealth?.dependencies?.find(d => d.name === 'WebSocket Ingestion')?.response_time_ms?.toFixed(1) || 'N/A', unit: 'ms' },
                    { label: 'Uptime', value: enhancedHealth?.metrics?.uptime_human || 'N/A' }
                  ]
                })}
              />

              {/* Processing Card - Phase 2: Clickable for details */}
              <CoreSystemCard
                title="PROCESSING"
                icon="⚙️"
                service="Enrichment Pipeline"
                status={
                  enhancedHealth?.dependencies?.find(d => d.name === 'Enrichment Pipeline')?.status === 'healthy'
                    ? 'healthy'
                    : enrichmentMetrics?.events_per_minute === 0
                    ? 'paused'
                    : 'unhealthy'
                }
                metrics={{
                  primary: {
                    label: 'Processed per Minute',
                    value: enrichmentMetrics?.events_per_minute || 0,
                    unit: 'proc/min'
                  },
                  secondary: {
                    label: 'Total Processed',
                    value: enrichmentMetrics?.total_events_received || 0,
                    unit: 'events'
                  }
                }}
                uptime={enhancedHealth?.metrics?.uptime_human || 'N/A'}
                darkMode={darkMode}
                onExpand={() => setSelectedService({
                  title: 'PROCESSING',
                  icon: '⚙️',
                  service: 'Enrichment Pipeline',
                  status: enhancedHealth?.dependencies?.find(d => d.name === 'Enrichment Pipeline')?.status === 'healthy' ? 'healthy' : enrichmentMetrics?.events_per_minute === 0 ? 'paused' : 'unhealthy',
                  details: [
                    { label: 'Processed per Minute', value: enrichmentMetrics?.events_per_minute || 0, unit: 'proc/min' },
                    { label: 'Total Processed', value: enrichmentMetrics?.total_events_received || 0, unit: 'events' },
                    { label: 'Connection Status', value: enhancedHealth?.dependencies?.find(d => d.name === 'Enrichment Pipeline')?.status || 'unknown' },
                    { label: 'Response Time', value: enhancedHealth?.dependencies?.find(d => d.name === 'Enrichment Pipeline')?.response_time_ms?.toFixed(1) || 'N/A', unit: 'ms' },
                    { label: 'Uptime', value: enhancedHealth?.metrics?.uptime_human || 'N/A' }
                  ]
                })}
              />

              {/* Storage Card - Phase 2: Clickable for details */}
              <CoreSystemCard
                title="STORAGE"
                icon="🗄️"
                service="InfluxDB Database"
                status={
                  enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status === 'healthy'
                    ? 'healthy'
                    : 'unhealthy'
                }
                metrics={{
                  primary: {
                    label: 'Response Time',
                    value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.response_time_ms?.toFixed(1) || '0',
                    unit: 'ms'
                  },
                  secondary: {
                    label: 'Availability',
                    value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status === 'healthy' ? '99.9' : '0',
                    unit: '%'
                  }
                }}
                uptime={enhancedHealth?.metrics?.uptime_human || 'N/A'}
                darkMode={darkMode}
                onExpand={() => setSelectedService({
                  title: 'STORAGE',
                  icon: '🗄️',
                  service: 'InfluxDB Database',
                  status: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status === 'healthy' ? 'healthy' : 'unhealthy',
                  details: [
                    { label: 'Response Time', value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.response_time_ms?.toFixed(1) || 'N/A', unit: 'ms' },
                    { label: 'Availability', value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status === 'healthy' ? '99.9' : '0', unit: '%' },
                    { label: 'Connection Status', value: enhancedHealth?.dependencies?.find(d => d.name === 'InfluxDB')?.status || 'unknown' },
                    { label: 'Database Type', value: 'InfluxDB 2.7' },
                    { label: 'Uptime', value: enhancedHealth?.metrics?.uptime_human || 'N/A' }
                  ]
                })}
              />
            </>
          )}
        </div>
      </div>

      {/* Phase 2/3: Performance Sparkline with configurable time range */}
      {/* TEMPORARY: Disabled due to null handling issues - will fix separately */}
      {false && throughputHistory.length > 0 && throughputStats.current != null && (
        <div className="mb-8">
          <PerformanceSparkline
            data={throughputHistory}
            current={throughputStats.current}
            peak={throughputStats.peak || 0}
            average={throughputStats.average || 0}
            unit="evt/min"
            darkMode={darkMode}
            selectedTimeRange={sparklineTimeRange}
            onTimeRangeChange={setSparklineTimeRange}
          />
        </div>
      )}

      {/* Home Assistant Integration Status */}
      {/* Re-enabled with comprehensive null safety */}
      {true && <div className="mb-8">
        <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          🏠 Home Assistant Integration
        </h2>
        
        {devicesLoading && devices.length === 0 ? (
          <SkeletonCard variant="metric" />
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {/* Devices Card */}
              <div className={`p-4 rounded-lg shadow border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Devices
                    </p>
                    <p className="text-3xl font-bold mt-1">
                      {haIntegration?.totalDevices || 0}
                    </p>
                  </div>
                  <div className="text-4xl">📱</div>
                </div>
              </div>

              {/* Entities Card */}
              <div className={`p-4 rounded-lg shadow border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Entities
                    </p>
                    <p className="text-3xl font-bold mt-1">
                      {haIntegration?.totalEntities || 0}
                    </p>
                  </div>
                  <div className="text-4xl">🔌</div>
                </div>
              </div>

              {/* Integrations Card */}
              <div className={`p-4 rounded-lg shadow border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Integrations
                    </p>
                    <p className="text-3xl font-bold mt-1">
                      {haIntegration?.totalIntegrations || 0}
                    </p>
                  </div>
                  <div className="text-4xl">🔧</div>
                </div>
              </div>

              {/* Health Card */}
              <div className={`p-4 rounded-lg shadow border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      Health
                    </p>
                    <p className="text-3xl font-bold mt-1">
                      {haIntegration?.healthPercent || 0}%
                    </p>
                  </div>
                  <div className="text-4xl">
                    {(haIntegration?.healthPercent || 0) >= 90 ? '✅' : (haIntegration?.healthPercent || 0) >= 70 ? '⚠️' : '❌'}
                  </div>
                </div>
              </div>
            </div>

            {/* Top Integrations */}
            {(haIntegration?.topIntegrations?.length || 0) > 0 && (
              <div className={`p-6 rounded-lg shadow border ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <h3 className={`text-sm font-semibold mb-4 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  Top Integrations
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {(haIntegration?.topIntegrations || []).map(({ platform, deviceCount, healthy }) => (
                    <button
                      key={platform}
                      onClick={() => {
                        const devicesTab = document.querySelector('[data-tab="devices"]') as HTMLElement;
                        if (devicesTab) devicesTab.click();
                      }}
                      className={`flex items-center justify-between p-3 rounded-lg transition-colors ${
                        darkMode 
                          ? 'bg-gray-750 hover:bg-gray-700 border border-gray-600' 
                          : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <span className="text-lg flex-shrink-0">
                          {healthy ? '✅' : '⚠️'}
                        </span>
                        <div className="flex-1 min-w-0 text-left">
                          <p className={`text-sm font-medium truncate ${
                            darkMode ? 'text-gray-200' : 'text-gray-900'
                          }`}>
                            {platform}
                          </p>
                          <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                            {deviceCount} {deviceCount === 1 ? 'device' : 'devices'}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                
                {/* View All Devices Button */}
                <div className="mt-4 text-center">
                  <button
                    onClick={() => {
                      const devicesTab = document.querySelector('[data-tab="devices"]') as HTMLElement;
                      if (devicesTab) devicesTab.click();
                    }}
                    className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                      darkMode
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    View All Devices →
                  </button>
                </div>
              </div>
            )}

            {/* Empty State */}
            {(haIntegration?.totalDevices || 0) === 0 && (
              <div className={`p-8 rounded-lg shadow border text-center ${
                darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
              }`}>
                <div className="text-6xl mb-4">🏠</div>
                <p className={`text-lg font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  No Home Assistant devices discovered yet
                </p>
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Waiting for Home Assistant connection and device discovery...
                </p>
              </div>
            )}

            {/* Devices API Connection Status */}
            <div className={`mt-4 p-4 rounded-lg shadow border ${
              darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {devicesLoading ? '⏳' : (haIntegration?.totalDevices || 0) > 0 ? '✅' : '⚠️'}
                  </div>
                  <div>
                    <p className={`text-sm font-semibold ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                      HA Devices API Status
                    </p>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {devicesLoading 
                        ? 'Loading device data...' 
                        : (haIntegration?.totalDevices || 0) > 0 
                          ? `Connected - ${haIntegration.totalDevices} devices discovered`
                          : 'Connected - Awaiting device discovery'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    const devicesTab = document.querySelector('[data-tab="devices"]') as HTMLElement;
                    if (devicesTab) devicesTab.click();
                  }}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    darkMode
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                  }`}
                >
                  View Details →
                </button>
              </div>
            </div>
          </>
        )}
      </div>}

      {/* Active Data Sources - Phase 2: Clickable */}
      <div className="mb-8">
        <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          🔗 Active Data Sources
        </h2>
        <div className={`rounded-lg shadow p-6 ${darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'}`}>
          <div className="flex flex-wrap gap-4">
            {Object.entries(dataSources || {}).map(([key, value]) => (
              <button
                key={key}
                onClick={() => {
                  const dataSourcesTab = document.querySelector('[data-tab="data-sources"]') as HTMLElement;
                  if (dataSourcesTab) dataSourcesTab.click();
                }}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                  darkMode 
                    ? 'hover:bg-gray-700' 
                    : 'hover:bg-gray-100'
                }`}
              >
                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <span className="text-xl">
                  {value ? '✅' : '⏸️'}
                </span>
              </button>
            ))}
            {(!dataSources || Object.keys(dataSources).length === 0) && (
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                No active data sources configured
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions - Phase 3: With accessibility */}
      <div className="mb-8">
        <h2 className={`text-xl font-semibold mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ⚡ Quick Actions
        </h2>
        <div className="flex flex-wrap gap-3" role="navigation" aria-label="Quick navigation actions">
          <button
            onClick={() => {
              const logsTab = document.querySelector('[data-tab="logs"]') as HTMLElement;
              if (logsTab) logsTab.click();
            }}
            className={`px-6 py-3 rounded-lg font-medium transition-colors-smooth focus-visible-ring stagger-item ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
            }`}
            aria-label="Navigate to logs tab"
          >
            📜 View Logs
          </button>
          <button
            onClick={() => {
              const depsTab = document.querySelector('[data-tab="dependencies"]') as HTMLElement;
              if (depsTab) depsTab.click();
            }}
            className={`px-6 py-3 rounded-lg font-medium transition-colors-smooth focus-visible-ring stagger-item ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
            }`}
            aria-label="Navigate to dependencies tab to check system dependencies"
          >
            🔗 Check Dependencies
          </button>
          <button
            onClick={() => {
              const servicesTab = document.querySelector('[data-tab="services"]') as HTMLElement;
              if (servicesTab) servicesTab.click();
            }}
            className={`px-6 py-3 rounded-lg font-medium transition-colors-smooth focus-visible-ring stagger-item ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
            }`}
            aria-label="Navigate to services tab to manage services"
          >
            🔧 Manage Services
          </button>
          <button
            onClick={() => {
              const configTab = document.querySelector('[data-tab="configuration"]') as HTMLElement;
              if (configTab) configTab.click();
            }}
            className={`px-6 py-3 rounded-lg font-medium transition-colors-smooth focus-visible-ring stagger-item ${
              darkMode
                ? 'bg-gray-700 hover:bg-gray-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-900'
            }`}
            aria-label="Navigate to configuration tab to adjust settings"
          >
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className={`text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mt-12 pt-8 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <p className="font-semibold">
          🏠 HA Ingestor Dashboard - Real-time System Health Monitoring
        </p>
        <p className="text-xs mt-2">
          {haIntegration?.totalDevices || 0} Devices • {haIntegration?.totalEntities || 0} Entities • {haIntegration?.totalIntegrations || 0} Integrations •{' '}
          {Object.values(dataSources || {}).filter(d => d !== null).length} Data Sources Active •{' '}
          Storage Optimized • Built with React & TypeScript
        </p>
      </div>

      {/* Phase 2: Service Details Modal */}
      {selectedService && (
        <ServiceDetailsModal
          isOpen={true}
          onClose={() => setSelectedService(null)}
          title={selectedService.title}
          icon={selectedService.icon}
          service={selectedService.service}
          status={selectedService.status}
          details={selectedService.details}
          darkMode={darkMode}
        />
      )}
    </>
  );
};
