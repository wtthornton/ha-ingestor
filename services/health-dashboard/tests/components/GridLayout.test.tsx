import React from 'react';
import { render, screen } from '@testing-library/react';
import { GridLayout } from '../../src/components/GridLayout';
import { LayoutConfig } from '../../src/types';
import { LAYOUT_CONFIGS } from '../../src/config/layouts';

// Mock the child components
vi.mock('../../src/components/HealthCard', () => ({
  HealthCard: ({ health, loading }: any) => (
    <div data-testid="health-card" data-loading={loading}>
      {loading ? 'Loading Health...' : `Health: ${health?.overall_status || 'No data'}`}
    </div>
  ),
}));

vi.mock('../../src/components/MetricsChart', () => ({
  MetricsChart: ({ title, loading, data }: any) => (
    <div data-testid="metrics-chart" data-loading={loading} data-title={title}>
      {loading ? 'Loading Chart...' : `Chart: ${title} - ${data?.labels?.length || 0} points`}
    </div>
  ),
}));

vi.mock('../../src/components/EventFeed', () => ({
  EventFeed: ({ events, loading }: any) => (
    <div data-testid="event-feed" data-loading={loading}>
      {loading ? 'Loading Events...' : `Events: ${events?.length || 0} items`}
    </div>
  ),
}));

vi.mock('../../src/components/SkeletonLoader', () => ({
  HealthCardSkeleton: () => <div data-testid="health-card-skeleton">Health Skeleton</div>,
  ChartSkeleton: () => <div data-testid="chart-skeleton">Chart Skeleton</div>,
  EventFeedSkeleton: () => <div data-testid="event-feed-skeleton">Event Feed Skeleton</div>,
}));

const mockHealth = {
  overall_status: 'healthy',
  admin_api_status: 'healthy',
  ingestion_service: {
    status: 'healthy',
    websocket_connection: { is_connected: true },
    event_processing: { total_events: 1000 },
    weather_enrichment: { enabled: true },
    influxdb_storage: { is_connected: true },
  },
  timestamp: '2024-01-01T00:00:00Z',
};

const mockEvents = [
  { id: '1', timestamp: '2024-01-01T00:00:00Z', entity_id: 'test.entity' },
  { id: '2', timestamp: '2024-01-01T00:01:00Z', entity_id: 'test.entity2' },
];

describe('GridLayout', () => {
  test('renders overview layout correctly', () => {
    const overviewLayout = LAYOUT_CONFIGS.overview;
    
    render(
      <GridLayout
        layout={overviewLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Check that all widgets are rendered
    expect(screen.getByTestId('health-card')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toBeInTheDocument();

    // Check grid container
    const gridContainer = screen.getByTestId('health-card').closest('.dashboard-grid');
    expect(gridContainer).toHaveStyle({
      display: 'grid',
      gridTemplateColumns: 'repeat(12, 1fr)',
      gap: '16px',
    });
  });

  test('renders detailed layout correctly', () => {
    const detailedLayout = LAYOUT_CONFIGS.detailed;
    
    render(
      <GridLayout
        layout={detailedLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Detailed layout should have more widgets
    const charts = screen.getAllByTestId('metrics-chart');
    expect(charts).toHaveLength(3); // Event rate, error rate, service status

    expect(screen.getByTestId('health-card')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toBeInTheDocument();
  });

  test('renders mobile layout correctly', () => {
    const mobileLayout = LAYOUT_CONFIGS.mobile;
    
    render(
      <GridLayout
        layout={mobileLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Mobile layout should have single column
    const gridContainer = screen.getByTestId('health-card').closest('.dashboard-grid');
    expect(gridContainer).toHaveStyle({
      gridTemplateColumns: 'repeat(1, 1fr)',
    });

    expect(screen.getByTestId('health-card')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toBeInTheDocument();
  });

  test('renders compact layout correctly', () => {
    const compactLayout = LAYOUT_CONFIGS.compact;
    
    render(
      <GridLayout
        layout={compactLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Compact layout should have 6 columns
    const gridContainer = screen.getByTestId('health-card').closest('.dashboard-grid');
    expect(gridContainer).toHaveStyle({
      gridTemplateColumns: 'repeat(6, 1fr)',
    });

    expect(screen.getByTestId('health-card')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toBeInTheDocument();
  });

  test('shows skeleton loaders when loading', () => {
    const overviewLayout = LAYOUT_CONFIGS.overview;
    
    render(
      <GridLayout
        layout={overviewLayout}
        health={mockHealth}
        events={mockEvents}
        loading={true}
      />
    );

    // Should show skeleton loaders instead of actual components
    expect(screen.getByTestId('health-card-skeleton')).toBeInTheDocument();
    expect(screen.getByTestId('chart-skeleton')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed-skeleton')).toBeInTheDocument();

    // Should not show actual components
    expect(screen.queryByTestId('health-card')).not.toBeInTheDocument();
    expect(screen.queryByTestId('metrics-chart')).not.toBeInTheDocument();
    expect(screen.queryByTestId('event-feed')).not.toBeInTheDocument();
  });

  test('applies correct grid positioning to widgets', () => {
    const overviewLayout = LAYOUT_CONFIGS.overview;
    
    render(
      <GridLayout
        layout={overviewLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Check that widgets have correct grid positioning
    const healthCard = screen.getByTestId('health-card').parentElement;
    expect(healthCard).toHaveStyle({
      gridColumn: '1 / span 4',
      gridRow: '1 / span 2',
    });

    const eventRateChart = screen.getByTestId('metrics-chart').parentElement;
    expect(eventRateChart).toHaveStyle({
      gridColumn: '5 / span 8',
      gridRow: '1 / span 2',
    });

    const eventFeed = screen.getByTestId('event-feed').parentElement;
    expect(eventFeed).toHaveStyle({
      gridColumn: '1 / span 12',
      gridRow: '3 / span 6',
    });
  });

  test('handles missing data gracefully', () => {
    const overviewLayout = LAYOUT_CONFIGS.overview;
    
    render(
      <GridLayout
        layout={overviewLayout}
        health={null}
        events={[]}
        loading={false}
      />
    );

    // Should still render components with empty data
    expect(screen.getByTestId('health-card')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-chart')).toBeInTheDocument();
    expect(screen.getByTestId('event-feed')).toBeInTheDocument();
  });

  test('generates correct chart data for different chart types', () => {
    const detailedLayout = LAYOUT_CONFIGS.detailed;
    
    render(
      <GridLayout
        layout={detailedLayout}
        health={mockHealth}
        events={mockEvents}
        loading={false}
      />
    );

    // Check that different chart types get appropriate data
    const charts = screen.getAllByTestId('metrics-chart');
    
    // Event rate chart should have line data
    const eventRateChart = charts.find(chart => 
      chart.getAttribute('data-title')?.includes('Event Rate')
    );
    expect(eventRateChart).toBeInTheDocument();
    expect(eventRateChart).toHaveAttribute('data-title', 'Event Rate (24h)');

    // Error rate chart should have bar data
    const errorRateChart = charts.find(chart => 
      chart.getAttribute('data-title')?.includes('Error Rate')
    );
    expect(errorRateChart).toBeInTheDocument();
    expect(errorRateChart).toHaveAttribute('data-title', 'Error Rate (24h)');

    // Service status chart should have doughnut data
    const serviceStatusChart = charts.find(chart => 
      chart.getAttribute('data-title')?.includes('Service Status')
    );
    expect(serviceStatusChart).toBeInTheDocument();
    expect(serviceStatusChart).toHaveAttribute('data-title', 'Service Status Distribution');
  });
});
