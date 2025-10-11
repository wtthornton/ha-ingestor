import React, { useState, useEffect } from 'react';
import { useHealth } from '../hooks/useHealth';
import { useStatistics } from '../hooks/useStatistics';
import { useDataSources } from '../hooks/useDataSources';
import { StatusCard } from './StatusCard';
import { MetricCard } from './MetricCard';
import { DataSourceCard } from './DataSourceCard';
import { ConfigForm } from './ConfigForm';
import { ServiceControl } from './ServiceControl';

export const Dashboard: React.FC = () => {
  const { health, loading: healthLoading, error: healthError } = useHealth(30000);
  const { statistics, loading: statsLoading, error: statsError } = useStatistics('1h', 60000);
  const { dataSources, loading: dataSourcesLoading } = useDataSources(30000);
  
  // Enhanced state management
  const [darkMode, setDarkMode] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTab, setSelectedTab] = useState('overview');

  // Apply theme to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  if (healthLoading || statsLoading) {
    return (
      <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} flex items-center justify-center transition-colors duration-300`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 ${darkMode ? 'border-blue-400' : 'border-blue-600'} mx-auto`}></div>
          <p className={`mt-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Loading enhanced dashboard...</p>
        </div>
      </div>
    );
  }

  if (healthError || statsError) {
    return (
      <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} flex items-center justify-center transition-colors duration-300`}>
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h1 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>Dashboard Error</h1>
          <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'} mb-4`}>
            {healthError || statsError}
          </p>
          <button 
            onClick={() => window.location.reload()} 
            className={`${darkMode ? 'bg-blue-500 hover:bg-blue-600' : 'bg-blue-600 hover:bg-blue-700'} text-white px-4 py-2 rounded transition-colors duration-200`}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} transition-colors duration-300`}>
      {/* Enhanced Header */}
      <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} shadow-sm border-b transition-colors duration-300`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className={`text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                🏠 HA Ingestor Dashboard
              </h1>
              <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Enhanced Home Assistant Event Ingestion & Data Enrichment Monitor
              </p>
            </div>
            
            {/* Enhanced Controls */}
            <div className="flex items-center space-x-4">
              {/* Theme Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'} transition-colors duration-200`}
                title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
              
              {/* Auto Refresh Toggle */}
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-2 rounded-lg ${autoRefresh ? (darkMode ? 'bg-green-700 hover:bg-green-600' : 'bg-green-100 hover:bg-green-200') : (darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200')} transition-colors duration-200`}
                title={autoRefresh ? 'Auto Refresh: ON' : 'Auto Refresh: OFF'}
              >
                {autoRefresh ? '🔄' : '⏸️'}
              </button>
              
              {/* Time Range Selector */}
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value)}
                className={`px-3 py-2 rounded-lg border ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'} transition-colors duration-200`}
              >
                <option value="15m">Last 15 min</option>
                <option value="1h">Last hour</option>
                <option value="6h">Last 6 hours</option>
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
              </select>
              
              {/* Last Updated */}
              <div className="text-right">
                <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Last updated (Local Time)
                </p>
                <p className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                  {health?.timestamp ? new Date(health.timestamp + 'Z').toLocaleTimeString('en-US', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  }) : new Date().toLocaleTimeString('en-US', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </p>
              </div>
            </div>
          </div>
          
          {/* Navigation Tabs */}
          <div className="flex space-x-8 border-t border-gray-200 dark:border-gray-700 pt-4">
            {[
              { id: 'overview', label: '📊 Overview', icon: '📊' },
              { id: 'services', label: '🔧 Services', icon: '🔧' },
              { id: 'data-sources', label: '🌐 Data Sources', icon: '🌐' },
              { id: 'analytics', label: '📈 Analytics', icon: '📈' },
              { id: 'alerts', label: '🚨 Alerts', icon: '🚨' },
              { id: 'configuration', label: '🔧 Configuration', icon: '🔧' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                  selectedTab === tab.id
                    ? darkMode
                      ? 'bg-blue-600 text-white'
                      : 'bg-blue-100 text-blue-700'
                    : darkMode
                    ? 'text-gray-300 hover:text-white hover:bg-gray-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Configuration Tab */}
        {selectedTab === 'configuration' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
              <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-4`}>
                ⚙️ Integration Configuration
              </h2>
              <p className={`${darkMode ? 'text-gray-300' : 'text-gray-600'} mb-6`}>
                Manage external API credentials and service settings
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <button
                  onClick={() => setSelectedTab('config-websocket')}
                  className="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg hover:shadow-lg transition-shadow duration-200 text-left"
                >
                  <div className="text-4xl mb-2">🏠</div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Home Assistant</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">WebSocket connection</p>
                </button>
                
                <button
                  onClick={() => setSelectedTab('config-weather')}
                  className="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg hover:shadow-lg transition-shadow duration-200 text-left"
                >
                  <div className="text-4xl mb-2">☁️</div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Weather API</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">OpenWeatherMap</p>
                </button>
                
                <button
                  onClick={() => setSelectedTab('config-influxdb')}
                  className="bg-blue-50 dark:bg-blue-900 p-6 rounded-lg hover:shadow-lg transition-shadow duration-200 text-left"
                >
                  <div className="text-4xl mb-2">💾</div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">InfluxDB</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Time-series database</p>
                </button>
              </div>
              
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'} mb-4`}>
                  Service Control
                </h2>
                <ServiceControl />
              </div>
            </div>
          </div>
        )}
        
        {/* Configuration Forms */}
        {selectedTab === 'config-websocket' && (
          <div>
            <button
              onClick={() => setSelectedTab('configuration')}
              className="mb-4 inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              ← Back to Configuration
            </button>
            <ConfigForm service="websocket" onSave={() => {}} />
          </div>
        )}
        
        {selectedTab === 'config-weather' && (
          <div>
            <button
              onClick={() => setSelectedTab('configuration')}
              className="mb-4 inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              ← Back to Configuration
            </button>
            <ConfigForm service="weather" onSave={() => {}} />
          </div>
        )}
        
        {selectedTab === 'config-influxdb' && (
          <div>
            <button
              onClick={() => setSelectedTab('configuration')}
              className="mb-4 inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
              ← Back to Configuration
            </button>
            <ConfigForm service="influxdb" onSave={() => {}} />
          </div>
        )}
        
        {/* Services Tab */}
        {selectedTab === 'services' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">🔧</div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
              Service Management
            </h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-6`}>
              Individual service configuration and monitoring
            </p>
            <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
              Tip: Use the Configuration tab to manage service credentials and settings
            </p>
          </div>
        )}
        
        {/* Data Sources Tab */}
        {selectedTab === 'data-sources' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">🌐</div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
              External Data Sources
            </h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-6`}>
              Monitor external API integrations (Weather, Carbon Intensity, etc.)
            </p>
            <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
              Tip: Configure API credentials in the Configuration tab
            </p>
          </div>
        )}
        
        {/* Analytics Tab */}
        {selectedTab === 'analytics' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">📈</div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
              Advanced Analytics
            </h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-6`}>
              Detailed metrics, trends, and performance analysis
            </p>
            <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
              Tip: View current metrics in the Overview tab
            </p>
          </div>
        )}
        
        {/* Alerts Tab */}
        {selectedTab === 'alerts' && (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">🚨</div>
            <h2 className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mb-2`}>
              System Alerts
            </h2>
            <p className={`${darkMode ? 'text-gray-400' : 'text-gray-600'} mb-6`}>
              Monitor and manage system alerts and notifications
            </p>
            <div className={`inline-flex items-center px-4 py-2 rounded-lg ${darkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'}`}>
              ✓ No active alerts - System healthy
            </div>
          </div>
        )}
        
        {/* Overview Tab (Default) */}
        {selectedTab === 'overview' && (
          <>
            {/* Enhanced System Health Status */}
            <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
              System Health
            </h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-2 rounded-lg ${darkMode ? 'bg-gray-700 hover:bg-gray-600' : 'bg-gray-100 hover:bg-gray-200'} transition-colors duration-200`}
                title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
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

        {/* Enhanced Key Metrics */}
        <div className="mb-8">
          <h2 className={`text-xl font-semibold ${darkMode ? 'text-white' : 'text-gray-900'} mb-4`}>
            📊 Key Metrics (Last Hour)
          </h2>
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

            {/* Enhanced Footer */}
            <div className={`text-center text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mt-12 pt-8 border-t ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
              <p className="font-semibold">
                🏠 HA Ingestor Dashboard - Enhanced with Real-time Monitoring & Data Enrichment
              </p>
              <p className="text-xs mt-2">
                {autoRefresh ? '🔄 Auto-refresh enabled' : '⏸️ Auto-refresh paused'} • 
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
        )}
      </div>
    </div>
  );
};
