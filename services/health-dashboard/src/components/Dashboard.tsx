import React, { useState, useEffect } from 'react';
import { Navigation } from './Navigation';
import { LayoutSwitcher } from './LayoutSwitcher';
import { GridLayout } from './GridLayout';
import { NotificationContainer } from './NotificationContainer';
import { MobileDashboard } from './MobileDashboard';
import { useLayout } from '../contexts/LayoutContext';
import { useHealth } from '../hooks/useHealth';
import { useStatistics } from '../hooks/useStatistics';
import { useEvents } from '../hooks/useEvents';
import { useThemeAware } from '../contexts/ThemeContext';
import { useMobileDetection } from '../hooks/useMobileDetection';
import { websocketService } from '../services/websocket';
import { notificationService } from '../services/notificationService';

export const Dashboard: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000);

  const { layoutState, getCurrentLayoutConfig } = useLayout();
  const { health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(refreshInterval);
  const { statistics, loading: statsLoading, error: statsError, refresh: refreshStats } = useStatistics('1h', refreshInterval);
  const { events, loading: eventsLoading, error: eventsError, refresh: refreshEvents } = useEvents({ limit: 50 }, 10000);
  const { isDark } = useThemeAware();
  const { isMobile } = useMobileDetection();

  // WebSocket connection management
  useEffect(() => {
    const connectWebSocket = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
        
        // Integrate notification service with WebSocket
        notificationService.integrateWithWebSocket(websocketService);
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

  const currentLayout = getCurrentLayoutConfig();
  const isLoading = healthLoading || statsLoading || eventsLoading;
  const hasError = healthError || statsError || eventsError;

  const handleRefresh = () => {
    refreshHealth();
    refreshStats();
    refreshEvents();
  };

  const handleRefreshIntervalChange = (interval: number) => {
    setRefreshInterval(interval);
  };

  // Return mobile dashboard for mobile devices
  if (isMobile) {
    return <MobileDashboard />;
  }

  if (!currentLayout) {
    return (
      <div className="min-h-screen bg-design-background flex items-center justify-center transition-colors duration-design-normal">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-design-text mb-2">Layout Error</h1>
          <p className="text-design-text-secondary">Unable to load dashboard layout</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-design-background transition-colors duration-design-normal">
      <Navigation />

      {/* Dashboard Header */}
      <header className="bg-design-surface shadow-design-sm border-b border-design-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-design-text">Dashboard Overview</h1>
              <p className="text-sm text-design-text-secondary">Home Assistant Ingestor Monitoring</p>
            </div>

            <div className="flex items-center space-x-4">
              {/* Layout Switcher */}
              <LayoutSwitcher />

              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`
                  w-2 h-2 rounded-full transition-colors duration-design-fast
                  ${isConnected ? 'bg-design-success animate-pulse-glow' : 'bg-design-error'}
                `}></div>
                <span className="text-sm text-design-text-secondary">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Refresh Controls */}
              <div className="flex items-center space-x-2">
                <select
                  value={refreshInterval}
                  onChange={(e) => handleRefreshIntervalChange(Number(e.target.value))}
                  className="
                    px-3 py-1 border border-design-border rounded-design-md text-sm
                    bg-design-surface text-design-text
                    focus:outline-none focus:ring-2 focus:ring-design-border-focus focus:border-design-border-focus
                    hover:bg-design-surface-hover transition-colors duration-design-fast
                  "
                >
                  <option value={10000}>10s</option>
                  <option value={30000}>30s</option>
                  <option value={60000}>1m</option>
                  <option value={300000}>5m</option>
                </select>

                <button
                  onClick={handleRefresh}
                  className="
                    px-3 py-1 bg-design-primary text-design-text-inverse rounded-design-md text-sm
                    hover:bg-design-primary-hover focus:outline-none focus:ring-2 focus:ring-design-border-focus
                    transition-all duration-design-fast shadow-design-sm hover:shadow-design-md
                  "
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content with Grid Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-[calc(100vh-200px)]">
          {hasError ? (
            <div className="bg-design-error-light border border-design-error rounded-design-lg p-6 shadow-design-md">
              <h3 className="text-sm font-medium text-design-error-dark">Error Loading Data</h3>
              <div className="mt-2 text-sm text-design-error-dark">
                {healthError && <p>Health: {healthError}</p>}
                {statsError && <p>Statistics: {statsError}</p>}
                {eventsError && <p>Events: {eventsError}</p>}
              </div>
            </div>
          ) : (
            <GridLayout
              layout={currentLayout}
              health={health}
              statistics={statistics}
              events={events}
              loading={isLoading}
              realTime={true}
              onRefresh={handleRefresh}
            />
          )}
        </div>
      </main>

      {/* Notification System */}
      <NotificationContainer />
    </div>
  );
};

export default Dashboard;