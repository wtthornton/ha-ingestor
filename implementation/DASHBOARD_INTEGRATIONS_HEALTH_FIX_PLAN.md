# Dashboard Integrations & Health Fix Plan
## Enhanced with Context7 KB Best Practices & Modern React Patterns

## Executive Summary

The dashboard at localhost:3000 shows critical issues with the "Integrations" and "Health" sections:
- **Health**: 0% with ❌ icon (critical system health issue)
- **Integrations**: 0 with 🔧 icon (no integrations discovered)

This enhanced plan addresses root causes and implements comprehensive improvements using Context7 KB best practices, modern React/TypeScript patterns, and proven dashboard UX principles.

## Context7 KB Best Practices Integration

### Modern React/TypeScript Patterns
- **Component Architecture**: Use compound components pattern for complex dashboard widgets
- **State Management**: Implement React Query for server state with optimistic updates
- **Type Safety**: Comprehensive TypeScript interfaces with strict null checks
- **Performance**: React.memo, useMemo, useCallback for expensive operations
- **Accessibility**: WCAG 2.1 AA compliance with proper ARIA labels and keyboard navigation

### Dashboard UX Best Practices
- **Information Hierarchy**: Critical metrics at top, details below (F-pattern layout)
- **Progressive Disclosure**: Overview → Details → Actions flow
- **Visual Consistency**: Consistent color schemes and spacing (design system)
- **Real-time Updates**: WebSocket integration with graceful degradation
- **Error Boundaries**: Comprehensive error handling with recovery actions

### Integration Monitoring Patterns
- **Health Scoring**: Multi-factor health calculation with weighted components
- **Status Indicators**: Clear visual states (healthy, degraded, critical) with color coding
- **Drill-down Navigation**: Seamless navigation from summary to detailed views
- **Historical Analysis**: Trend visualization with configurable time ranges
- **Proactive Alerts**: Threshold-based alerts with escalation paths

## Current State Analysis

### Health Section Issues
- **Root Cause**: Health percentage calculated as `(healthyIntegrations / totalIntegrations) * 100`
- **Problem**: No integrations have `state === 'loaded'`, resulting in 0% health
- **Data Source**: InfluxDB `config_entries` measurement via `/api/integrations` endpoint
- **Calculation Logic**: Located in `OverviewTab.tsx` lines 126-130
- **UX Issue**: Single metric doesn't provide actionable insights

### Integrations Section Issues  
- **Root Cause**: Integration discovery not working properly
- **Problem**: No integrations being stored in InfluxDB `config_entries` measurement
- **Data Source**: Home Assistant WebSocket events → InfluxDB storage
- **Storage Logic**: `websocket-ingestion` service should store config entries
- **UX Issue**: No management capabilities or detailed views

### Click Behavior Issues
- **Current**: Cards navigate to existing tabs (devices, data-sources)
- **Missing**: Dedicated management pages for integrations and health details
- **Problem**: No proper click handlers or dedicated routes
- **UX Issue**: Violates progressive disclosure principle

## Phase 1: Immediate Health Investigation & Restoration (HIGH PRIORITY)

### 1.1 Diagnose Integration Discovery Failure
**Goal**: Identify why integrations are not being discovered and stored

**Tasks**:
- [ ] Check WebSocket connection status to Home Assistant
- [ ] Verify `config_entries` events are being received
- [ ] Audit InfluxDB storage of integration data
- [ ] Test integration discovery service

**Implementation**:
```bash
# Check WebSocket service logs
docker logs ha-ingestor-websocket-ingestion-1

# Check InfluxDB for config_entries data
curl -G "http://localhost:8086/api/v2/query" \
  --data-urlencode "org=homeassistant" \
  --data-urlencode "query=from(bucket: \"home_assistant_events\") |> range(start: -7d) |> filter(fn: (r) => r[\"_measurement\"] == \"config_entries\") |> count()"
```

### 1.2 Fix Integration Data Storage
**Goal**: Ensure integration data flows from HA → InfluxDB → Dashboard

**Tasks**:
- [ ] Fix `websocket-ingestion` service to properly store config entries
- [ ] Implement proper error handling for integration discovery
- [ ] Add integration state monitoring and alerts

**Code Changes**:
- Update `websocket-ingestion/src/event_processor.py` to handle `config_entry` events
- Ensure `config_entries` measurement is properly written to InfluxDB
- Add integration health monitoring

