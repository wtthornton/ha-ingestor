import React, { useState, useEffect } from 'react';
import { MobileLayout, MobileCard, MobileSection, MobileButton, MobileGrid } from './MobileLayout';
import { HealthCard } from './HealthCard';
import { StatisticsCard } from './StatisticsCard';
import { EventFeed } from './EventFeed';
import { useHealth } from '../hooks/useHealth';
import { useStatistics } from '../hooks/useStatistics';
import { useEvents } from '../hooks/useEvents';
import { useThemeAware } from '../contexts/ThemeContext';
import { useTouchGestures } from '../hooks/useTouchGestures';
import { 
  ArrowPathIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

export const MobileDashboard: React.FC = () => {
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'health' | 'stats' | 'events'>('overview');
  
  const { isDark } = useThemeAware();
  const { health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(refreshInterval);
  const { statistics, loading: statsLoading, error: statsError, refresh: refreshStats } = useStatistics('1h', refreshInterval);
  const { events, loading: eventsLoading, error: eventsError, refresh: refreshEvents } = useEvents({ limit: 20 }, 10000);

  // Touch gestures for pull-to-refresh
  const { touchHandlers, swipeGesture } = useTouchGestures({
    swipe: {
      callbacks: {
        onSwipeDown: () => {
          if (window.scrollY === 0) {
            handleRefresh();
          }
        },
      },
      options: { minSwipeDistance: 80 }
    }
  });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refreshHealth(),
        refreshStats(),
        refreshEvents(),
      ]);
    } catch (error) {
      console.error('Refresh failed:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const isLoading = healthLoading || statsLoading || eventsLoading;
  const hasError = healthError || statsError || eventsError;

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-design-success" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-design-warning" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-design-error" />;
      default:
        return <ChartBarIcon className="h-5 w-5 text-design-text-secondary" />;
    }
  };

  const renderOverview = () => (
    <div className="space-y-4">
      {/* Quick Status */}
      <MobileCard>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-design-text">System Status</h3>
          <div className="flex items-center space-x-2">
            {getStatusIcon(health?.overall_status)}
            <span className="text-sm font-medium text-design-text capitalize">
              {health?.overall_status || 'Unknown'}
            </span>
          </div>
        </div>
        
        <MobileGrid columns={2} gap="sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-design-text">
              {statistics?.total_events || 0}
            </div>
            <div className="text-xs text-design-text-secondary">Total Events</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-design-text">
              {statistics?.active_entities || 0}
            </div>
            <div className="text-xs text-design-text-secondary">Active Entities</div>
          </div>
        </MobileGrid>
      </MobileCard>

      {/* Recent Events */}
      <MobileSection title="Recent Events">
        <div className="space-y-2">
          {events?.slice(0, 5).map((event) => (
            <div key={event.id} className="flex items-center space-x-3 p-2 rounded-design-md bg-design-background-secondary">
              <div className="flex-shrink-0">
                <div className="w-2 h-2 bg-design-primary rounded-full"></div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-design-text truncate">
                  {event.entity_id}
                </p>
                <p className="text-xs text-design-text-secondary">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </MobileSection>
    </div>
  );

  const renderHealth = () => (
    <div className="space-y-4">
      <HealthCard health={health} loading={healthLoading} />
      
      {healthError && (
        <MobileCard className="border-design-error bg-design-error-light">
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-5 w-5 text-design-error" />
            <span className="text-sm text-design-error-dark">Health data unavailable</span>
          </div>
        </MobileCard>
      )}
    </div>
  );

  const renderStats = () => (
    <div className="space-y-4">
      <StatisticsCard statistics={statistics} loading={statsLoading} />
      
      {statsError && (
        <MobileCard className="border-design-error bg-design-error-light">
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-5 w-5 text-design-error" />
            <span className="text-sm text-design-error-dark">Statistics unavailable</span>
          </div>
        </MobileCard>
      )}
    </div>
  );

  const renderEvents = () => (
    <div className="space-y-4">
      <MobileSection title="Event Feed">
        <EventFeed events={events} loading={eventsLoading} />
      </MobileSection>
      
      {eventsError && (
        <MobileCard className="border-design-error bg-design-error-light">
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-5 w-5 text-design-error" />
            <span className="text-sm text-design-error-dark">Events unavailable</span>
          </div>
        </MobileCard>
      )}
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'health':
        return renderHealth();
      case 'stats':
        return renderStats();
      case 'events':
        return renderEvents();
      default:
        return renderOverview();
    }
  };

  return (
    <MobileLayout {...touchHandlers}>
      {/* Pull-to-refresh indicator */}
      {swipeGesture?.gestureState.isTouching && swipeGesture.gestureState.swipeDirection === 'down' && (
        <div className="fixed top-16 left-0 right-0 z-30 bg-design-primary text-design-text-inverse text-center py-2">
          <div className="flex items-center justify-center space-x-2">
            <ArrowPathIcon className="h-4 w-4 animate-spin" />
            <span className="text-sm">Pull to refresh</span>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mobile-card">
        <div className="flex space-x-1 bg-design-background-secondary rounded-design-md p-1">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'health', label: 'Health', icon: CheckCircleIcon },
            { id: 'stats', label: 'Stats', icon: ChartBarIcon },
            { id: 'events', label: 'Events', icon: ChartBarIcon },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex-1 flex items-center justify-center space-x-1 px-2 py-2 rounded-design-sm
                  text-xs font-medium transition-colors duration-design-fast touch-target
                  ${isActive 
                    ? 'bg-design-primary text-design-text-inverse shadow-design-sm' 
                    : 'text-design-text-secondary hover:text-design-text hover:bg-design-surface-hover'
                  }
                `}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Refresh Controls */}
      <MobileCard>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ArrowPathIcon className={`h-4 w-4 text-design-text-secondary ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm text-design-text-secondary">
              {isRefreshing ? 'Refreshing...' : 'Auto-refresh'}
            </span>
          </div>
          
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="
              px-2 py-1 border border-design-border rounded-design-sm text-xs
              bg-design-surface text-design-text
              focus:outline-none focus:ring-1 focus:ring-design-border-focus
            "
          >
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={300000}>5m</option>
          </select>
          
          <MobileButton
            onClick={handleRefresh}
            disabled={isRefreshing}
            size="sm"
            className="ml-2"
          >
            Refresh
          </MobileButton>
        </div>
      </MobileCard>

      {/* Error State */}
      {hasError && (
        <MobileCard className="border-design-error bg-design-error-light">
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-5 w-5 text-design-error" />
            <div>
              <h3 className="text-sm font-medium text-design-error-dark">Connection Issues</h3>
              <p className="text-xs text-design-error-dark">
                Some data may not be available. Pull down to refresh.
              </p>
            </div>
          </div>
        </MobileCard>
      )}

      {/* Main Content */}
      <div className="space-y-4">
        {renderContent()}
      </div>

      {/* Loading Overlay */}
      {isLoading && !isRefreshing && (
        <div className="fixed inset-0 bg-black bg-opacity-25 flex items-center justify-center z-40">
          <div className="bg-design-surface rounded-design-lg p-6 shadow-design-xl">
            <div className="flex items-center space-x-3">
              <ArrowPathIcon className="h-6 w-6 text-design-primary animate-spin" />
              <span className="text-design-text">Loading...</span>
            </div>
          </div>
        </div>
      )}
    </MobileLayout>
  );
};
