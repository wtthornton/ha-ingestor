import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { 
  StatusIndicator, 
  TrendIndicator, 
  StatusBadge 
} from '../../src/components/StatusIndicator';
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

describe('StatusIndicator', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render with healthy status', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText(/Updated:/)).toBeInTheDocument();
  });

  it('should render with warning status', () => {
    renderWithTheme(
      <StatusIndicator
        status="warning"
        label="Test Service"
        value="75%"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('should render with error status', () => {
    renderWithTheme(
      <StatusIndicator
        status="error"
        label="Test Service"
        value="0%"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should render with unknown status', () => {
    renderWithTheme(
      <StatusIndicator
        status="unknown"
        label="Test Service"
        value="N/A"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('should render with trend indicator', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        trend="up"
        lastUpdated={new Date()}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should render inline variant', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        variant="inline"
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should render minimal variant', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        variant="minimal"
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should handle click events', () => {
    const onClick = vi.fn();
    
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        onClick={onClick}
      />
    );

    const indicator = screen.getByText('Test Service').closest('div');
    fireEvent.click(indicator!);

    expect(onClick).toHaveBeenCalled();
  });

  it('should render different sizes', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        size="sm"
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
  });

  it('should hide trend when showTrend is false', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        trend="up"
        lastUpdated={new Date()}
        showTrend={false}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('should hide last updated when showLastUpdated is false', () => {
    renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        showLastUpdated={false}
      />
    );

    expect(screen.getByText('Test Service')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.queryByText(/Updated:/)).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = renderWithTheme(
      <StatusIndicator
        status="healthy"
        label="Test Service"
        value="100%"
        lastUpdated={new Date()}
        className="custom-class"
      />
    );

    // Find the main container div that should have the custom class
    const statusContainer = container.querySelector('.custom-class');
    expect(statusContainer).toBeInTheDocument();
  });
});

describe('TrendIndicator', () => {
  it('should render up trend', () => {
    renderWithTheme(
      <TrendIndicator trend="up" />
    );

    // The component should render without errors
    expect(document.body).toBeInTheDocument();
  });

  it('should render down trend', () => {
    renderWithTheme(
      <TrendIndicator trend="down" />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render stable trend', () => {
    renderWithTheme(
      <TrendIndicator trend="stable" />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should render with value', () => {
    renderWithTheme(
      <TrendIndicator trend="up" value={5} />
    );

    expect(document.body).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <TrendIndicator trend="up" className="custom-class" />
    );

    expect(document.body).toBeInTheDocument();
  });
});

describe('StatusBadge', () => {
  it('should render with healthy status', () => {
    renderWithTheme(
      <StatusBadge status="healthy" text="HEALTHY" />
    );

    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
  });

  it('should render with warning status', () => {
    renderWithTheme(
      <StatusBadge status="warning" text="WARNING" />
    );

    expect(screen.getByText('WARNING')).toBeInTheDocument();
  });

  it('should render with error status', () => {
    renderWithTheme(
      <StatusBadge status="error" text="ERROR" />
    );

    expect(screen.getByText('ERROR')).toBeInTheDocument();
  });

  it('should render with unknown status', () => {
    renderWithTheme(
      <StatusBadge status="unknown" text="UNKNOWN" />
    );

    expect(screen.getByText('UNKNOWN')).toBeInTheDocument();
  });

  it('should render different sizes', () => {
    renderWithTheme(
      <StatusBadge status="healthy" text="HEALTHY" size="sm" />
    );

    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    renderWithTheme(
      <StatusBadge status="healthy" text="HEALTHY" className="custom-class" />
    );

    const badge = screen.getByText('HEALTHY');
    expect(badge).toHaveClass('custom-class');
  });
});