### 1.3 Implement Enhanced Health Status Calculation
**Goal**: Multi-factor health calculation with Context7 KB best practices

**Enhanced Health Calculation Strategy**:
```typescript
// services/health-dashboard/src/hooks/useHealthCalculation.ts
interface HealthFactors {
  integrations: number;      // Weight: 0.3
  services: number;          // Weight: 0.4  
  dependencies: number;      // Weight: 0.2
  performance: number;        // Weight: 0.1
}

interface HealthStatus {
  overall: number;
  factors: HealthFactors;
  status: 'healthy' | 'degraded' | 'critical';
  lastUpdated: string;
  trends: HealthTrend[];
}

export const useHealthCalculation = (): HealthStatus => {
  const [integrations] = useIntegrations();
  const [services] = useServices();
  const [dependencies] = useDependencies();
  const [performance] = usePerformanceMetrics();

  const calculateHealth = useMemo(() => {
    const factors: HealthFactors = {
      integrations: calculateIntegrationHealth(integrations),
      services: calculateServiceHealth(services),
      dependencies: calculateDependencyHealth(dependencies),
      performance: calculatePerformanceHealth(performance)
    };

    const weights = { integrations: 0.3, services: 0.4, dependencies: 0.2, performance: 0.1 };
    const overall = Object.entries(factors).reduce(
      (sum, [key, value]) => sum + (value * weights[key as keyof HealthFactors]), 0
    );

    const status = overall >= 90 ? 'healthy' : overall >= 70 ? 'degraded' : 'critical';

    return { overall: Math.round(overall), factors, status, lastUpdated: new Date().toISOString(), trends: [] };
  }, [integrations, services, dependencies, performance]);

  return calculateHealth;
};
```

**Implementation Tasks**:
- [ ] Create weighted health calculation system
- [ ] Implement health trend tracking
- [ ] Add health status indicators with proper color coding
- [ ] Create health breakdown visualization
- [ ] Add health history and analytics

## Phase 2: Enhanced Click Behaviors & Dedicated Pages

### 2.1 Create Enhanced Integrations Management Page
**Goal**: Dedicated page with Context7 KB best practices for integration management

**Enhanced Features with Modern Patterns**:
- **Compound Component Architecture**: Modular, reusable integration components
- **React Query Integration**: Optimistic updates with server state management
- **Real-time Updates**: WebSocket integration for live status updates
- **Advanced Filtering**: Multi-criteria filtering with URL state persistence
- **Bulk Operations**: Select multiple integrations for batch actions
- **Integration Wizard**: Step-by-step integration setup with validation

