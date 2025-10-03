import React, { useState, useEffect } from 'react';
import { HealthCard } from './HealthCard';
import { MetricsChart } from './MetricsChart';
import { EventFeed } from './EventFeed';
import { useHealth } from '../hooks/useHealth';
import { useStatistics } from '../hooks/useStatistics';
import { useEvents } from '../hooks/useEvents';
import { websocketService } from '../services/websocket';
import { ChartData } from '../types';

export const Dashboard: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000);

  const { health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(refreshInterval);
  const { statistics, loading: statsLoading, error: statsError, refresh: refreshStats } = useStatistics('1h', refreshInterval);
  const { events, loading: eventsLoading, error: eventsError, refresh: refreshEvents } = useEvents({ limit: 50 }, 10000);

  // WebSocket connection management
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        setIsConnected(false);
      }
    };

    connectWebSocket();

    const unsubscribe = websocketService.onDisconnect(() => {
      setIsConnected(false);
    });

    return () => {
      unsubscribe();
      websocketService.disconnect();
    };
  }, []);

  // Generate sample chart data for demonstration
  const generateEventRateData = (): ChartData => {
    const labels = [];
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      labels.push(time.getHours().toString().padStart(2, '0') + ':00');
      data.push(Math.floor(Math.random() * 100) + 20);
    }

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
  };

  const generateErrorRateData = (): ChartData => {
    const labels = ['WebSocket', 'Processing', 'Weather API', 'InfluxDB'];
    const data = [
      health?.ingestion_service.websocket_connection.last_error ? 1 : 0,
      health?.ingestion_service.event_processing.error_rate || 0,
      health?.ingestion_service.weather_enrichment.last_error ? 1 : 0,
      health?.ingestion_service.influxdb_storage.write_errors || 0,
    ];

    return {
      labels,
      datasets: [
        {
          label: 'Error Rate',
          data,
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(34, 197, 94, 0.8)',
            'rgba(99, 102, 241, 0.8)',
          ],
          borderColor: [
            'rgba(239, 68, 68, 1)',
            'rgba(245, 158, 11, 1)',
            'rgba(34, 197, 94, 1)',
            'rgba(99, 102, 241, 1)',
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  const handleRefresh = () => {
    refreshHealth();
    refreshStats();
    refreshEvents();
  };

  const handleRefreshIntervalChange = (interval: number) => {
    setRefreshInterval(interval);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Health Dashboard</h1>
              <p className="text-sm text-gray-600">Home Assistant Ingestor Monitoring</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Refresh Controls */}
              <div className="flex items-center space-x-2">
                <select
                  value={refreshInterval}
                  onChange={(e) => handleRefreshIntervalChange(Number(e.target.value))}
                  className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={10000}>10s</option>
                  <option value={30000}>30s</option>
                  <option value={60000}>1m</option>
                  <option value={300000}>5m</option>
                </select>
                
                <button
                  onClick={handleRefresh}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Display */}
        {(healthError || statsError || eventsError) && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  {healthError && <p>Health: {healthError}</p>}
                  {statsError && <p>Statistics: {statsError}</p>}
                  {eventsError && <p>Events: {eventsError}</p>}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Health Overview */}
        <div className="mb-8">
          {health && <HealthCard health={health} loading={healthLoading} />}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <MetricsChart
            data={generateEventRateData()}
            type="line"
            title="Event Rate (Last 24 Hours)"
            loading={statsLoading}
            height={300}
          />
          
          <MetricsChart
            data={generateErrorRateData()}
            type="doughnut"
            title="Service Error Status"
            loading={healthLoading}
            height={300}
          />
        </div>

        {/* Events Feed */}
        <div className="mb-8">
          <EventFeed events={events} loading={eventsLoading} />
        </div>

        {/* Statistics Summary */}
        {statistics && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistics Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {statistics.metrics?.total_events || 0}
                </div>
                <div className="text-sm text-gray-600">Total Events</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {statistics.metrics?.success_rate || 0}%
                </div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {statistics.metrics?.avg_processing_time || 0}ms
                </div>
                <div className="text-sm text-gray-600">Avg Processing Time</div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
