import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { 
  HealthMetrics, 
  ProgressBar, 
  Gauge, 
  MetricCard, 
  SystemStatusOverview 
} from '../../src/components/HealthMetrics';
import { ThemeProvider } from '../../src/contexts/ThemeContext';

// Mock the status animation hook
vi.mock('../../src/hooks/useStatusUpdates', () => ({
  useStatusAnimation: () => ({
    animationClasses: '',
  }),
}));

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

const mockMetrics = [
  {
    id: '1',
    label: 'CPU Usage',
    value: 75,
    unit: '%',
    status: 'warning' as const,
    trend: 'up' as const,
    trendValue: 5,
    lastUpdated: new Date(),
    threshold: { warning: 70, error: 90 },
    description: 'Current CPU utilization',
  },
  {
    id: '2',
    label: 'Memory Usage',
    value: 45,
    unit: '%',
    status: 'healthy' as const,
    trend: 'stable' as const,
    lastUpdated: new Date(),
    description: 'Current memory utilization',
  },
  {
    id: '3',
    label: 'Disk Usage',
    value: 95,
    unit: '%',
    status: 'error' as const,
    trend: 'up' as const,
    trendValue: 2,
    lastUpdated: new Date(),
    description: 'Current disk utilization',
  },
];

describe('HealthMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render metrics with default layout', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    expect(screen.getByText('Disk Usage')).toBeInTheDocument();
  });

  it('should render with title', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} title="System Metrics" />
    );

    expect(screen.getByText('System Metrics')).toBeInTheDocument();
  });

  it('should render with list layout', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} layout="list" />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
  });

  it('should render with cards layout', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} layout="cards" />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
  });

  it('should hide trends when showTrends is false', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} showTrends={false} />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <HealthMetrics metrics={mockMetrics} className="custom-class" />
    );

    const container = screen.getByText('CPU Usage').closest('div');
    expect(container?.closest('div')).toHaveClass('custom-class');
  });
});

describe('ProgressBar', () => {
  it('should render with default props', () => {
    renderWithTheme(
      <ProgressBar value={50} />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render with label', () => {
    renderWithTheme(
      <ProgressBar value={50} label="Test Progress" />
    );

    expect(screen.getByText('Test Progress')).toBeInTheDocument();
  });

  it('should render with percentage', () => {
    renderWithTheme(
      <ProgressBar value={50} showPercentage={true} />
    );

    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('should render with different status colors', () => {
    renderWithTheme(
      <ProgressBar value={50} status="healthy" />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render with custom max value', () => {
    renderWithTheme(
      <ProgressBar value={25} max={50} />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <ProgressBar value={50} className="custom-class" />
    );

    expect(document.body).toBeInTheDocument();
  });
});

describe('Gauge', () => {
  it('should render with default props', () => {
    renderWithTheme(
      <Gauge value={50} />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render with label', () => {
    renderWithTheme(
      <Gauge value={50} label="Test Gauge" />
    );

    expect(screen.getByText('Test Gauge')).toBeInTheDocument();
  });

  it('should render with different sizes', () => {
    renderWithTheme(
      <Gauge value={50} size="sm" />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render with different status colors', () => {
    renderWithTheme(
      <Gauge value={50} status="warning" />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <Gauge value={50} className="custom-class" />
    );

    expect(document.body).toBeInTheDocument();
  });
});

describe('MetricCard', () => {
  it('should render with all props', () => {
    renderWithTheme(
      <MetricCard
        title="Test Metric"
        value={75}
        unit="%"
        status="warning"
        trend="up"
        trendValue={5}
        lastUpdated={new Date()}
        description="Test description"
      />
    );

    expect(screen.getByText('Test Metric')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('WARNING')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('should handle click events', () => {
    const onClick = vi.fn();
    
    renderWithTheme(
      <MetricCard
        title="Test Metric"
        value={75}
        status="healthy"
        lastUpdated={new Date()}
        onClick={onClick}
      />
    );

    const card = screen.getByText('Test Metric').closest('div');
    fireEvent.click(card!);

    expect(onClick).toHaveBeenCalled();
  });

  it('should render without trend', () => {
    renderWithTheme(
      <MetricCard
        title="Test Metric"
        value={75}
        status="healthy"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Metric')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
  });

  it('should render without description', () => {
    renderWithTheme(
      <MetricCard
        title="Test Metric"
        value={75}
        status="healthy"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Metric')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <MetricCard
        title="Test Metric"
        value={75}
        status="healthy"
        lastUpdated={new Date()}
        className="custom-class"
      />
    );

    const card = screen.getByText('Test Metric').closest('div');
    expect(card).toHaveClass('custom-class');
  });
});

describe('SystemStatusOverview', () => {
  const mockServices = [
    {
      name: 'WebSocket Service',
      status: 'healthy' as const,
      lastChecked: new Date(),
    },
    {
      name: 'Database Service',
      status: 'warning' as const,
      lastChecked: new Date(),
    },
    {
      name: 'API Service',
      status: 'error' as const,
      lastChecked: new Date(),
    },
  ];

  it('should render with healthy overall status', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="healthy"
        services={mockServices}
      />
    );

    expect(screen.getByText('System Status')).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(screen.getByText('WebSocket Service')).toBeInTheDocument();
  });

  it('should render with warning overall status', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="warning"
        services={mockServices}
      />
    );

    expect(screen.getByText('WARNING')).toBeInTheDocument();
  });

  it('should render with error overall status', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="error"
        services={mockServices}
      />
    );

    expect(screen.getByText('ERROR')).toBeInTheDocument();
  });

  it('should render with unknown overall status', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="unknown"
        services={mockServices}
      />
    );

    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
  });

  it('should render all services', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="healthy"
        services={mockServices}
      />
    );

    expect(screen.getByText('WebSocket Service')).toBeInTheDocument();
    expect(screen.getByText('Database Service')).toBeInTheDocument();
    expect(screen.getByText('API Service')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <SystemStatusOverview
        overallStatus="healthy"
        services={mockServices}
        className="custom-class"
      />
    );

    const container = screen.getByText('System Status').closest('div');
    expect(container).toHaveClass('custom-class');
  });
});