**Implementation with TypeScript Best Practices**:
```typescript
// services/health-dashboard/src/components/tabs/IntegrationsTab.tsx
interface Integration {
  id: string;
  name: string;
  domain: string;
  status: 'loaded' | 'not_loaded' | 'setup_in_progress' | 'failed';
  health: 'healthy' | 'degraded' | 'critical';
  lastSeen: string;
  deviceCount: number;
  entityCount: number;
  configuration: IntegrationConfig;
}

interface IntegrationFilters {
  status: Integration['status'][];
  health: Integration['health'][];
  domain: string[];
  search: string;
}

export const IntegrationsTab: React.FC<TabProps> = ({ darkMode }) => {
  const [filters, setFilters] = useState<IntegrationFilters>({
    status: [],
    health: [],
    domain: [],
    search: ''
  });
  
  const [selectedIntegrations, setSelectedIntegrations] = useState<Set<string>>(new Set());
  const [showWizard, setShowWizard] = useState(false);

  // React Query for server state management
  const { data: integrations, isLoading, error, refetch } = useQuery({
    queryKey: ['integrations', filters],
    queryFn: () => fetchIntegrations(filters),
    refetchInterval: 30000, // 30s refresh
    staleTime: 10000, // 10s stale time
  });

  const integrationMutation = useMutation({
    mutationFn: updateIntegration,
    onSuccess: () => {
      queryClient.invalidateQueries(['integrations']);
      toast.success('Integration updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update integration: ${error.message}`);
    }
  });

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <IntegrationHeader 
        onAddIntegration={() => setShowWizard(true)}
        onRefresh={refetch}
        selectedCount={selectedIntegrations.size}
        onBulkAction={handleBulkAction}
      />
      
      {/* Advanced Filters */}
      <IntegrationFilters 
        filters={filters}
        onFiltersChange={setFilters}
        integrationCount={integrations?.length || 0}
      />
      
      {/* Integration Grid with Virtualization */}
      <IntegrationGrid
        integrations={integrations}
        loading={isLoading}
        error={error}
        selectedIntegrations={selectedIntegrations}
        onSelectionChange={setSelectedIntegrations}
        onIntegrationClick={handleIntegrationClick}
      />
      
      {/* Integration Details Modal */}
      <IntegrationDetailsModal
        integration={selectedIntegration}
        onClose={() => setSelectedIntegration(null)}
        onUpdate={integrationMutation.mutate}
      />
      
      {/* Integration Setup Wizard */}
      {showWizard && (
        <IntegrationWizard
          onClose={() => setShowWizard(false)}
          onComplete={handleIntegrationSetup}
        />
      )}
    </div>
  );
};
```

**Accessibility & Performance Features**:
- [ ] Virtual scrolling for large integration lists
- [ ] Keyboard navigation support
- [ ] Screen reader compatibility
- [ ] Loading skeletons and error boundaries
- [ ] Optimistic updates with rollback

### 2.2 Create Advanced Health Details Page
**Goal**: Comprehensive health monitoring with Context7 KB best practices

**Enhanced Features with Modern Patterns**:
- **Real-time Health Monitoring**: WebSocket integration for live updates
- **Multi-dimensional Health Analysis**: Service, dependency, and performance metrics
- **Interactive Health Timeline**: Historical trends with zoom and pan
- **Predictive Health Analytics**: ML-based health predictions
- **Automated Troubleshooting**: AI-powered diagnostic suggestions
- **Health Alerts Management**: Configurable thresholds and notifications

**Implementation with Advanced TypeScript Patterns**:
```typescript
// services/health-dashboard/src/components/tabs/HealthTab.tsx
interface HealthMetrics {
  timestamp: string;
  overall: number;
  services: ServiceHealth[];
  dependencies: DependencyHealth[];
  performance: PerformanceMetrics;
  alerts: HealthAlert[];
}

interface HealthTrend {
  period: string;
  average: number;
  min: number;
  max: number;
  trend: 'improving' | 'stable' | 'degrading';
}

export const HealthTab: React.FC<TabProps> = ({ darkMode }) => {
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState<keyof HealthMetrics>('overall');
  const [showPredictions, setShowPredictions] = useState(false);

  // Real-time health data with React Query
  const { data: currentHealth, isLoading } = useQuery({
    queryKey: ['health', 'current'],
    queryFn: fetchCurrentHealth,
    refetchInterval: 5000, // 5s refresh for real-time
  });

  const { data: healthHistory } = useQuery({
    queryKey: ['health', 'history', timeRange],
    queryFn: () => fetchHealthHistory(timeRange),
    refetchInterval: 30000, // 30s refresh for history
  });

  const { data: healthTrends } = useQuery({
    queryKey: ['health', 'trends', timeRange],
    queryFn: () => fetchHealthTrends(timeRange),
  });

  // WebSocket for real-time updates
  useWebSocket('/ws/health', {
    onMessage: (event) => {
      const healthUpdate = JSON.parse(event.data);
      queryClient.setQueryData(['health', 'current'], healthUpdate);
    }
  });

  return (
    <div className="space-y-6">
      {/* Health Overview Dashboard */}
      <HealthOverview 
        health={currentHealth}
        loading={isLoading}
        onMetricSelect={setSelectedMetric}
      />
      
      {/* Interactive Health Timeline */}
      <HealthTimeline
        data={healthHistory}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        selectedMetric={selectedMetric}
        onMetricSelect={setSelectedMetric}
      />
      
      {/* Health Breakdown Grid */}
      <HealthBreakdownGrid
        services={currentHealth?.services}
        dependencies={currentHealth?.dependencies}
        performance={currentHealth?.performance}
      />
      
      {/* Predictive Analytics */}
      {showPredictions && (
        <PredictiveHealthAnalytics
          trends={healthTrends}
          onClose={() => setShowPredictions(false)}
        />
      )}
      
      {/* Automated Troubleshooting */}
      <TroubleshootingPanel
        health={currentHealth}
        onRunDiagnostics={runAutomatedDiagnostics}
      />
      
      {/* Health Alerts Management */}
      <HealthAlertsManager
        alerts={currentHealth?.alerts}
        onConfigureAlerts={configureHealthAlerts}
      />
    </div>
  );
};
```

**Advanced Features**:
- [ ] Real-time WebSocket health updates
- [ ] Interactive charts with Chart.js/D3.js
- [ ] Predictive health analytics with ML
- [ ] Automated troubleshooting suggestions
- [ ] Configurable health thresholds
- [ ] Health trend analysis and forecasting

### 2.3 Enhanced Dashboard Card Click Behaviors
**Goal**: Implement Context7 KB best practices for interactive dashboard cards

**Enhanced Click Behavior Features**:
- **Progressive Disclosure**: Smooth transitions from overview to detailed views
- **Context Preservation**: Maintain user context during navigation
- **Loading States**: Immediate feedback with skeleton loaders
- **Error Boundaries**: Graceful error handling with recovery options
- **Accessibility**: Full keyboard navigation and screen reader support

**Implementation with Modern React Patterns**:
```typescript
// services/health-dashboard/src/components/DashboardCard.tsx
interface DashboardCardProps {
  title: string;
  value: string | number;
  icon: string;
  status: 'healthy' | 'degraded' | 'critical' | 'loading';
  onClick?: () => void;
  href?: string;
  loading?: boolean;
  error?: string;
  children?: React.ReactNode;
}

export const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  icon,
  status,
  onClick,
  href,
  loading = false,
  error,
  children
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = useCallback(() => {
    if (loading || error) return;
    
    // Add haptic feedback for mobile
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
    
    onClick?.();
  }, [loading, error, onClick]);

  const cardClasses = useMemo(() => {
    const baseClasses = "relative p-6 rounded-xl shadow-sm border transition-all duration-200 cursor-pointer";
    const statusClasses = {
      healthy: "bg-green-50 border-green-200 hover:bg-green-100",
      degraded: "bg-yellow-50 border-yellow-200 hover:bg-yellow-100", 
      critical: "bg-red-50 border-red-200 hover:bg-red-100",
      loading: "bg-gray-50 border-gray-200"
    };
    const interactionClasses = isPressed ? "scale-95" : isHovered ? "scale-105 shadow-lg" : "";
    
    return `${baseClasses} ${statusClasses[status]} ${interactionClasses}`;
  }, [status, isPressed, isHovered]);

  return (
    <div
      className={cardClasses}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      role="button"
      tabIndex={0}
      aria-label={`${title}: ${value}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* Loading Skeleton */}
      {loading && (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
          <div className="h-8 bg-gray-300 rounded w-1/2 mb-4"></div>
          <div className="h-6 w-6 bg-gray-300 rounded"></div>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="flex items-center space-x-2 text-red-600">
          <span className="text-xl">⚠️</span>
          <span className="text-sm">{error}</span>
        </div>
      )}
      
      {/* Normal Content */}
      {!loading && !error && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
            <span className="text-2xl">{icon}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-3xl font-bold text-gray-900">{value}</span>
            <StatusIndicator status={status} />
          </div>
          
          {children}
          
          {/* Hover Indicator */}
          {isHovered && (
            <div className="absolute inset-0 rounded-xl border-2 border-blue-300 pointer-events-none" />
          )}
        </>
      )}
    </div>
  );
};

// Enhanced Status Indicator Component
const StatusIndicator: React.FC<{ status: DashboardCardProps['status'] }> = ({ status }) => {
  const indicators = {
    healthy: { icon: '✅', color: 'text-green-500' },
    degraded: { icon: '⚠️', color: 'text-yellow-500' },
    critical: { icon: '❌', color: 'text-red-500' },
    loading: { icon: '⏳', color: 'text-gray-400' }
  };
  
  const indicator = indicators[status];
  
  return (
    <span className={`text-lg ${indicator.color}`} aria-label={`Status: ${status}`}>
      {indicator.icon}
    </span>
  );
};
```

**Enhanced Navigation Implementation**:
```typescript
// services/health-dashboard/src/components/tabs/OverviewTab.tsx

// Enhanced Integrations Card
<DashboardCard
  title="Integrations"
  value={haIntegration?.totalIntegrations || 0}
  icon="🔧"
  status={getIntegrationStatus(haIntegration)}
  loading={devicesLoading}
  error={integrationError}
  onClick={() => {
    // Smooth navigation with loading state
    setNavigationLoading(true);
    const integrationsTab = document.querySelector('[data-tab="integrations"]') as HTMLElement;
    if (integrationsTab) {
      integrationsTab.click();
      // Track analytics
      analytics.track('dashboard_card_clicked', { card: 'integrations' });
    }
  }}
>
  {/* Additional context */}
  <div className="mt-2 text-xs text-gray-500">
    {haIntegration?.totalIntegrations === 0 
      ? 'No integrations discovered' 
      : `${haIntegration?.healthPercent || 0}% healthy`}
  </div>
</DashboardCard>

// Enhanced Health Card  
<DashboardCard
  title="System Health"
  value={`${haIntegration?.healthPercent || 0}%`}
  icon={getHealthIcon(haIntegration?.healthPercent || 0)}
  status={getHealthStatus(haIntegration?.healthPercent || 0)}
  loading={healthLoading}
  error={healthError}
  onClick={() => {
    setNavigationLoading(true);
    const healthTab = document.querySelector('[data-tab="health"]') as HTMLElement;
    if (healthTab) {
      healthTab.click();
      analytics.track('dashboard_card_clicked', { card: 'health' });
    }
  }}
>
  {/* Health breakdown preview */}
  <div className="mt-2 space-y-1">
    <div className="flex justify-between text-xs">
      <span>Services</span>
      <span className={getServiceHealthColor(serviceHealth)}>
        {serviceHealth}%
      </span>
    </div>
    <div className="flex justify-between text-xs">
      <span>Dependencies</span>
      <span className={getDependencyHealthColor(dependencyHealth)}>
        {dependencyHealth}%
      </span>
    </div>
  </div>
</DashboardCard>
```

**Accessibility & Performance Enhancements**:
- [ ] Full keyboard navigation support
- [ ] Screen reader announcements for status changes
- [ ] Haptic feedback for mobile devices
- [ ] Smooth animations with reduced motion support
- [ ] Analytics tracking for user interactions
- [ ] Error boundaries with recovery actions

## Phase 3: Advanced Features & UX Improvements (Context7 KB Enhanced)

### 3.1 Advanced Integration Management Features
**Goal**: Full integration lifecycle management with Context7 KB best practices

**Enhanced Features**:
- **Integration Marketplace**: Browse and install integrations from a curated marketplace
- **Configuration Templates**: Pre-built configuration templates for common setups
- **Integration Testing**: Automated testing suite for integration validation
- **Performance Monitoring**: Real-time performance metrics for each integration
- **Integration Analytics**: Usage patterns and optimization suggestions
- **Bulk Configuration**: Mass configuration updates across multiple integrations

**Implementation with Advanced Patterns**:
```typescript
// services/health-dashboard/src/components/integrations/IntegrationMarketplace.tsx
interface IntegrationTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: string;
  requirements: string[];
  configuration: Record<string, any>;
  preview: IntegrationPreview;
}

export const IntegrationMarketplace: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'popularity' | 'newest' | 'rating'>('popularity');

  const { data: templates, isLoading } = useQuery({
    queryKey: ['integration-templates', searchQuery, selectedCategory, sortBy],
    queryFn: () => fetchIntegrationTemplates({ searchQuery, category: selectedCategory, sortBy }),
  });

  const installTemplateMutation = useMutation({
    mutationFn: installIntegrationTemplate,
    onSuccess: (data) => {
      toast.success(`Integration "${data.name}" installed successfully`);
      queryClient.invalidateQueries(['integrations']);
    },
    onError: (error) => {
      toast.error(`Failed to install integration: ${error.message}`);
    }
  });

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <IntegrationSearchFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
        sortBy={sortBy}
        onSortChange={setSortBy}
      />
      
      {/* Integration Grid */}
      <IntegrationTemplateGrid
        templates={templates}
        loading={isLoading}
        onInstall={installTemplateMutation.mutate}
      />
    </div>
  );
};
```

### 3.2 Advanced Health Monitoring & Analytics
**Goal**: Proactive health monitoring with AI-powered insights

**Enhanced Features**:
- **Predictive Health Analytics**: ML-based health trend prediction
- **Anomaly Detection**: Automatic detection of unusual patterns
- **Health Scoring Algorithm**: Multi-factor health calculation with machine learning
- **Automated Remediation**: Self-healing capabilities for common issues
- **Health Forecasting**: Predictive health modeling with confidence intervals
- **Custom Health Metrics**: User-defined health indicators and thresholds

**Implementation with ML Integration**:
```typescript
// services/health-dashboard/src/hooks/usePredictiveHealth.ts
interface HealthPrediction {
  timestamp: string;
  predictedHealth: number;
  confidence: number;
  factors: {
    serviceHealth: number;
    dependencyHealth: number;
    performanceHealth: number;
    integrationHealth: number;
  };
  recommendations: HealthRecommendation[];
}

export const usePredictiveHealth = (timeHorizon: '1h' | '24h' | '7d' = '24h') => {
  const { data: historicalData } = useQuery({
    queryKey: ['health-history', timeHorizon],
    queryFn: () => fetchHealthHistory(timeHorizon),
  });

  const { data: predictions, isLoading } = useQuery({
    queryKey: ['health-predictions', timeHorizon],
    queryFn: () => predictHealthTrends(historicalData, timeHorizon),
    enabled: !!historicalData,
  });

  const { data: anomalies } = useQuery({
    queryKey: ['health-anomalies'],
    queryFn: detectHealthAnomalies,
    refetchInterval: 60000, // Check every minute
  });

  return {
    predictions,
    anomalies,
    isLoading,
    refetch: () => {
      queryClient.invalidateQueries(['health-predictions']);
      queryClient.invalidateQueries(['health-anomalies']);
    }
  };
};
```

### 3.3 Enhanced Visual Feedback & Animations
**Goal**: Modern, accessible UI with smooth animations and micro-interactions

**Enhanced Features**:
- **Micro-interactions**: Subtle animations for user feedback
- **Loading States**: Contextual loading indicators with progress
- **Error Recovery**: Interactive error states with recovery actions
- **Dark Mode**: Comprehensive dark mode with system preference detection
- **Responsive Design**: Mobile-first design with touch-friendly interactions
- **Accessibility**: WCAG 2.1 AA compliance with screen reader support

**Implementation with Framer Motion**:
```typescript
// services/health-dashboard/src/components/animations/HealthCardAnimation.tsx
import { motion, AnimatePresence } from 'framer-motion';

interface AnimatedHealthCardProps {
  health: number;
  status: 'healthy' | 'degraded' | 'critical';
  children: React.ReactNode;
}

export const AnimatedHealthCard: React.FC<AnimatedHealthCardProps> = ({
  health,
  status,
  children
}) => {
  const statusVariants = {
    healthy: { backgroundColor: '#10B981', scale: 1 },
    degraded: { backgroundColor: '#F59E0B', scale: 1.02 },
    critical: { backgroundColor: '#EF4444', scale: 1.05 }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <motion.div
        className="relative overflow-hidden rounded-xl"
        animate={statusVariants[status]}
        transition={{ duration: 0.5, ease: 'easeInOut' }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={health}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
        
        {/* Health pulse animation */}
        <motion.div
          className="absolute inset-0 rounded-xl"
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 0, 0.5]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
          style={{
            backgroundColor: statusVariants[status].backgroundColor
          }}
        />
      </motion.div>
    </motion.div>
  );
};
```

## Phase 4: Testing & Validation (Context7 KB Enhanced)

### 4.1 Comprehensive Testing Strategy
**Goal**: Ensure reliability and performance with Context7 KB testing best practices

**Enhanced Testing Approach**:
- **Unit Testing**: Jest + React Testing Library with 90%+ coverage
- **Integration Testing**: API integration tests with mock services
- **E2E Testing**: Playwright tests for critical user journeys
- **Performance Testing**: Lighthouse CI for performance monitoring
- **Accessibility Testing**: axe-core integration for WCAG compliance
- **Visual Regression Testing**: Chromatic for UI consistency

**Implementation with Modern Testing Patterns**:
```typescript
// services/health-dashboard/src/components/__tests__/DashboardCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardCard } from '../DashboardCard';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

describe('DashboardCard', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  it('should render health card with correct status', async () => {
    renderWithQueryClient(
      <DashboardCard
        title="System Health"
        value="85%"
        icon="❤️"
        status="degraded"
        onClick={jest.fn()}
      />
    );

    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
    expect(screen.getByLabelText('Status: degraded')).toBeInTheDocument();
  });

  it('should handle click events correctly', async () => {
    const mockOnClick = jest.fn();
    
    renderWithQueryClient(
      <DashboardCard
        title="Integrations"
        value="12"
        icon="🔧"
        status="healthy"
        onClick={mockOnClick}
      />
    );

    const card = screen.getByRole('button');
    fireEvent.click(card);

    await waitFor(() => {
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });
  });

  it('should be accessible via keyboard', async () => {
    const mockOnClick = jest.fn();
    
    renderWithQueryClient(
      <DashboardCard
        title="Health"
        value="90%"
        icon="✅"
        status="healthy"
        onClick={mockOnClick}
      />
    );

    const card = screen.getByRole('button');
    card.focus();
    fireEvent.keyDown(card, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });
  });

  it('should show loading state correctly', () => {
    renderWithQueryClient(
      <DashboardCard
        title="Loading"
        value="0"
        icon="⏳"
        status="loading"
        loading={true}
      />
    );

    expect(screen.getByRole('button')).toHaveClass('animate-pulse');
  });

  it('should handle error state gracefully', () => {
    renderWithQueryClient(
      <DashboardCard
        title="Error"
        value="0"
        icon="❌"
        status="critical"
        error="Connection failed"
      />
    );

    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });
});
```

### 4.2 Performance Testing & Optimization
**Goal**: Ensure optimal performance with Context7 KB performance best practices

**Performance Testing Strategy**:
- **Bundle Analysis**: Webpack Bundle Analyzer for size optimization
- **Runtime Performance**: React DevTools Profiler integration
- **Memory Leak Detection**: Automated memory leak testing
- **API Performance**: Response time monitoring and optimization
- **Caching Strategy**: Redis caching for frequently accessed data
- **CDN Integration**: Static asset optimization and delivery

**Implementation with Performance Monitoring**:
```typescript
// services/health-dashboard/src/utils/performance.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export const initPerformanceMonitoring = () => {
  // Core Web Vitals monitoring
  getCLS(console.log);
  getFID(console.log);
  getFCP(console.log);
  getLCP(console.log);
  getTTFB(console.log);

  // Custom performance metrics
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.entryType === 'measure') {
        console.log(`${entry.name}: ${entry.duration}ms`);
      }
    }
  });

  observer.observe({ entryTypes: ['measure'] });
};

// React Query performance optimization
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error.status === 404) return false;
        return failureCount < 3;
      },
    },
  },
});
```

### 4.3 Accessibility Testing & Compliance
**Goal**: Ensure WCAG 2.1 AA compliance with Context7 KB accessibility best practices

**Accessibility Testing Strategy**:
- **Automated Testing**: axe-core integration in CI/CD
- **Manual Testing**: Keyboard navigation and screen reader testing
- **Color Contrast**: Automated color contrast validation
- **Focus Management**: Proper focus handling and management
- **Screen Reader Support**: NVDA, JAWS, and VoiceOver compatibility
- **Mobile Accessibility**: Touch accessibility and gesture support

**Implementation with Accessibility Tools**:
```typescript
// services/health-dashboard/src/utils/accessibility.ts
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

export const testAccessibility = async (container: HTMLElement) => {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

// Focus management utilities
export const focusManager = {
  trapFocus: (element: HTMLElement) => {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    element.addEventListener('keydown', handleTabKey);
    firstElement.focus();

    return () => element.removeEventListener('keydown', handleTabKey);
  }
};
```

## Implementation Timeline (Context7 KB Enhanced)

### Week 1: Critical Fixes & Foundation
- [ ] Fix integration discovery and storage in WebSocket service
- [ ] Implement enhanced health calculation with weighted factors
- [ ] Add basic click behaviors with proper navigation
- [ ] Set up React Query for server state management
- [ ] Implement error boundaries and loading states

### Week 2: Enhanced Pages & Navigation
- [ ] Create advanced integrations management page with marketplace
- [ ] Create comprehensive health details page with real-time monitoring
- [ ] Implement compound component architecture
- [ ] Add WebSocket integration for live updates
- [ ] Implement advanced filtering and search capabilities

### Week 3: Advanced Features & UX
- [ ] Add integration marketplace with templates
- [ ] Implement predictive health analytics with ML
- [ ] Add micro-interactions and animations with Framer Motion
- [ ] Implement bulk operations and configuration management
- [ ] Add automated troubleshooting and remediation

### Week 4: Testing, Performance & Polish
- [ ] Comprehensive testing suite (unit, integration, E2E)
- [ ] Performance optimization and monitoring
- [ ] Accessibility compliance (WCAG 2.1 AA)
- [ ] Visual regression testing and UI consistency
- [ ] Documentation and user guides

## Success Metrics (Context7 KB Enhanced)

### Health Section
- [ ] **Accuracy**: Health percentage reflects actual system status with 95%+ accuracy
- [ ] **Real-time**: Health updates within 5 seconds of system changes
- [ ] **Predictive**: ML-based health predictions with 80%+ accuracy
- [ ] **Actionable**: Health details provide specific, actionable insights
- [ ] **Performance**: Health calculations complete in <100ms

### Integrations Section
- [ ] **Discovery**: Integration discovery works reliably with 99%+ success rate
- [ ] **Management**: Full lifecycle management (discover, configure, monitor, troubleshoot)
- [ ] **Marketplace**: Integration marketplace with 50+ pre-built templates
- [ ] **Performance**: Integration operations complete in <500ms
- [ ] **Reliability**: Integration health monitoring with automated recovery

### User Experience
- [ ] **Accessibility**: WCAG 2.1 AA compliance with 0 violations
- [ ] **Performance**: Core Web Vitals scores in "Good" range
- [ ] **Responsiveness**: Smooth 60fps animations and interactions
- [ ] **Usability**: User task completion rate >90%
- [ ] **Satisfaction**: User satisfaction score >4.5/5

### Technical Excellence
- [ ] **Test Coverage**: 90%+ code coverage with comprehensive test suite
- [ ] **Performance**: Bundle size <500KB gzipped, load time <2s
- [ ] **Reliability**: 99.9% uptime with graceful error handling
- [ ] **Maintainability**: Clean code with comprehensive documentation
- [ ] **Scalability**: Handles 1000+ integrations and 10k+ health metrics

## Risk Mitigation (Context7 KB Enhanced)

### Data Loss Prevention
- [ ] **Backup Strategy**: Automated backups of integration configurations
- [ ] **Version Control**: Git-based configuration versioning
- [ ] **Rollback Capability**: One-click rollback for failed deployments
- [ ] **Data Validation**: Comprehensive data validation and sanitization
- [ ] **Audit Trail**: Complete audit trail for all configuration changes

### Performance Impact
- [ ] **Caching Strategy**: Multi-layer caching (browser, CDN, Redis)
- [ ] **Lazy Loading**: Component and route-based lazy loading
- [ ] **Virtual Scrolling**: Virtual scrolling for large data sets
- [ ] **Bundle Optimization**: Code splitting and tree shaking
- [ ] **API Optimization**: GraphQL for efficient data fetching

### User Disruption
- [ ] **Feature Flags**: Gradual rollout with feature flags
- [ ] **Backward Compatibility**: Maintain API compatibility
- [ ] **Migration Path**: Clear migration path for existing configurations
- [ ] **User Training**: Comprehensive documentation and tutorials
- [ ] **Support Channels**: Multiple support channels for user assistance

### Security Considerations
- [ ] **Authentication**: Secure authentication and authorization
- [ ] **Data Encryption**: End-to-end encryption for sensitive data
- [ ] **Input Validation**: Comprehensive input validation and sanitization
- [ ] **Rate Limiting**: API rate limiting and abuse prevention
- [ ] **Security Headers**: Proper security headers and CORS configuration

## Conclusion

This enhanced plan integrates Context7 KB best practices with modern React/TypeScript patterns to create a comprehensive solution for the dashboard's integrations and health sections. The approach focuses on:

1. **Immediate Impact**: Fix critical issues with integration discovery and health calculation
2. **Enhanced Functionality**: Advanced features like marketplace, predictive analytics, and automated troubleshooting
3. **Modern UX**: Smooth animations, accessibility compliance, and responsive design
4. **Technical Excellence**: Comprehensive testing, performance optimization, and maintainable code

The phased implementation ensures critical issues are resolved first while building toward a world-class dashboard experience that sets new standards for integration management and health monitoring.
